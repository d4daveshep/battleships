"""Battleships game FastAPI application.

This is the main entry point for the application. Routes are organized
into separate router modules in the `routes` package.
"""

import asyncio
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response

from game.lobby import Lobby
from services.auth_service import AuthService
from services.lobby_service import LobbyService
from game.game_service import GameService

# Import routers
from routes.helpers import set_up_helpers
from routes.auth import set_up_auth_router, router as auth_router
from routes.lobby import set_up_lobby_router, router as lobby_router
from routes.ship_placement import (
    set_up_ship_placement_router,
    router as ship_placement_router,
)
from routes.gameplay import set_up_gameplay_router, router as gameplay_router
from routes.start_game import set_up_start_game_router, router as start_game_router

app: FastAPI = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates: Jinja2Templates = Jinja2Templates(directory="templates")


# Global lobby instance for state management
_game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(_game_lobby)
game_service: GameService = GameService()


# Set up helpers module first (shared by all routers)
set_up_helpers(templates, game_service, lobby_service)

# Set up all routers with their dependencies
set_up_auth_router(templates, auth_service, game_service, lobby_service)
set_up_lobby_router(templates, game_service, lobby_service)
set_up_ship_placement_router(templates, game_service, lobby_service)
set_up_gameplay_router(templates, game_service)
set_up_start_game_router(templates, game_service, lobby_service)

# Include all routers
app.include_router(auth_router)
app.include_router(lobby_router)
app.include_router(ship_placement_router)
app.include_router(gameplay_router)
app.include_router(start_game_router)


# === Testing Endpoints ===
# These endpoints are kept in main.py as they are specific to the main app


@app.post("/test/reset-lobby")
async def reset_lobby_for_testing() -> dict[str, str]:
    """Reset lobby state - for testing only"""
    _game_lobby.players.clear()
    _game_lobby.game_requests.clear()
    _game_lobby.version = 0
    _game_lobby.change_event = asyncio.Event()

    return {"status": "lobby cleared"}


@app.post("/test/add-player-to-lobby")
async def add_player_to_lobby_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Add a player to the lobby bypassing authentication - for testing only"""
    try:
        # Create a player object for testing
        from game.player import Player, PlayerStatus

        test_player: Player = Player(player_name, PlayerStatus.AVAILABLE)
        lobby_service.join_lobby(test_player)
        return {"status": "player added", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/remove-player-from-lobby")
async def remove_player_from_lobby_for_testing(
    player_name: str = Form(),
) -> dict[str, str]:
    """Remove a player from the lobby bypassing authentication - for testing only"""
    try:
        # Look up player ID by name
        player_id: str | None = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        lobby_service.leave_lobby(player_id)
        return {"status": "player removed", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/send-game-request")
async def send_game_request_for_testing(
    sender_name: str = Form(), target_name: str = Form()
) -> dict[str, str]:
    """Send a game request bypassing session validation - for testing only"""
    try:
        # Look up player IDs by names
        sender_id: str | None = lobby_service.get_player_id_by_name(sender_name)
        target_id: str | None = lobby_service.get_player_id_by_name(target_name)
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


@app.post("/test/accept-game-request")
async def accept_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Accept a game request bypassing session validation - for testing only"""
    try:
        # Look up player ID by name
        player_id: str | None = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        sender_id, receiver_id = lobby_service.accept_game_request(player_id)
        sender_name: str | None = lobby_service.get_player_name(sender_id)
        receiver_name: str | None = lobby_service.get_player_name(receiver_id)
        return {
            "status": "game request accepted",
            "player": receiver_name or receiver_id,
            "sender": sender_name or sender_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/decline-game-request")
async def decline_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Decline a game request bypassing session validation - for testing only"""
    try:
        # Look up player ID by name
        player_id: str | None = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        sender_id: str = lobby_service.decline_game_request(player_id)
        sender_name: str | None = lobby_service.get_player_name(sender_id)
        return {
            "status": "game request declined",
            "player": player_name,
            "sender": sender_name or sender_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for test infrastructure"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
