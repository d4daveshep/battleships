"""Game start confirmation routes."""

from typing import Any, NamedTuple

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from game.player import Player, PlayerStatus

from routes.helpers import (
    _get_game_service,
    _get_lobby_service,
    _get_player_from_session,
    _get_templates,
)

router: APIRouter = APIRouter(prefix="", tags=["start_game"])


class ValidatedAction(NamedTuple):
    """Result of action validation with redirect URL if applicable."""

    action: str
    game_id: str | None = None


class StartGameContext(NamedTuple):
    """Template context data for start game page."""

    player_name: str
    opponent_name: str
    game_mode: str


# ============================================================================
# Helper Functions
# ============================================================================


def _get_opponent_info_from_lobby(player_id: str) -> tuple[str, bool]:
    """Get opponent name from lobby if player is in a multiplayer game.

    Args:
        player_id: The unique identifier of the player

    Returns:
        Tuple of (opponent_name, is_multiplayer) where is_multiplayer is True
        if player is in a multiplayer game
    """
    lobby_service = _get_lobby_service()
    try:
        player_status: PlayerStatus = lobby_service.get_player_status(player_id)
        if player_status == PlayerStatus.IN_GAME:
            opponent_name: str | None = lobby_service.get_opponent_name(player_id)
            if opponent_name:
                return (opponent_name, True)
    except ValueError:
        # Player not in lobby - single player mode
        pass
    return ("", False)


def _create_start_game_context(player: Player) -> StartGameContext:
    """Create the template context for the start game page.

    Args:
        player: The player requesting the start game page

    Returns:
        StartGameContext with player name, opponent name, and game mode
    """
    opponent_name: str
    is_multiplayer: bool
    opponent_name, is_multiplayer = _get_opponent_info_from_lobby(player.id)

    game_mode: str = "Two Player" if is_multiplayer else "Single Player"

    return StartGameContext(
        player_name=player.name,
        opponent_name=opponent_name,
        game_mode=game_mode,
    )


VALID_ACTIONS: tuple[str, ...] = ("start_game", "abandon_game", "launch_game")


def _validate_action(action: str | None) -> ValidatedAction:
    """Validate the action parameter and return validated result.

    Args:
        action: The action string to validate

    Returns:
        ValidatedAction with the validated action

    Raises:
        HTTPException: 400 if action is invalid or missing
    """
    if not action or action not in VALID_ACTIONS:
        valid_actions_str: str = ", ".join(VALID_ACTIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Must be one of: {valid_actions_str}",
        )
    return ValidatedAction(action=action)


def _get_redirect_url_for_action(
    validated_action: ValidatedAction, player_id: str
) -> str:
    """Get the redirect URL based on the validated action.

    Args:
        validated_action: The validated action result
        player_id: The player ID for starting games

    Returns:
        Redirect URL string

    Raises:
        HTTPException: 400 if action is somehow invalid (shouldn't happen)
    """
    game_service = _get_game_service()
    action: str = validated_action.action

    if action == "start_game":
        return "/place-ships"
    elif action == "launch_game":
        game_id: str = game_service.start_single_player_game(player_id)
        return f"/game/{game_id}"
    elif action == "abandon_game":
        return "/login"
    else:
        # This should never happen due to _validate_action, but keep for safety
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}",
        )


def _create_start_game_template_context(
    player: Player, opponent_name: str, game_mode: str
) -> dict[str, Any]:
    """Create the template context dictionary for rendering.

    Args:
        player: The player requesting the page
        opponent_name: The opponent's name (empty string if single player)
        game_mode: The game mode string

    Returns:
        Dictionary with context for template rendering
    """
    return {
        "player_name": player.name,
        "opponent_name": opponent_name,
        "game_mode": game_mode,
    }


# ============================================================================
# Route Setup
# ============================================================================


def set_up_start_game_router(
    templates: Jinja2Templates,
    game_service: "GameService",
    lobby_service: "LobbyService",
) -> APIRouter:
    """Configure the start game router with required dependencies."""
    return router


# ============================================================================
# Route Handlers
# ============================================================================


@router.get("/start-game", response_class=HTMLResponse)
async def start_game_page(request: Request) -> HTMLResponse:
    """Start game confirmation page.

    Args:
        request: The FastAPI request object

    Returns:
        HTMLResponse with start game confirmation page or error
    """
    templates = _get_templates()
    player: Player = _get_player_from_session(request)

    # Get context for template rendering
    context: StartGameContext = _create_start_game_context(player)

    return templates.TemplateResponse(
        request=request,
        name="start_game.html",
        context=_create_start_game_template_context(
            player=player,
            opponent_name=context.opponent_name,
            game_mode=context.game_mode,
        ),
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
        action: The action to perform (start_game, abandon_game, launch_game)
        player_name: The player name (optional, from ship placement)

    Returns:
        RedirectResponse to appropriate page based on action
    """
    player: Player = _get_player_from_session(request)

    # Validate and process the action
    validated_action: ValidatedAction = _validate_action(action)
    redirect_url: str = _get_redirect_url_for_action(validated_action, player.id)

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
