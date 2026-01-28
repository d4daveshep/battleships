import pytest

from game.game_service import Game, GameMode, GameStatus
from game.player import Player, PlayerStatus
from game.model import Ship, ShipType, Orientation, Coord
from game.exceptions import ShotLimitExceededError, ActionAfterFireError


class TestGameModeEnum:
    """Unit tests for GameMode enumeration"""

    def test_game_mode_values(self):
        expected_modes = {
            GameMode.SINGLE_PLAYER,
            GameMode.TWO_PLAYER,
        }
        actual_modes: set[GameMode] = {mode for mode in GameMode}
        assert expected_modes == actual_modes


class TestGameStatusEnum:
    """Unit tests for GameStatus enumeration"""

    def test_game_status_values(self):
        expected_statuses = {
            GameStatus.CREATED,
            GameStatus.SETUP,
            GameStatus.PLAYING,
            GameStatus.FINISHED,
            GameStatus.ABANDONED,
        }
        actual_statuses: set[GameStatus] = {status for status in GameStatus}
        assert expected_statuses == actual_statuses


class TestGameModel:
    """Unit tests for Game"""

    # Uses alice and bob fixtures from conftest.py

    def test_single_player_game_creation(self, alice: Player) -> None:
        # Test creating a valid single player game
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)

        game_id: str = game.id
        assert isinstance(game_id, str)
        assert len(game_id) == 22
        assert game.player_1 == alice
        assert game.game_mode == GameMode.SINGLE_PLAYER
        assert game.player_2 is None

    def test_two_player_game_creation(self, alice, bob):
        # Test creating a valid two player game
        game = Game(player_1=alice, player_2=bob, game_mode=GameMode.TWO_PLAYER)

        assert game.player_1 == alice
        assert game.player_2 == bob
        assert game.game_mode == GameMode.TWO_PLAYER

    def test_create_two_player_game_fails_with_one_player(self, alice):
        # Test that two player game requires two players
        with pytest.raises(ValueError, match="Two player games must have two players"):
            Game(player_1=alice, game_mode=GameMode.TWO_PLAYER)

    def test_create_single_player_game_fails_with_two_players(self, alice, bob):
        # Test that single player game cannot two players
        with pytest.raises(
            ValueError, match="Single player games cannot have two players"
        ):
            Game(player_1=alice, player_2=bob, game_mode=GameMode.SINGLE_PLAYER)

    def test_game_initializes_round_one(self, alice):
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)
        assert game.round == 1

    def test_game_get_shots_available_all_ships(self, alice):
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)
        board = game.board[alice]

        # Place all ships with spacing (skipping rows)
        # Carrier (5) - 2 shots
        board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        # Battleship (4) - 1 shot
        board.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        # Cruiser (3) - 1 shot
        board.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        # Submarine (3) - 1 shot
        board.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        # Destroyer (2) - 1 shot
        board.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        assert game.get_shots_available(alice.id) == 6


