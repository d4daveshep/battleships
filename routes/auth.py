"""Authentication and login routes."""

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from game.game_service import GameService
from game.player import Player, PlayerStatus
from services.auth_service import AuthService
from services.lobby_service import LobbyService

router: APIRouter = APIRouter(prefix="", tags=["auth"])

# Module-level service references (set during app initialization)
_templates: Jinja2Templates | None = None
_auth_service: AuthService | None = None
_game_service: GameService | None = None
_lobby_service: LobbyService | None = None


def set_up_auth_router(
    templates: Jinja2Templates,
    auth_service: AuthService,
    game_service: GameService,
    lobby_service: LobbyService,
) -> APIRouter:
    """Configure the auth router with required dependencies."""
    global _templates, _auth_service, _game_service, _lobby_service
    _templates = templates
    _auth_service = auth_service
    _game_service = game_service
    _lobby_service = lobby_service
    return router


def _get_templates() -> Jinja2Templates:
    """Get templates, raising if not initialized."""
    if _templates is None:
        raise RuntimeError("Router not initialized - call set_up_auth_router first")
    return _templates


def _get_auth_service() -> AuthService:
    """Get auth_service, raising if not initialized."""
    if _auth_service is None:
        raise RuntimeError("Router not initialized - call set_up_auth_router first")
    return _auth_service


def _get_game_service() -> GameService:
    """Get game_service, raising if not initialized."""
    if _game_service is None:
        raise RuntimeError("Router not initialized - call set_up_auth_router first")
    return _game_service


def _get_lobby_service() -> LobbyService:
    """Get lobby_service, raising if not initialized."""
    if _lobby_service is None:
        raise RuntimeError("Router not initialized - call set_up_auth_router first")
    return _lobby_service


def _create_login_error_response(
    request: Request,
    error_message: str,
    player_name: str = "",
    css_class: str = "error",
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTMLResponse:
    """Display the login page with an error message.

    Used for login validation errors and lobby operation errors that
    redirect users back to the login page.
    """
    templates = _get_templates()

    template_context: dict[str, str] = {
        "error_message": error_message,
        "player_name": player_name,
        "css_class": css_class,
    }

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=template_context,
        status_code=status_code,
    )


def _get_player_id(request: Request) -> str:
    """Get player ID from session.

    Args:
        request: The FastAPI request object containing session data

    Returns:
        The player ID from session

    Raises:
        HTTPException: 401 if no session or no player-id
    """
    player_id: str | None = request.session.get("player-id")
    if not player_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found - please login",
        )
    return player_id


def _get_player_from_session(request: Request) -> Player:
    """Get Player object from session.

    Args:
        request: The FastAPI request object containing session data

    Returns:
        The Player object for the session

    Raises:
        HTTPException: 401 if no session, 404 if player not found
    """
    player_id: str = _get_player_id(request)
    game_service = _get_game_service()
    player: Player | None = game_service.get_player(player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    return player


def _get_validated_player_name(request: Request, claimed_name: str) -> str:
    """Verify the session owns this player name.

    Args:
        request: The FastAPI request object containing session data
        claimed_name: The player name being claimed in the request

    Returns:
        The validated player name

    Raises:
        HTTPException: 401 if no session, 403 if session doesn't own player
    """
    player: Player = _get_player_from_session(request)
    if player.name != claimed_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not own this player",
        )
    return claimed_name


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
    request.session["player-id"] = player.id
    game_service.add_player(player)

    try:
        redirect_url: str
        if game_mode == "human":
            lobby_service.join_lobby(player)  # Add the player to the lobby
            redirect_url = "/lobby"

        elif game_mode == "computer":
            redirect_url = "/start-game"
        else:
            raise ValueError(f"Invalid game mode: {game_mode}")

        if request.headers.get("HX-Request"):
            response: Response = Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={"HX-Redirect": redirect_url},
            )
            return response
        else:
            return RedirectResponse(
                url=redirect_url, status_code=status.HTTP_303_SEE_OTHER
            )
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
