"""Game start confirmation routes."""

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from game.game_service import GameService
from game.player import Player, PlayerStatus
from services.lobby_service import LobbyService

from routes.helpers import (
    _get_game_service,
    _get_lobby_service,
    _get_player_from_session,
    _get_templates,
)

router: APIRouter = APIRouter(prefix="", tags=["start_game"])


def set_up_start_game_router(
    templates: Jinja2Templates,
    game_service: "GameService",
    lobby_service: LobbyService,
) -> APIRouter:
    """Configure the start game router with required dependencies."""
    return router


@router.get("/start-game", response_class=HTMLResponse)
async def start_game_page(request: Request) -> HTMLResponse:
    """Start game confirmation page.

    Args:
        request: The FastAPI request object

    Returns:
        HTMLResponse with start game confirmation page or error
    """
    templates = _get_templates()
    lobby_service = _get_lobby_service()

    # Get player from session
    player: Player = _get_player_from_session(request)

    # Get opponent from lobby if player is in a multiplayer game
    # Only check lobby if player status is IN_GAME
    opponent_name: str = ""
    try:
        # Check if player is in lobby and has IN_GAME status
        player_status: PlayerStatus = lobby_service.get_player_status(player.id)
        if player_status == PlayerStatus.IN_GAME:
            opponent_name_from_lobby: str | None = lobby_service.get_opponent_name(
                player.id
            )
            if opponent_name_from_lobby:
                opponent_name = opponent_name_from_lobby
    except ValueError:
        # Player not in lobby - single player mode
        pass

    game_mode: str = "Two Player" if opponent_name else "Single Player"
    return templates.TemplateResponse(
        request=request,
        name="start_game.html",
        context={
            "player_name": player.name,
            "opponent_name": opponent_name,
            "game_mode": game_mode,
        },
    )


@router.post("/start-game", response_model=None)
async def start_game_submit(
    request: Request,
    action: str = Form(default=""),
    player_name: str = Form(default=""),
) -> RedirectResponse:
    """Handle start game confirmation form submission.

    Args:
        request: The FastAPI request object
        action: The action to perform (start_game, abandon_game)
        player_name: The player name (optional, from ship placement)

    Returns:
        RedirectResponse to appropriate page based on action
    """
    game_service = _get_game_service()

    # Get player from session
    player: Player = _get_player_from_session(request)

    # Validate action parameter
    valid_actions: list[str] = ["start_game", "abandon_game", "launch_game"]
    if not action or action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
        )

    # Route based on action
    redirect_url: str
    if action == "start_game":
        redirect_url = "/place-ships"
    elif action == "launch_game":
        # Start single player game
        game_id = game_service.start_single_player_game(player.id)
        return RedirectResponse(
            url=f"/game/{game_id}", status_code=status.HTTP_303_SEE_OTHER
        )
    elif action == "abandon_game":
        redirect_url = "/login"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}",
        )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
