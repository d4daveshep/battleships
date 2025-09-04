from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
from typing import AsyncGenerator

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
    return {"status": "lobby cleared"}


@app.post("/select-opponent")
async def select_opponent(
    request: Request, player_name: str = Form(), opponent_name: str = Form()
) -> HTMLResponse:
    """Handle opponent selection and return updated lobby view"""

    # Update player statuses: sender becomes "Requesting Game", target becomes "Requesting Game"
    try:
        lobby_service.update_player_status(player_name, PlayerStatus.REQUESTING_GAME)
        lobby_service.update_player_status(opponent_name, PlayerStatus.REQUESTING_GAME)
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


async def generate_sse_events(player_name: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for lobby updates"""
    try:
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player_name)
        
        # Create template context similar to lobby_page
        template_context = {
            "player_name": player_name,
            "game_mode": "Two Player", 
            "available_players": lobby_data,
            "confirmation_message": "",
            "player_status": "Available",
            "error_message": "",
        }
        
        # Render the lobby partial template as HTML fragment
        html_content = templates.get_template("components/lobby_content.html").render(template_context)
        
        # Send as SSE data event
        yield f"data: {html_content}\n\n"
        
    except Exception as e:
        # Send error as SSE event
        yield f"event: error\ndata: {{\"error\": \"Failed to load lobby data: {str(e)}\"}}\n\n"


@app.get("/lobby/events/{player_name}")
async def lobby_events(player_name: str) -> StreamingResponse:
    """Server-Sent Events endpoint for real-time lobby updates"""
    
    # Validate player name using existing auth service
    validation: PlayerNameValidation = auth_service.validate_player_name(
        player_name, strip_quotes=True
    )
    
    if not validation.is_valid:
        raise HTTPException(status_code=422, detail=validation.error_message)
    
    # Return SSE stream
    return StreamingResponse(
        generate_sse_events(player_name),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
