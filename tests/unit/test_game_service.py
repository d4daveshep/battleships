import pytest
from game.player import Player, PlayerStatus

from game.game_service import (
    Game,
    GameStatus,
    GameMode,
    GameService,
    PlayerAlreadyInGameException,
    UnknownPlayerException,
    PlayerNotInGameException,
    DuplicatePlayerException,
    UnknownGameException,
)
from game.exceptions import NoShotsAimedError, ActionAfterFireError
from game.model import GameBoard
from game.model import ShipType, Coord, CoordHelper, Ship, Orientation


class TestGameService:
    # Uses game_service and test_players fixtures from conftest.py

    def test_new_add_player(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)
        assert alice.id in game_service.players

    def test_create_game_service(self, game_service):
        assert game_service, "Can't create GameService"
        assert len(game_service.games) == 0

    def test_create_single_player_game(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)

        game_id: str = game_service.create_single_player_game(player_id=alice.id)

        # game_id should be a 22 character URL-safe random string
        assert len(game_id) == 22

        assert len(game_service.games) == 1
        assert game_id in game_service.games
        game: Game = game_service.games[game_id]
        assert game.id == game_id
        assert game.game_mode == GameMode.SINGLE_PLAYER
        assert game.player_1 == alice
        assert len(game_service.games_by_player) == 1
        assert alice.id in game_service.games_by_player
        assert game_service.games_by_player[alice.id] == game

    def test_create_single_player_game_fails_with_unknown_player(
        self, game_service: GameService
    ):
        john_doe: Player = Player("John Doe", status=PlayerStatus.AVAILABLE)
        with pytest.raises(UnknownPlayerException):
            game_service.create_single_player_game(john_doe.id)

    def test_create_single_player_game_fails_with_player_already_in_game(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)
        game_service.create_single_player_game(alice.id)

        with pytest.raises(PlayerAlreadyInGameException):
            game_service.create_single_player_game(alice.id)

    def test_get_game_board_from_known_player_id(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)
        game_service.create_single_player_game(player_id=alice.id)

        board: GameBoard = game_service.get_game_board(player_id=alice.id)
        assert board, "Didn't get GameBoard from GameService"

    def test_create_two_player_game(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        bob: Player = test_players["Bob"]

        game_service.add_player(alice)
        game_service.add_player(bob)

        game_id: str = game_service.create_two_player_game(
            player_1_id=alice.id, player_2_id=bob.id
        )

        assert len(game_id) == 22

        assert len(game_service.games) == 1
        assert game_id in game_service.games
        game: Game = game_service.games[game_id]
        assert game.id == game_id
        assert game.game_mode == GameMode.TWO_PLAYER
        assert game.player_1 == alice
        assert game.player_2 == bob
        assert len(game_service.games_by_player) == 2
        assert alice.id in game_service.games_by_player
        assert bob.id in game_service.games_by_player
        assert game_service.games_by_player[alice.id] == game
        assert game_service.games_by_player[bob.id] == game

    def test_create_two_player_game_fails_with_unknown_player(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)
        unknown_bob: Player = test_players["Bob"]
        # test fail on unknown player 1 or player 2
        with pytest.raises(
            UnknownPlayerException, match=r".*" + unknown_bob.id + r".*"
        ):
            game_service.create_two_player_game(unknown_bob.id, alice.id)
        with pytest.raises(
            UnknownPlayerException, match=r".*" + unknown_bob.id + r".*"
        ):
            game_service.create_two_player_game(alice.id, unknown_bob.id)

    def test_create_two_player_game_fails_with_player_already_in_game(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        bob: Player = test_players["Bob"]

        game_service.add_player(alice)
        game_service.add_player(bob)
        game_service.create_single_player_game(alice.id)

        # test fail on player 1 or player 2 already in game
        with pytest.raises(
            PlayerAlreadyInGameException, match=r".*" + alice.id + r".*"
        ):
            game_service.create_two_player_game(alice.id, bob.id)
        with pytest.raises(
            PlayerAlreadyInGameException, match=r".*" + alice.id + r".*"
        ):
            game_service.create_two_player_game(bob.id, alice.id)

    def test_create_two_player_game_fails_with_both_players_same(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)

        # test fail if same player used for both sides
        with pytest.raises(
            DuplicatePlayerException,
            match=r"Two player game must have two different players",
        ):
            game_service.create_two_player_game(alice.id, alice.id)

    def test_get_game_id_by_player_id(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        bob: Player = test_players["Bob"]
        charlie: Player = test_players["Charlie"]

        game_service.add_player(alice)
        game_service.add_player(bob)
        game_service.add_player(charlie)

        game_id: str = game_service.create_single_player_game(alice.id)
        with pytest.raises(NotImplementedError):
            assert game_id == game_service.get_game_id_by_player_id(alice.id)

        game_id = game_service.create_two_player_game(bob.id, charlie.id)
        with pytest.raises(NotImplementedError):
            assert game_service.get_game_id_by_player_id(bob.id) == game_id
            assert game_service.get_game_id_by_player_id(charlie.id) == game_id

    def test_abandon_game_by_player_id(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        bob: Player = test_players["Bob"]
        charlie: Player = test_players["Charlie"]
        diana: Player = test_players["Diana"]
        eddie: Player = test_players["Eddie"]

        game_service.add_player(alice)
        game_id: str = game_service.create_single_player_game(alice.id)

        # game_service.abandon_game_by_player_id(alice.id)
        # assert game_service.get_game_status_by_game_id(game_id) == GameStatus.ABANDONED
        #

    #     assert False, "Figure out what status to put the player into after a game"
    #
    #     game_service.add_player(bob)
    #     game_service.add_player(charlie)
    #     game_service.create_two_player_game(bob.id, charlie.id)
    #     game_service.abandon_game_by_player_id(bob.id)  # player 1 abandons
    #     assert game_service.get_game_status_by_game_id(game_id) == GameStatus.ABANDONED
    #
    #     game_service.add_player(diana)
    #     game_service.add_player(eddie)
    #     game_service.create_two_player_game(diana.id, eddie.id)
    #     game_service.abandon_game_by_player_id(eddie.id)  # player 2 abandons
    #     assert game_service.get_game_status_by_game_id(game_id) == GameStatus.ABANDONED

    def test_get_game_status_by_player_id(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        bob: Player = test_players["Bob"]
        charlie: Player = test_players["Charlie"]

        game_service.add_player(alice)
        game_service.add_player(bob)
        game_service.add_player(charlie)

        # Test getting game status for single player game
        game_service.create_single_player_game(alice.id)
        status: GameStatus = game_service.get_game_status_by_player_id(alice.id)
        assert status == GameStatus.CREATED

        # Test getting game status for two player game
        game_service.create_two_player_game(bob.id, charlie.id)
        status = game_service.get_game_status_by_player_id(bob.id)
        assert status == GameStatus.CREATED
        status = game_service.get_game_status_by_player_id(charlie.id)
        assert status == GameStatus.CREATED

    def test_get_game_status_by_player_id_fails_with_unknown_player(
        self, game_service: GameService
    ):
        unknown_player: Player = Player(name="Unknown", status=PlayerStatus.AVAILABLE)
        with pytest.raises(UnknownPlayerException):
            game_service.get_game_status_by_player_id(unknown_player.id)

    def test_get_game_status_by_player_id_fails_with_player_not_in_game(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        game_service.add_player(alice)

        # Alice is added to the service but not in a game
        with pytest.raises(PlayerNotInGameException):
            game_service.get_game_status_by_player_id(alice.id)

    def test_get_game_status_by_game_id(
        self, game_service: GameService, test_players: dict[str, Player]
    ):
        alice: Player = test_players["Alice"]
        bob: Player = test_players["Bob"]
        charlie: Player = test_players["Charlie"]

        game_service.add_player(alice)
        game_service.add_player(bob)
        game_service.add_player(charlie)

        # Test getting game status for single player game
        game_id_1: str = game_service.create_single_player_game(alice.id)
        status: GameStatus = game_service.get_game_status_by_game_id(game_id_1)
        assert status == GameStatus.CREATED

        # Test getting game status for two player game
        game_id_2: str = game_service.create_two_player_game(bob.id, charlie.id)
        status = game_service.get_game_status_by_game_id(game_id_2)
        assert status == GameStatus.CREATED

    def test_get_game_status_by_game_id_fails_with_unknown_id(
        self, game_service: GameService
    ):
        unknown_game_id: str = "unknown_game_id_12345"
        with pytest.raises(UnknownGameException):
            game_service.get_game_status_by_game_id(unknown_game_id)


class TestMultiplayerShipPlacement:
    """Tests for multiplayer ship placement functionality"""

    # Uses game_service fixture from conftest.py

    @pytest.fixture
    def two_players_in_game(
        self, game_service: GameService
    ) -> tuple[Player, Player, str]:
        """Setup two players in a multiplayer game"""
        alice = Player(name="Alice", status=PlayerStatus.AVAILABLE)
        bob = Player(name="Bob", status=PlayerStatus.AVAILABLE)
        game_service.add_player(alice)
        game_service.add_player(bob)
        game_id = game_service.create_two_player_game(alice.id, bob.id)
        return alice, bob, game_id

    def test_get_opponent_ready_status_returns_false_initially(
        self, game_service: GameService, two_players_in_game: tuple[Player, Player, str]
    ) -> None:
        """When a multiplayer game starts, opponent should not be ready"""
        alice, bob, game_id = two_players_in_game

        # Alice checks if Bob is ready - should be False initially
        is_opponent_ready = game_service.is_opponent_ready(alice.id)
        assert is_opponent_ready is False

        # Bob checks if Alice is ready - should be False initially
        is_opponent_ready = game_service.is_opponent_ready(bob.id)
        assert is_opponent_ready is False

    def test_get_opponent_ready_status_returns_true_when_opponent_is_ready(
        self, game_service: GameService, two_players_in_game: tuple[Player, Player, str]
    ) -> None:
        """When opponent marks themselves as ready, player should see them as ready"""
        alice, bob, game_id = two_players_in_game

        # Bob marks himself as ready
        game_service.set_player_ready(bob.id)

        # Alice checks if Bob is ready - should be True now
        is_opponent_ready = game_service.is_opponent_ready(alice.id)
        assert is_opponent_ready is True

        # Bob checks if Alice is ready - should still be False
        is_opponent_ready = game_service.is_opponent_ready(bob.id)
        assert is_opponent_ready is False

    def test_both_players_ready_check(
        self, game_service: GameService, two_players_in_game: tuple[Player, Player, str]
    ) -> None:
        """Check if both players in a game are ready"""
        alice, bob, game_id = two_players_in_game

        # Initially neither is ready
        assert game_service.are_both_players_ready(game_id) is False

        # Alice becomes ready
        game_service.set_player_ready(alice.id)
        assert game_service.are_both_players_ready(game_id) is False

        # Bob becomes ready
        game_service.set_player_ready(bob.id)
        assert game_service.are_both_players_ready(game_id) is True

    def test_placement_version_increments_when_game_created(
        self, game_service: GameService
    ) -> None:
        """When a two-player game is created, placement version should increment to notify waiting players"""
        alice = Player(name="Alice", status=PlayerStatus.AVAILABLE)
        bob = Player(name="Bob", status=PlayerStatus.AVAILABLE)
        game_service.add_player(alice)
        game_service.add_player(bob)

        # Get initial version
        initial_version = game_service.get_placement_version()

        # Create a two-player game (simulating both players ready scenario)
        game_id = game_service.create_two_player_game(alice.id, bob.id)

        # Version should have incremented to notify waiting players
        # This is critical for Player 1 who is waiting via long-polling
        current_version = game_service.get_placement_version()
        assert current_version > initial_version, (
            "Placement version should increment when game is created "
            "to wake up waiting long-poll requests"
        )


class TestPlaceShipsRandomly:
    """Comprehensive unit tests for GameService.place_ships_randomly()"""

    # Uses game_service fixture from conftest.py

    @pytest.fixture
    def player_in_game(self, game_service: GameService) -> Player:
        """Setup a player in a single-player game"""
        player = Player(name="TestPlayer", status=PlayerStatus.AVAILABLE)
        game_service.add_player(player)
        game_service.create_single_player_game(player.id)
        return player

    def test_successfully_places_all_5_ships(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that all 5 ships are placed on the board"""
        player_id = player_in_game.id

        # Place ships randomly
        game_service.place_ships_randomly(player_id)

        # Get the board
        board = game_service.get_or_create_ship_placement_board(player_id)

        # Verify all 5 ships are placed
        assert len(board.ships) == 5, "Should have exactly 5 ships placed"

        # Verify each ship type is present
        ship_types_on_board = {ship.ship_type for ship in board.ships}
        expected_ship_types = {
            ShipType.CARRIER,
            ShipType.BATTLESHIP,
            ShipType.CRUISER,
            ShipType.SUBMARINE,
            ShipType.DESTROYER,
        }
        assert ship_types_on_board == expected_ship_types, (
            "All 5 ship types should be present"
        )

    def test_ships_dont_overlap(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that placed ships don't overlap"""
        player_id = player_in_game.id

        # Place ships randomly
        game_service.place_ships_randomly(player_id)

        # Get the board
        board = game_service.get_or_create_ship_placement_board(player_id)

        # Collect all ship positions
        all_positions: list[Coord] = []
        for ship in board.ships:
            all_positions.extend(ship.positions)

        # Check for duplicates (overlaps)
        assert len(all_positions) == len(set(all_positions)), (
            "Ships should not overlap - each position should be unique"
        )

    def test_ships_respect_spacing_rules(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that ships maintain required spacing (no touching)"""
        player_id = player_in_game.id

        # Place ships randomly
        game_service.place_ships_randomly(player_id)

        # Get the board
        board = game_service.get_or_create_ship_placement_board(player_id)

        # For each ship, verify it doesn't touch other ships
        for i, ship in enumerate(board.ships):
            # Get adjacent coords for this ship
            adjacent_coords = CoordHelper.coords_adjacent_to_a_coords_list(
                ship.positions
            )

            # Check that no other ship occupies adjacent coords
            for j, other_ship in enumerate(board.ships):
                if i != j:  # Don't compare ship with itself
                    other_ship_positions = set(other_ship.positions)
                    touching_coords = adjacent_coords.intersection(other_ship_positions)
                    assert len(touching_coords) == 0, (
                        f"{ship.ship_type.name} should not touch {other_ship.ship_type.name}"
                    )

    def test_clears_existing_ships_before_placing(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that existing ships are cleared before placing new random ships"""
        player_id = player_in_game.id

        # Get the board and manually place a ship
        board = game_service.get_or_create_ship_placement_board(player_id)
        from game.model import Ship, Coord, Orientation

        manual_ship = Ship(ShipType.DESTROYER)
        board.place_ship(manual_ship, Coord.A1, Orientation.HORIZONTAL)

        # Verify manual ship is placed
        assert len(board.ships) == 1
        assert board.ships[0].ship_type == ShipType.DESTROYER

        # Now place ships randomly
        game_service.place_ships_randomly(player_id)

        # Get the board again
        board = game_service.get_or_create_ship_placement_board(player_id)

        # Verify old ship is gone and we have 5 new ships
        assert len(board.ships) == 5, "Should have 5 ships after random placement"

        # The manually placed destroyer should be replaced with a new random one
        # We can't verify exact positions, but we can verify all 5 types are present
        ship_types_on_board = {ship.ship_type for ship in board.ships}
        assert ShipType.DESTROYER in ship_types_on_board

    def test_raises_exception_for_invalid_player(
        self, game_service: GameService
    ) -> None:
        """Test that UnknownPlayerException is raised for non-existent player"""
        invalid_player_id = "non_existent_player_id_12345"

        with pytest.raises(UnknownPlayerException):
            game_service.place_ships_randomly(invalid_player_id)

    def test_ships_are_within_board_bounds(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that all ship positions are valid coordinates (A1-J10)"""
        player_id = player_in_game.id

        # Place ships randomly
        game_service.place_ships_randomly(player_id)

        # Get the board
        board = game_service.get_or_create_ship_placement_board(player_id)

        # Verify all positions are valid Coord enum values
        from game.model import Coord

        all_valid_coords = set(Coord)

        for ship in board.ships:
            for position in ship.positions:
                assert position in all_valid_coords, (
                    f"Position {position} should be a valid coordinate"
                )

                # Additional check: verify row is A-J and column is 1-10
                coord_details = position.value
                assert 1 <= coord_details.row_index <= 10, (
                    f"Row index {coord_details.row_index} should be between 1 and 10"
                )
                assert 1 <= coord_details.col_index <= 10, (
                    f"Column index {coord_details.col_index} should be between 1 and 10"
                )

    def test_randomness_produces_different_results(
        self, game_service: GameService
    ) -> None:
        """Test that multiple calls produce different ship placements"""
        # Create two separate players to avoid clearing issue
        player1 = Player(name="Player1", status=PlayerStatus.AVAILABLE)
        player2 = Player(name="Player2", status=PlayerStatus.AVAILABLE)

        game_service.add_player(player1)
        game_service.add_player(player2)

        game_service.create_single_player_game(player1.id)
        game_service.create_single_player_game(player2.id)

        # Place ships randomly for both players
        game_service.place_ships_randomly(player1.id)
        game_service.place_ships_randomly(player2.id)

        # Get both boards
        board1 = game_service.get_or_create_ship_placement_board(player1.id)
        board2 = game_service.get_or_create_ship_placement_board(player2.id)

        # Collect all positions from both boards
        positions1 = set()
        for ship in board1.ships:
            for pos in ship.positions:
                positions1.add((ship.ship_type, pos))

        positions2 = set()
        for ship in board2.ships:
            for pos in ship.positions:
                positions2.add((ship.ship_type, pos))

        # The positions should be different (extremely unlikely to be identical)
        # We check that at least one ship has a different position
        assert positions1 != positions2, (
            "Random placement should produce different results on different calls"
        )

    def test_each_ship_has_correct_length(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that each placed ship has the correct number of positions"""
        player_id = player_in_game.id

        # Place ships randomly
        game_service.place_ships_randomly(player_id)

        # Get the board
        board = game_service.get_or_create_ship_placement_board(player_id)

        # Verify each ship has correct length
        for ship in board.ships:
            expected_length = ship.ship_type.length
            actual_length = len(ship.positions)
            assert actual_length == expected_length, (
                f"{ship.ship_type.name} should have {expected_length} positions, "
                f"but has {actual_length}"
            )

    def test_works_for_player_without_existing_board(
        self, game_service: GameService, player_in_game: Player
    ) -> None:
        """Test that method works even if player has no existing ship placement board"""
        player_id = player_in_game.id

        # Verify no board exists yet (or clear it)
        if player_id in game_service.ship_placement_boards:
            del game_service.ship_placement_boards[player_id]

        # Place ships randomly - should create board automatically
        game_service.place_ships_randomly(player_id)

        # Verify board was created and has ships
        board = game_service.get_or_create_ship_placement_board(player_id)
        assert len(board.ships) == 5


class TestIsMultiplayer:
    """Tests for GameService.is_multiplayer() method"""

    # Uses game_service fixture from conftest.py

    def test_is_multiplayer_returns_false_for_player_not_in_game(
        self, game_service: GameService
    ) -> None:
        """Player not in any game should return False"""
        player = Player(name="SoloPlayer", status=PlayerStatus.AVAILABLE)
        game_service.add_player(player)

        # Player exists but is not in a game
        result = game_service.is_multiplayer(player.id)
        assert result is False

    def test_is_multiplayer_returns_false_for_single_player_game(
        self, game_service: GameService
    ) -> None:
        """Player in single-player game should return False"""
        player = Player(name="SoloPlayer", status=PlayerStatus.AVAILABLE)
        game_service.add_player(player)
        game_service.create_single_player_game(player.id)

        # Should be False - single player mode
        result = game_service.is_multiplayer(player.id)
        assert result is False

    def test_is_multiplayer_returns_true_for_two_player_game(
        self, game_service: GameService
    ) -> None:
        """Player in two-player game should return True"""
        alice = Player(name="Alice", status=PlayerStatus.AVAILABLE)
        bob = Player(name="Bob", status=PlayerStatus.AVAILABLE)
        game_service.add_player(alice)
        game_service.add_player(bob)
        game_service.create_two_player_game(alice.id, bob.id)

        # Should be True for both players
        assert game_service.is_multiplayer(alice.id) is True
        assert game_service.is_multiplayer(bob.id) is True

    def test_is_multiplayer_only_checks_game_mode(
        self, game_service: GameService
    ) -> None:
        """is_multiplayer should only check game.game_mode, not lobby pairings"""
        alice = Player(name="Alice", status=PlayerStatus.AVAILABLE)
        bob = Player(name="Bob", status=PlayerStatus.AVAILABLE)
        game_service.add_player(alice)
        game_service.add_player(bob)

        # Create a two-player game
        game_service.create_two_player_game(alice.id, bob.id)

        # Verify the game mode is what we expect
        game = game_service.games_by_player[alice.id]
        assert game.game_mode == GameMode.TWO_PLAYER

        # is_multiplayer should return True based on game mode
        assert game_service.is_multiplayer(alice.id) is True

    def test_is_multiplayer_does_not_require_lobby_service(
        self, game_service: GameService
    ) -> None:
        """is_multiplayer should work without passing lobby_service parameter"""
        alice = Player(name="Alice", status=PlayerStatus.AVAILABLE)
        bob = Player(name="Bob", status=PlayerStatus.AVAILABLE)
        game_service.add_player(alice)
        game_service.add_player(bob)
        game_service.create_two_player_game(alice.id, bob.id)

        # This should work WITHOUT passing lobby_service
        # The old implementation required lobby_service to check lobby.active_games
        # The new implementation should only check game.game_mode
        result = game_service.is_multiplayer(alice.id)
        assert result is True

        result = game_service.is_multiplayer(bob.id)
        assert result is True


def _create_player_with_all_ships(
    game_service: GameService,
) -> tuple[Player, str]:
    """Helper to create player with all ships placed - returns (player, game_id)"""
    from game.model import Ship, Orientation

    player = Player(name="TestPlayer", status=PlayerStatus.AVAILABLE)
    game_service.add_player(player)
    game_id = game_service.create_single_player_game(player.id)

    board = game_service.get_game_board(player.id)
    board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

    return player, game_id


class TestToggleAim:
    """Tests for GameService.toggle_aim() method"""

    # Uses game_service fixture from conftest.py

    @pytest.fixture
    def player_with_ships(self, game_service: GameService) -> tuple[Player, str]:
        """Create a player in a game with all ships placed"""
        return _create_player_with_all_ships(game_service)

    def test_toggle_aim_adds_coordinate(
        self, game_service: GameService, player_with_ships: tuple[Player, str]
    ) -> None:
        """Test that toggle_aim adds a coordinate when not already aimed"""
        alice, game_id = player_with_ships

        result = game_service.toggle_aim(game_id, alice.id, "J1")

        assert result.is_aimed is True
        assert result.aimed_count == 1
        assert result.shots_available == 6

    def test_toggle_aim_removes_coordinate(
        self, game_service: GameService, player_with_ships: tuple[Player, str]
    ) -> None:
        """Test that toggle_aim removes a coordinate when already aimed"""
        alice, game_id = player_with_ships

        # First toggle - add
        game_service.toggle_aim(game_id, alice.id, "J1")

        # Second toggle - remove
        result = game_service.toggle_aim(game_id, alice.id, "J1")

        assert result.is_aimed is False
        assert result.aimed_count == 0
        assert result.shots_available == 6

    def test_toggle_aim_multiple_coordinates(
        self, game_service: GameService, player_with_ships: tuple[Player, str]
    ) -> None:
        """Test toggling multiple different coordinates"""
        alice, game_id = player_with_ships

        result1 = game_service.toggle_aim(game_id, alice.id, "J1")
        result2 = game_service.toggle_aim(game_id, alice.id, "J2")
        result3 = game_service.toggle_aim(game_id, alice.id, "J3")

        assert result1.aimed_count == 1
        assert result2.aimed_count == 2
        assert result3.aimed_count == 3

    def test_toggle_aim_returns_aim_result(
        self, game_service: GameService, player_with_ships: tuple[Player, str]
    ) -> None:
        """Test that toggle_aim returns an AimResult named tuple"""
        alice, game_id = player_with_ships

        result = game_service.toggle_aim(game_id, alice.id, "J1")

        # Verify it's a NamedTuple with expected fields
        assert hasattr(result, "is_aimed")
        assert hasattr(result, "aimed_count")
        assert hasattr(result, "shots_available")


def _aim_at_coordinates(game: Game, player_id: str, coordinates: list[str]) -> None:
    """Helper to aim at multiple coordinates"""
    for coord_str in coordinates:
        coord = Coord[coord_str]
        game.aim_at(player_id, coord)


class TestSelectShot:
    """Tests for GameService.select_shot() method - shot selection limit enforcement"""

    # Uses game_service fixture from conftest.py

    @pytest.fixture
    def player_with_ships_and_max_aimed(
        self, game_service: GameService
    ) -> tuple[Player, str]:
        """Create a player in a game with all ships placed and max shots aimed"""
        player, game_id = _create_player_with_all_ships(game_service)
        game = game_service.games[game_id]
        _aim_at_coordinates(game, player.id, ["A1", "B1", "C1", "D1", "E1", "F1"])
        return player, game_id

    def test_cannot_select_more_shots_than_available(
        self,
        game_service: GameService,
        player_with_ships_and_max_aimed: tuple[Player, str],
    ) -> None:
        """Test that select_shot fails when player already aimed max shots"""
        alice, game_id = player_with_ships_and_max_aimed

        result = game_service.select_shot(game_id, alice.id, "G7")

        assert result.success is False
        assert result.error == "All available shots aimed"
        assert "G7" not in game_service.games[game_id].get_aimed_shots(alice.id)

    @pytest.fixture
    def player_with_ships_for_counter(
        self, game_service: GameService
    ) -> tuple[Player, str]:
        """Create a player in a game with all ships placed"""
        return _create_player_with_all_ships(game_service)

    def test_shot_counter_display_format(
        self,
        game_service: GameService,
        player_with_ships_for_counter: tuple[Player, str],
    ) -> None:
        """Test that shot counter displays correct format"""
        alice, game_id = player_with_ships_for_counter
        game = game_service.games[game_id]
        _aim_at_coordinates(game, alice.id, ["A1", "B1", "C1"])
        counter = game.get_shot_counter_display(alice.id)
        assert counter == "Shots Aimed: 3/6"

    def test_coordinate_selection_state_management(
        self,
        game_service: GameService,
        player_with_ships_for_counter: tuple[Player, str],
    ) -> None:
        """Test that coordinate selection state is managed correctly"""
        alice, game_id = player_with_ships_for_counter
        game = game_service.games[game_id]

        assert game.is_coordinate_selectable(alice.id, Coord.A1) is True
        assert game.is_coordinate_selectable(alice.id, Coord.C3) is True

        game.aim_at(alice.id, Coord.A1)

        assert game.is_coordinate_selectable(alice.id, Coord.A1) is False
        assert game.is_coordinate_selectable(alice.id, Coord.C3) is True


class TestFireShotsService:
    """Tests for GameService.fire_shots() method."""

    @pytest.fixture
    def two_player_setup(self, game_service: GameService) -> tuple[Player, Player, str]:
        """Create a two-player game with all ships placed."""
        alice = Player(name="Alice", status=PlayerStatus.AVAILABLE)
        bob = Player(name="Bob", status=PlayerStatus.AVAILABLE)
        game_service.add_player(alice)
        game_service.add_player(bob)
        game_id = game_service.create_two_player_game(alice.id, bob.id)
        game = game_service.games[game_id]

        # Place all ships for both players
        for player in [alice, bob]:
            board = game.board[player]
            board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
            board.place_ship(
                Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL
            )
            board.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
            board.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
            board.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        return alice, bob, game_id

    def test_fire_shots_submits_aimed_shots(
        self, game_service: GameService, two_player_setup: tuple[Player, Player, str]
    ) -> None:
        """Test that fire_shots submits the currently aimed shots."""
        alice, _, game_id = two_player_setup

        # Aim at some coordinates
        game_service.toggle_aim(game_id, alice.id, "A1")
        game_service.toggle_aim(game_id, alice.id, "B2")
        game_service.toggle_aim(game_id, alice.id, "C3")
        game_service.toggle_aim(game_id, alice.id, "D4")

        # Fire the shots
        game_service.fire_shots(game_id, alice.id)

        # Verify shots were fired
        game = game_service.games[game_id]
        fired_shots = game.get_fired_shots(alice.id)
        assert len(fired_shots) == 4
        assert Coord.A1 in fired_shots
        assert Coord.B2 in fired_shots
        assert Coord.C3 in fired_shots
        assert Coord.D4 in fired_shots

    def test_fire_shots_with_fewer_than_available(
        self, game_service: GameService, two_player_setup: tuple[Player, Player, str]
    ) -> None:
        """Test that firing fewer shots than available is allowed."""
        alice, _, game_id = two_player_setup

        # Aim at only 4 coordinates (out of 6 available)
        game_service.toggle_aim(game_id, alice.id, "A1")
        game_service.toggle_aim(game_id, alice.id, "B2")
        game_service.toggle_aim(game_id, alice.id, "C3")
        game_service.toggle_aim(game_id, alice.id, "D4")

        # Fire the shots - should succeed
        game_service.fire_shots(game_id, alice.id)

        game = game_service.games[game_id]
        fired_shots = game.get_fired_shots(alice.id)
        assert len(fired_shots) == 4

    def test_fire_shots_sets_waiting_status(
        self, game_service: GameService, two_player_setup: tuple[Player, Player, str]
    ) -> None:
        """Test that firing shots sets the player to waiting for opponent status."""
        alice, _, game_id = two_player_setup

        # Aim at one shot first
        game_service.toggle_aim(game_id, alice.id, "A1")

        # Fire shots
        game_service.fire_shots(game_id, alice.id)

        game = game_service.games[game_id]
        assert game.is_waiting_for_opponent(alice.id) is True

    def test_fire_shots_clears_aimed_shots(
        self, game_service: GameService, two_player_setup: tuple[Player, Player, str]
    ) -> None:
        """Test that firing shots clears the aimed shots."""
        alice, _, game_id = two_player_setup

        game_service.toggle_aim(game_id, alice.id, "A1")
        game_service.toggle_aim(game_id, alice.id, "B2")

        game_service.fire_shots(game_id, alice.id)

        game = game_service.games[game_id]
        assert game.get_aimed_shots_count(alice.id) == 0

    def test_fire_shots_with_no_aimed_shots_raises_error(
        self, game_service: GameService, two_player_setup: tuple[Player, Player, str]
    ) -> None:
        """Test that firing with no aimed shots raises an error."""
        alice, _, game_id = two_player_setup

        with pytest.raises(NoShotsAimedError):
            game_service.fire_shots(game_id, alice.id)

    def test_cannot_aim_after_firing(
        self, game_service: GameService, two_player_setup: tuple[Player, Player, str]
    ) -> None:
        """Test that aiming is blocked after firing shots."""
        alice, _, game_id = two_player_setup

        game_service.toggle_aim(game_id, alice.id, "A1")
        game_service.fire_shots(game_id, alice.id)

        # Attempting to aim should raise an error
        with pytest.raises(ActionAfterFireError):
            game_service.toggle_aim(game_id, alice.id, "B2")
