"""Testing endpoints for development and automated testing.

These endpoints bypass normal authentication and are only meant for testing purposes.
They should only be included when TESTING environment variable is set.
"""

import asyncio

from fastapi import APIRouter, Form, HTTPException

from game.game_service import GameService
from game.lobby import Lobby
from game.player import Player, PlayerStatus
from services.lobby_service import LobbyService

router = APIRouter(prefix="/test", tags=["testing"])

# Module-level references (set during setup)
_lobby: Lobby | None = None
_game_service: GameService | None = None
_lobby_service: LobbyService | None = None


def set_up_testing_router(
    lobby: Lobby,
    game_service: GameService,
    lobby_service: LobbyService,
) -> APIRouter:
    """Configure the testing router with required dependencies.

    Args:
        lobby: The global Lobby instance
        game_service: The GameService instance
        lobby_service: The LobbyService instance

    Returns:
        Configured APIRouter
    """
    global _lobby, _game_service, _lobby_service
    _lobby = lobby
    _game_service = game_service
    _lobby_service = lobby_service
    return router


def _get_lobby() -> Lobby:
    if _lobby is None:
        raise RuntimeError("Testing router not initialized")
    return _lobby


def _get_game_service() -> GameService:
    if _game_service is None:
        raise RuntimeError("Testing router not initialized")
    return _game_service


def _get_lobby_service() -> LobbyService:
    if _lobby_service is None:
        raise RuntimeError("Testing router not initialized")
    return _lobby_service


@router.post("/reset-lobby")
async def reset_lobby_for_testing() -> dict[str, str]:
    """Reset lobby and game state - for testing only."""
    lobby = _get_lobby()
    game_service = _get_game_service()

    # Reset lobby state
    lobby.players.clear()
    lobby.game_requests.clear()
    lobby.active_games.clear()
    lobby.version = 0
    lobby.change_event = asyncio.Event()

    # Reset game service state
    game_service.games.clear()
    game_service.games_by_player.clear()
    game_service.ship_placement_boards.clear()
    game_service.ready_players.clear()
    game_service._placement_version = 0
    game_service._placement_change_event = asyncio.Event()

    return {"status": "lobby and games cleared"}


@router.post("/add-player-to-lobby")
async def add_player_to_lobby_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Add a player to the lobby bypassing authentication - for testing only."""
    lobby_service = _get_lobby_service()

    try:
        test_player = Player(player_name, PlayerStatus.AVAILABLE)
        lobby_service.join_lobby(test_player)
        return {"status": "player added", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/remove-player-from-lobby")
async def remove_player_from_lobby_for_testing(
    player_name: str = Form(),
) -> dict[str, str]:
    """Remove a player from the lobby bypassing authentication - for testing only."""
    lobby_service = _get_lobby_service()

    try:
        player_id = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        lobby_service.leave_lobby(player_id)
        return {"status": "player removed", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-game-request")
async def send_game_request_for_testing(
    sender_name: str = Form(), target_name: str = Form()
) -> dict[str, str]:
    """Send a game request bypassing session validation - for testing only."""
    lobby_service = _get_lobby_service()

    try:
        sender_id = lobby_service.get_player_id_by_name(sender_name)
        target_id = lobby_service.get_player_id_by_name(target_name)
        if not sender_id:
            raise ValueError(f"Sender '{sender_name}' not found in lobby")
        if not target_id:
            raise ValueError(f"Target '{target_name}' not found in lobby")
        lobby_service.send_game_request(sender_id, target_id)
        return {
            "status": "game request sent",
            "sender": sender_name,
            "target": target_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/accept-game-request")
async def accept_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Accept a game request bypassing session validation - for testing only."""
    lobby_service = _get_lobby_service()
    game_service = _get_game_service()

    try:
        player_id = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")

        sender_id, receiver_id = lobby_service.accept_game_request(player_id)

        # Create the game (idempotent - handles concurrent accepts)
        game_service.create_game_from_accepted_request(sender_id, receiver_id)

        sender_name_result = lobby_service.get_player_name(sender_id)
        receiver_name_result = lobby_service.get_player_name(receiver_id)
        return {
            "status": "game request accepted",
            "player": receiver_name_result or receiver_id,
            "sender": sender_name_result or sender_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decline-game-request")
async def decline_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Decline a game request bypassing session validation - for testing only."""
    lobby_service = _get_lobby_service()

    try:
        player_id = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        sender_id = lobby_service.decline_game_request(player_id)
        sender_name_result = lobby_service.get_player_name(sender_id)
        return {
            "status": "game request declined",
            "player": player_name,
            "sender": sender_name_result or sender_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
