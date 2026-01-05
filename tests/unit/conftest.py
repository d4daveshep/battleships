import pytest
from typing import Dict, List
from services.lobby_service import LobbyService
from services.auth_service import AuthService
from game.lobby import Lobby
from game.player import Player, PlayerStatus


def make_player(name: str, status: PlayerStatus = PlayerStatus.AVAILABLE) -> Player:
    """Helper function to create Player objects for testing"""
    return Player(name, status)


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
        "charlie": populated_lobby["charlie"]
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
    # AuthService instance for player name validation
    return AuthService()
