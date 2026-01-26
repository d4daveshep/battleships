"""Authentication and login routes."""

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from game.player import Player, PlayerStatus
from services.auth_service import AuthService

from routes.helpers import (
    _create_login_error_response,
    _get_game_service,
    _get_lobby_service,
    _get_templates,
    _redirect_or_htmx,
    SESSION_PLAYER_ID_KEY,
)

router: APIRouter = APIRouter(prefix="", tags=["auth"])

# Module-level service references (set during app initialization)
_auth_service: AuthService | None = None


def set_up_auth_router(
    templates: Jinja2Templates,
    auth_service: AuthService,
    game_service: "GameService",
    lobby_service: "LobbyService",
) -> APIRouter:
    """Configure the auth router with required dependencies."""
    global _auth_service
    _auth_service = auth_service
    return router


def _get_auth_service() -> AuthService:
    """Get auth_service, raising if not initialized."""
    if _auth_service is None:
        raise RuntimeError("Router not initialized - call set_up_auth_router first")
    return _auth_service


@router.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request) -> HTMLResponse:
    """Welcome page with link to login"""
    templates = _get_templates()
    return templates.TemplateResponse(request=request, name="welcome.html", context={})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Display the login page"""
    templates = _get_templates()
    template_context: dict[str, str] = {
        "player_name": "",
        "error_message": "",
        "css_class": "",
    }

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=template_context,
    )


@router.post("/login", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse | Response:
    """Handle login form submission"""
    auth_service = _get_auth_service()
    game_service = _get_game_service()
    lobby_service = _get_lobby_service()

    validation = auth_service.validate_player_name(player_name, strip_quotes=True)

    if not validation.is_valid:
        return _create_login_error_response(
            request=request,
            error_message=validation.error_message,
            player_name="" if validation.error_message else player_name,
            css_class=validation.css_class,
            status_code=status.HTTP_200_OK,  # Login form errors return 200, not 400
        )

    # Generate and store player ID in session and player object in game service
    player: Player = Player(player_name, PlayerStatus.AVAILABLE)
    game_service.add_player(player)
    request.session[SESSION_PLAYER_ID_KEY] = player.id

    try:
        redirect_url: str
        if game_mode == "human":
            lobby_service.join_lobby(player)  # Add the player to the lobby
            redirect_url = "/lobby"

        elif game_mode == "computer":
            redirect_url = "/start-game"
        else:
            raise ValueError(f"Invalid game mode: {game_mode}")

        return _redirect_or_htmx(request, redirect_url)
    except ValueError as e:
        return _create_login_error_response(
            request=request,
            error_message=str(e),
            player_name=player_name,
            css_class="error",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post("/player-name")
async def validate_player_name(
    request: Request, player_name: str = Form()
) -> HTMLResponse:
    """Validate player name and return partial HTML with validation result"""
    templates = _get_templates()
    auth_service = _get_auth_service()

    validation = auth_service.validate_player_name(player_name, strip_quotes=False)

    return templates.TemplateResponse(
        request=request,
        name="components/player_name_input.html",
        context={
            "player_name": player_name,
            "error_message": validation.error_message,
            "css_class": validation.css_class,
        },
    )


@router.get("/goodbye", response_class=HTMLResponse)
async def goodbye_page(request: Request) -> HTMLResponse:
    """Goodbye page when user exits the game"""
    return HTMLResponse(content="<html><body><h1>Goodbye</h1></body></html>")


# Forward references for type hints (resolved at runtime)
from routes.helpers import GameService, LobbyService  # noqa: E402
