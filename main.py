from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
from typing import AsyncIterator

from game.lobby import Lobby
from game.player import Player, PlayerStatus
from services.auth_service import AuthService, PlayerNameValidation
from services.lobby_service import LobbyService

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")

# Global lobby instance for state management
game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(game_lobby)

# SSE connections for real-time lobby updates
lobby_connections: dict[str, list[asyncio.Queue]] = {}


# All validation and lobby logic moved to service classes


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {"player_name": "", "error_message": "", "css_class": ""},
    )


@app.post("/", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse:
    validation: PlayerNameValidation = auth_service.validate_player_name(
        player_name, strip_quotes=True
    )

    if not validation.is_valid:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error_message": validation.error_message,
                "player_name": "" if validation.error_message else player_name,
                "css_class": validation.css_class,
            },
        )

    if game_mode == "human":
        lobby_service.join_lobby(player_name)  # Add the player to the lobby

        return RedirectResponse(
            url=f"/lobby?player_name={player_name.strip()}", status_code=302
        )
    else:
        return RedirectResponse(
            url=f"/game?player_name={player_name.strip()}", status_code=302
        )


@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request, player_name: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "game.html",
        {"player_name": player_name, "game_mode": "Single Player"},
    )


@app.post("/player-name")
async def validate_player_name(
    request: Request, player_name: str = Form()
) -> HTMLResponse:
    """Validate player name and return partial HTML with validation result"""
    validation: PlayerNameValidation = auth_service.validate_player_name(
        player_name, strip_quotes=False
    )

    return templates.TemplateResponse(
        request,
        "components/player_name_input.html",
        {
            "player_name": player_name,
            "error_message": validation.error_message,
            "css_class": validation.css_class,
        },
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for test infrastructure"""
    return {"status": "healthy"}


@app.post("/test/reset-lobby")
async def reset_lobby_for_testing() -> dict[str, str]:
    """Reset lobby state - for testing only"""
    game_lobby.players.clear()
    # Clear SSE connections as well
    lobby_connections.clear()
    return {"status": "lobby cleared"}


async def broadcast_lobby_update() -> None:
    """Broadcast lobby updates to all connected clients"""
    if not lobby_connections:
        return
    
    # Get current lobby state
    all_players = list(game_lobby.players.values())
    update_data = {
        "type": "lobby_update",
        "players": [{"name": p.name, "status": p.status} for p in all_players]
    }
    
    # Send to all connections
    for player_queues in lobby_connections.values():
        for queue in player_queues[:]:  # Copy list to avoid modification during iteration
            try:
                queue.put_nowait(update_data)
            except asyncio.QueueFull:
                # Remove full queues (disconnected clients)
                player_queues.remove(queue)


@app.post("/select-opponent")
async def select_opponent(
    request: Request, player_name: str = Form(), opponent_name: str = Form()
) -> HTMLResponse:
    """Handle opponent selection and return updated lobby view"""

    # Update player statuses: sender becomes "Requesting Game", target becomes "Requesting Game"
    try:
        lobby_service.update_player_status(player_name, PlayerStatus.REQUESTING_GAME)
        lobby_service.update_player_status(opponent_name, PlayerStatus.REQUESTING_GAME)
        
        # Broadcast the update to all connected clients
        await broadcast_lobby_update()
    except ValueError:
        # Handle case where player doesn't exist in lobby
        pass

    # Get updated lobby data after status changes
    lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player_name)

    return templates.TemplateResponse(
        request,
        "lobby.html",
        {
            "player_name": player_name,
            "game_mode": "Two Player",
            "available_players": lobby_data,
            "confirmation_message": f"Game request sent to {opponent_name}",
            "player_status": "Requesting Game",
        },
    )


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request, player_name: str = "") -> HTMLResponse:
    # Default template context
    template_context = {
        "player_name": player_name,
        "game_mode": "Two Player",
        "available_players": [],
        "confirmation_message": "",
        "player_status": "Available",
        "error_message": "",
    }

    # Try to get lobby data for valid player names
    try:
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player_name)
        template_context["available_players"] = lobby_data
    except ValueError as e:
        template_context["player_name"] = ""
        template_context["error_message"] = str(e)

    return templates.TemplateResponse(request, "lobby.html", template_context)


@app.get("/lobby/stream/{player_name}")
async def lobby_stream(player_name: str) -> StreamingResponse:
    """SSE endpoint for real-time lobby updates"""
    
    async def event_stream() -> AsyncIterator[str]:
        # Create a queue for this connection
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        # Add to connections
        if player_name not in lobby_connections:
            lobby_connections[player_name] = []
        lobby_connections[player_name].append(queue)
        
        try:
            # Send initial lobby state
            all_players = list(game_lobby.players.values())
            initial_data = {
                "type": "lobby_update",
                "players": [{"name": p.name, "status": p.status} for p in all_players]
            }
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            # Keep connection alive and send updates
            while True:
                try:
                    # Wait for updates with timeout
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(update)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield "data: {\"type\": \"keepalive\"}\n\n"
                
        except asyncio.CancelledError:
            pass
        finally:
            # Clean up connection
            if player_name in lobby_connections:
                try:
                    lobby_connections[player_name].remove(queue)
                    if not lobby_connections[player_name]:
                        del lobby_connections[player_name]
                except ValueError:
                    pass
    
    return StreamingResponse(event_stream(), media_type="text/plain")


@app.get("/lobby/players/{player_name}")
async def lobby_players_partial(request: Request, player_name: str) -> HTMLResponse:
    """Return partial HTML with current player list for SSE updates"""
    try:
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player_name)
        player_status = "Available"
        try:
            player_status = lobby_service.get_player_status(player_name).value
        except ValueError:
            pass
            
        return templates.TemplateResponse(
            request,
            "components/players_list.html",
            {
                "player_name": player_name,
                "available_players": lobby_data,
                "player_status": player_status,
            },
        )
    except ValueError:
        return templates.TemplateResponse(
            request,
            "components/players_list.html",
            {
                "player_name": player_name,
                "available_players": [],
                "player_status": "Available",
            },
        )
