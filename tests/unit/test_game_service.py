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
from game.model import GameBoard


class TestGameService:
    @pytest.fixture
    def game_service(self) -> GameService:
        return GameService()

    @pytest.fixture
    def test_players(self) -> dict[str, Player]:
        return {
            "Alice": Player(name="Alice", status=PlayerStatus.AVAILABLE),
            "Bob": Player(name="Bob", status=PlayerStatus.AVAILABLE),
            "Charlie": Player(name="Charlie", status=PlayerStatus.AVAILABLE),
            "Diana": Player(name="Diana", status=PlayerStatus.AVAILABLE),
            "Eddie": Player(name="Eddie", status=PlayerStatus.AVAILABLE),
        }

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

    @pytest.fixture
    def game_service(self) -> GameService:
        return GameService()

    @pytest.fixture
    def two_players_in_game(self, game_service: GameService) -> tuple[Player, Player, str]:
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