class TestGameAimedShots:
    """Unit tests for aimed shots functionality"""

    # Uses alice and bob fixtures from conftest.py

    @pytest.fixture
    def game_with_ships(self, alice: Player) -> Game:
        """Create a game with all ships placed (6 shots available)"""
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)
        board = game.board[alice]
        # Place all ships with spacing (skipping rows)
        board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)
        return game

    def test_game_initializes_with_empty_aimed_shots(self, alice):
        """Test that a new game has no aimed shots for any player"""
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)
        assert game.aimed_shots == {}

    def test_aim_at_coordinate(self, alice, game_with_ships):
        """Test that aiming at a coordinate adds it to aimed_shots"""
        game_with_ships.aim_at(alice.id, Coord.J10)
        assert Coord.J10 in game_with_ships.get_aimed_shots(alice.id)

    def test_aim_at_multiple_coordinates(self, alice, game_with_ships):
        """Test that multiple coordinates can be aimed at"""
        game_with_ships.aim_at(alice.id, Coord.J1)
        game_with_ships.aim_at(alice.id, Coord.J3)
        game_with_ships.aim_at(alice.id, Coord.J5)
        aimed: set[Coord] = game_with_ships.get_aimed_shots(alice.id)
        assert Coord.J1 in aimed
        assert Coord.J3 in aimed
        assert Coord.J5 in aimed
        assert len(aimed) == 3

    def test_unaim_at_coordinate(self, alice, game_with_ships):
        """Test that unaiming removes a coordinate from aimed_shots"""
        game_with_ships.aim_at(alice.id, Coord.J1)
        game_with_ships.aim_at(alice.id, Coord.J3)
        game_with_ships.unaim_at(alice.id, Coord.J1)
        aimed: set[Coord] = game_with_ships.get_aimed_shots(alice.id)
        assert Coord.J1 not in aimed
        assert Coord.J3 in aimed
        assert len(aimed) == 1

    def test_unaim_at_coordinate_not_aimed(self, alice):
        """Test that unaiming a coordinate that wasn't aimed doesn't error"""
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)
        # Should not raise an error
        game.unaim_at(alice.id, Coord.A1)
        assert len(game.get_aimed_shots(alice.id)) == 0

    def test_get_aimed_shots_count(self, alice, game_with_ships):
        """Test getting count of aimed shots"""
        assert game_with_ships.get_aimed_shots_count(alice.id) == 0

        game_with_ships.aim_at(alice.id, Coord.J1)
        assert game_with_ships.get_aimed_shots_count(alice.id) == 1

        game_with_ships.aim_at(alice.id, Coord.J3)
        game_with_ships.aim_at(alice.id, Coord.J5)
        assert game_with_ships.get_aimed_shots_count(alice.id) == 3

    def test_cannot_aim_more_than_available_shots(self, alice, game_with_ships):
        """Test that aiming at more coordinates than available shots raises error"""
        # Aim at 6 coordinates (the max available)
        game_with_ships.aim_at(alice.id, Coord.A10)
        game_with_ships.aim_at(alice.id, Coord.B10)
        game_with_ships.aim_at(alice.id, Coord.C10)
        game_with_ships.aim_at(alice.id, Coord.D10)
        game_with_ships.aim_at(alice.id, Coord.E10)
        game_with_ships.aim_at(alice.id, Coord.F10)

        # 7th should raise an error
        with pytest.raises(ShotLimitExceededError):
            game_with_ships.aim_at(alice.id, Coord.G10)

    def test_aiming_same_coordinate_twice_does_not_count_as_two(
        self, alice, game_with_ships
    ):
        """Test that aiming at same coordinate twice only counts once"""
        game_with_ships.aim_at(alice.id, Coord.J1)
        game_with_ships.aim_at(alice.id, Coord.J1)  # Same coordinate
        assert game_with_ships.get_aimed_shots_count(alice.id) == 1


