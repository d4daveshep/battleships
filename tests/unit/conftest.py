import pytest
from typing import Dict, List
from services.lobby_service import LobbyService
from services.auth_service import AuthService
from game.lobby import Lobby
from game.player import PlayerStatus


@pytest.fixture
def empty_lobby() -> Lobby:
    # Fresh empty lobby instance for each test
    return Lobby()


@pytest.fixture
def populated_lobby(empty_lobby: Lobby) -> Lobby:
    # Lobby pre-populated with Alice and Bob as available players
    empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
    empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
    empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
    return empty_lobby


@pytest.fixture
def empty_lobby_service(empty_lobby: Lobby) -> LobbyService:
    # LobbyService instance with fresh empty lobby
    return LobbyService(empty_lobby)


@pytest.fixture
def populated_lobby_service(populated_lobby: Lobby) -> LobbyService:
    # LobbyService instance with pre-populated lobby (Alice and Bob)
    return LobbyService(populated_lobby)


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

