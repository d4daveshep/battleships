from typing import Dict, List, NamedTuple

import pytest

from game.game_service import GameService
from game.lobby import Lobby
from game.player import Player, PlayerStatus
from services.auth_service import AuthService
from services.lobby_service import LobbyService


def make_player(name: str, status: PlayerStatus = PlayerStatus.AVAILABLE) -> Player:
    """Helper function to create Player objects for testing."""
    return Player(name, status)


# =============================================================================
# Game Setup Helpers
# =============================================================================


class TwoPlayerGameSetup(NamedTuple):
    """Container for two-player game setup data."""

    player_1: Player
    player_2: Player
    game_id: str
    game_service: GameService


def create_two_player_game_setup(
    game_service: GameService,
    player1_name: str = "Alice",
    player2_name: str = "Bob",
) -> TwoPlayerGameSetup:
    """Create two players and a two-player game.

    Args:
        game_service: GameService instance
        player1_name: Name for player 1 (default "Alice")
        player2_name: Name for player 2 (default "Bob")

    Returns:
        TwoPlayerGameSetup with players and game_id
    """
    player1 = Player(name=player1_name, status=PlayerStatus.AVAILABLE)
    player2 = Player(name=player2_name, status=PlayerStatus.AVAILABLE)
    game_service.add_player(player1)
    game_service.add_player(player2)
    game_id = game_service.create_two_player_game(player1.id, player2.id)
    return TwoPlayerGameSetup(player1, player2, game_id, game_service)


# =============================================================================
# Lobby Setup Helpers
# =============================================================================


class GameRequestSetup(NamedTuple):
    """Container for game request setup data."""

    sender: Player
    receiver: Player
    lobby: Lobby


def setup_game_request(
    lobby: Lobby,
    sender_name: str = "Alice",
    receiver_name: str = "Bob",
) -> GameRequestSetup:
    """Setup two players with a pending game request.

    Args:
        lobby: Lobby instance
        sender_name: Name for sender (default "Alice")
        receiver_name: Name for receiver (default "Bob")

    Returns:
        GameRequestSetup with sender, receiver, and lobby
    """
    sender = make_player(sender_name, PlayerStatus.AVAILABLE)
    receiver = make_player(receiver_name, PlayerStatus.AVAILABLE)
    lobby.add_player(sender)
    lobby.add_player(receiver)
    lobby.send_game_request(sender.id, receiver.id)
    return GameRequestSetup(sender, receiver, lobby)


def add_players_to_lobby(
    lobby: Lobby,
    *names: str,
    status: PlayerStatus = PlayerStatus.AVAILABLE,
) -> list[Player]:
    """Add multiple players to a lobby and return them.

    Args:
        lobby: Lobby instance
        *names: Player names to add
        status: Status for all players (default AVAILABLE)

    Returns:
        List of created Player objects
    """
    players = []
    for name in names:
        player = make_player(name, status)
        lobby.add_player(player)
        players.append(player)
    return players


# =============================================================================
# GameService fixtures
# =============================================================================


@pytest.fixture
def game_service() -> GameService:
    """Fresh GameService instance for each test.

    Returns:
        New GameService instance with no players or games
    """
    return GameService()


# =============================================================================
# Common player fixtures
# =============================================================================


@pytest.fixture
def alice() -> Player:
    """Alice player fixture with AVAILABLE status.

    Returns:
        Player named Alice with AVAILABLE status
    """
    return Player("Alice", PlayerStatus.AVAILABLE)


@pytest.fixture
def bob() -> Player:
    """Bob player fixture with AVAILABLE status.

    Returns:
        Player named Bob with AVAILABLE status
    """
    return Player("Bob", PlayerStatus.AVAILABLE)


@pytest.fixture
def charlie() -> Player:
    """Charlie player fixture with AVAILABLE status.

    Returns:
        Player named Charlie with AVAILABLE status
    """
    return Player("Charlie", PlayerStatus.AVAILABLE)


@pytest.fixture
def diana() -> Player:
    """Diana player fixture with AVAILABLE status.

    Returns:
        Player named Diana with AVAILABLE status
    """
    return Player("Diana", PlayerStatus.AVAILABLE)


@pytest.fixture
def eddie() -> Player:
    """Eddie player fixture with AVAILABLE status.

    Returns:
        Player named Eddie with AVAILABLE status
    """
    return Player("Eddie", PlayerStatus.AVAILABLE)


@pytest.fixture
def test_players() -> dict[str, Player]:
    """Dictionary of common test players.

    Returns:
        Dictionary mapping player names to Player instances
    """
    return {
        "Alice": Player(name="Alice", status=PlayerStatus.AVAILABLE),
        "Bob": Player(name="Bob", status=PlayerStatus.AVAILABLE),
        "Charlie": Player(name="Charlie", status=PlayerStatus.AVAILABLE),
        "Diana": Player(name="Diana", status=PlayerStatus.AVAILABLE),
        "Eddie": Player(name="Eddie", status=PlayerStatus.AVAILABLE),
    }


@pytest.fixture
def empty_lobby() -> Lobby:
    # Fresh empty lobby instance for each test
    return Lobby()


@pytest.fixture
def populated_lobby(empty_lobby: Lobby) -> dict:
    # Lobby pre-populated with Alice, Bob and Charlie as available players
    alice = Player("Alice", PlayerStatus.AVAILABLE)
    bob = Player("Bob", PlayerStatus.AVAILABLE)
    charlie = Player("Charlie", PlayerStatus.AVAILABLE)
    empty_lobby.add_player(alice)
    empty_lobby.add_player(bob)
    empty_lobby.add_player(charlie)
    return {"lobby": empty_lobby, "alice": alice, "bob": bob, "charlie": charlie}


@pytest.fixture
def empty_lobby_service(empty_lobby: Lobby) -> LobbyService:
    # LobbyService instance with fresh empty lobby
    return LobbyService(empty_lobby)


@pytest.fixture
def populated_lobby_service(populated_lobby: dict) -> dict:
    # LobbyService instance with pre-populated lobby (Alice, Bob, Charlie)
    service = LobbyService(populated_lobby["lobby"])
    return {
        "service": service,
        "alice": populated_lobby["alice"],
        "bob": populated_lobby["bob"],
        "charlie": populated_lobby["charlie"],
    }


@pytest.fixture
def empty_result() -> Dict[str, List[Dict[str, str]]]:
    # Standard empty lobby result format
    return {"available_players": []}


@pytest.fixture
def diana_expected_players() -> List[Dict[str, str]]:
    # Expected players for Diana scenario
    return [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]


@pytest.fixture
def auth_service() -> AuthService:
    """AuthService instance for player name validation."""
    return AuthService()


@pytest.fixture
def two_player_game(game_service: GameService) -> TwoPlayerGameSetup:
    """Fixture providing a ready-to-use two-player game.

    Args:
        game_service: GameService instance from fixture

    Returns:
        TwoPlayerGameSetup with Alice and Bob in a game
    """
    return create_two_player_game_setup(game_service)


@pytest.fixture
def lobby_with_game_request(empty_lobby: Lobby) -> GameRequestSetup:
    """Fixture with Alice having sent a game request to Bob.

    Args:
        empty_lobby: Empty Lobby instance from fixture

    Returns:
        GameRequestSetup with Alice requesting Bob
    """
    return setup_game_request(empty_lobby)