class TestFireShots:
    """Unit tests for firing shots functionality"""

    @pytest.fixture
    def two_player_game_with_ships(self, alice: Player, bob: Player) -> Game:
        """Create a two-player game with all ships placed"""
        game = Game(player_1=alice, player_2=bob, game_mode=GameMode.TWO_PLAYER)

        # Place all ships for player 1
        board_1 = game.board[alice]
        board_1.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        # Place all ships for player 2
        board_2 = game.board[bob]
        board_2.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        return game

    def test_fire_shots_submits_aimed_shots(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that firing shots submits the currently aimed shots."""
        game = two_player_game_with_ships

        # Aim at 4 coordinates
        game.aim_at(alice.id, Coord.A1)
        game.aim_at(alice.id, Coord.B2)
        game.aim_at(alice.id, Coord.C3)
        game.aim_at(alice.id, Coord.D4)

        # Fire the shots
        game.fire_shots(alice.id)

        # Shots should be recorded as fired
        fired_shots = game.get_fired_shots(alice.id)
        assert len(fired_shots) == 4
        assert Coord.A1 in fired_shots
        assert Coord.B2 in fired_shots
        assert Coord.C3 in fired_shots
        assert Coord.D4 in fired_shots

    def test_fire_shots_with_fewer_than_available(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that firing fewer shots than available is allowed."""
        game = two_player_game_with_ships

        # Aim at only 4 coordinates (out of 6 available)
        game.aim_at(alice.id, Coord.A1)
        game.aim_at(alice.id, Coord.B2)
        game.aim_at(alice.id, Coord.C3)
        game.aim_at(alice.id, Coord.D4)

        # Fire the shots - should succeed
        game.fire_shots(alice.id)

        fired_shots = game.get_fired_shots(alice.id)
        assert len(fired_shots) == 4

    def test_fire_shots_clears_aimed_shots(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that firing shots clears the aimed shots."""
        game = two_player_game_with_ships

        # Aim at some coordinates
        game.aim_at(alice.id, Coord.A1)
        game.aim_at(alice.id, Coord.B2)

        assert game.get_aimed_shots_count(alice.id) == 2

        # Fire the shots
        game.fire_shots(alice.id)

        # Aimed shots should be cleared
        assert game.get_aimed_shots_count(alice.id) == 0

    def test_fire_shots_sets_waiting_status(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that firing shots sets the player to waiting for opponent status."""
        game = two_player_game_with_ships

        # Aim at one shot before firing
        game.aim_at(alice.id, Coord.A1)

        # Fire shots
        game.fire_shots(alice.id)

        # Player should be in waiting status
        assert game.is_waiting_for_opponent(alice.id) is True

    def test_cannot_aim_after_firing(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that aiming is blocked after firing shots."""
        game = two_player_game_with_ships

        # Aim at one shot first
        game.aim_at(alice.id, Coord.A1)

        # Fire shots
        game.fire_shots(alice.id)

        # Attempting to aim should raise an error
        with pytest.raises(ActionAfterFireError):
            game.aim_at(alice.id, Coord.E5)

    def test_get_fired_shots_returns_empty_initially(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that no shots are fired at game start."""
        game = two_player_game_with_ships

        fired_shots = game.get_fired_shots(alice.id)
        assert len(fired_shots) == 0


class TestWaitingForOpponent:
    """Unit tests for waiting for opponent status"""

    @pytest.fixture
    def two_player_game_with_ships(self, alice: Player, bob: Player) -> Game:
        """Create a two-player game with all ships placed"""
        game = Game(player_1=alice, player_2=bob, game_mode=GameMode.TWO_PLAYER)

        # Place all ships for player 1
        board_1 = game.board[alice]
        board_1.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        board_1.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        # Place all ships for player 2
        board_2 = game.board[bob]
        board_2.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        board_2.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        return game

    def test_is_waiting_for_opponent_false_initially(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that player is not waiting for opponent at game start."""
        game = two_player_game_with_ships

        assert game.is_waiting_for_opponent(alice.id) is False

    def test_is_waiting_for_opponent_true_after_firing(
        self, alice: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that player is waiting for opponent after firing shots."""
        game = two_player_game_with_ships

        # Aim at one shot first
        game.aim_at(alice.id, Coord.A1)

        game.fire_shots(alice.id)

        assert game.is_waiting_for_opponent(alice.id) is True

    def test_opponent_not_waiting_after_first_player_fires(
        self, alice: Player, bob: Player, two_player_game_with_ships: Game
    ) -> None:
        """Test that opponent is not waiting when only first player has fired."""
        game = two_player_game_with_ships

        # Player 1 aims and fires
        game.aim_at(alice.id, Coord.A1)
        game.fire_shots(alice.id)

        # Player 1 is waiting
        assert game.is_waiting_for_opponent(alice.id) is True
        # Player 2 is not waiting (hasn't fired yet)
        assert game.is_waiting_for_opponent(bob.id) is False
