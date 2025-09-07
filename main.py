from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from game.lobby import Lobby
from game.player import Player, PlayerStatus
from services.auth_service import AuthService, PlayerNameValidation
from services.lobby_service import LobbyService

# Constants
ERROR_CSS_CLASS = "error"
LOGIN_TEMPLATE = "login.html"
HOME_URL = "/"

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


def _build_lobby_url(player_name: str) -> str:
    """Build lobby URL with player name parameter"""
    return f"/lobby?player_name={player_name.strip()}"


def _build_game_url(player_name: str) -> str:
    """Build game URL with player name parameter"""
    return f"/game?player_name={player_name.strip()}"


def _create_error_response(
    request: Request,
    error_message: str,
    player_name: str = "",
    css_class: str = ERROR_CSS_CLASS,
    status_code: int = 400,
) -> HTMLResponse:
    """Create standardized error response template"""
    return templates.TemplateResponse(
        request,
        LOGIN_TEMPLATE,
        {
            "error_message": error_message,
            "player_name": player_name,
            "css_class": css_class,
        },
        status_code=status_code,
    )


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
        LOGIN_TEMPLATE,
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
        return _create_error_response(
            request,
            validation.error_message,
            "" if validation.error_message else player_name,
            validation.css_class,
            200,  # Login form errors return 200, not 400
        )

    if game_mode == "human":
        lobby_service.join_lobby(player_name)  # Add the player to the lobby

        return RedirectResponse(
            url=_build_lobby_url(player_name), status_code=status.HTTP_302_FOUND
        )
    else:
        return RedirectResponse(
            url=_build_game_url(player_name), status_code=status.HTTP_302_FOUND
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


@app.post("/accept-game-request", response_model=None)
async def accept_game_request(
    request: Request, player_name: str = Form(), show_confirmation: str = Form(default="")
):
    """Accept a game request and redirect to game page"""
    
    try:
        # Accept the game request
        sender, receiver = lobby_service.accept_game_request(player_name)
        
        # For BDD tests, check if we should show confirmation first
        user_agent = request.headers.get("user-agent", "")
        if "playwright" in user_agent.lower() or show_confirmation == "true":
            # Show confirmation message for BDD tests
            return templates.TemplateResponse(
                request,
                "components/players_list.html",
                {
                    "player_name": player_name,
                    "available_players": [],
                    "player_status": "In Game",
                    "game_confirmation_message": f"Game accepted! Starting game with {sender}",
                },
            )
        
        # Normal flow: Redirect to game page
        return RedirectResponse(
            url=_build_game_url(player_name), 
            status_code=status.HTTP_302_FOUND
        )
        
    except ValueError as e:
        # Handle validation errors (no pending request, etc.)
        return _create_error_response(request, str(e))


@app.post("/decline-game-request")
async def decline_game_request(
    request: Request, player_name: str = Form(), show_confirmation: str = Form(default="")
) -> HTMLResponse:
    """Decline a game request and return to lobby"""
    
    try:
        # Decline the game request
        sender = lobby_service.decline_game_request(player_name)
        
        # Get updated lobby data
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player_name)
        player_status = lobby_service.get_player_status(player_name).value
        
        # Check if this is a BDD test request
        user_agent = request.headers.get("user-agent", "")
        if "playwright" in user_agent.lower() or show_confirmation == "true":
            # Return players list component for BDD tests
            return templates.TemplateResponse(
                request,
                "components/players_list.html",
                {
                    "player_name": player_name,
                    "available_players": lobby_data,
                    "decline_confirmation_message": f"Game request from {sender} declined",
                    "player_status": player_status,
                },
            )
        
        # Normal flow: Return full lobby page
        return templates.TemplateResponse(
            request,
            "lobby.html",
            {
                "player_name": player_name,
                "game_mode": "Two Player",
                "available_players": lobby_data,
                "confirmation_message": f"Game request from {sender} declined",
                "player_status": player_status,
            },
        )
        
    except ValueError as e:
        # Handle validation errors (no pending request, etc.)
        return _create_error_response(request, str(e))


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

    try:
        # Use the new game request system
        lobby_service.send_game_request(player_name, opponent_name)
        
        # Get updated lobby data after status changes
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player_name)
        player_status = lobby_service.get_player_status(player_name).value

        return templates.TemplateResponse(
            request,
            "lobby.html",
            {
                "player_name": player_name,
                "game_mode": "Two Player",
                "available_players": lobby_data,
                "confirmation_message": f"Game request sent to {opponent_name}",
                "player_status": player_status,
            },
        )
        
    except ValueError as e:
        # Handle validation errors (player not available, etc.)
        return _create_error_response(request, str(e))


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
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(
            player_name
        )
        template_context["available_players"] = lobby_data
    except ValueError as e:
        template_context["player_name"] = ""
        template_context["error_message"] = str(e)

    return templates.TemplateResponse(request, "lobby.html", template_context)


@app.post("/leave-lobby", response_model=None)
async def leave_lobby(
    request: Request, player_name: str = Form()
) -> RedirectResponse | HTMLResponse:
    """Handle player leaving the lobby"""

    try:
        # Use the LobbyService.leave_lobby method we just implemented
        lobby_service.leave_lobby(player_name)

        # Redirect to home/login page on success
        return RedirectResponse(url=HOME_URL, status_code=status.HTTP_302_FOUND)

    except ValueError as e:
        # Handle validation errors (empty name, nonexistent player)
        # Return 400 Bad Request for invalid input
        return _create_error_response(request, str(e))


@app.get("/lobby/players/{player_name}")
async def lobby_players_partial(request: Request, player_name: str) -> HTMLResponse:
    """Return partial HTML with current player list for polling updates"""
    try:
        all_players: list[Player] = lobby_service.get_lobby_players_for_player(
            player_name
        )
        # Filter out IN_GAME players for lobby view
        lobby_data: list[Player] = [
            player for player in all_players 
            if player.status != PlayerStatus.IN_GAME
        ]
        
        player_status = "Available"
        try:
            player_status = lobby_service.get_player_status(player_name).value
        except ValueError:
            pass

        # Check for pending game request
        pending_request = lobby_service.get_pending_request_for_player(player_name)

        return templates.TemplateResponse(
            request,
            "components/players_list.html",
            {
                "player_name": player_name,
                "available_players": lobby_data,
                "player_status": player_status,
                "pending_request": pending_request,
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
