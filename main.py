from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

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



@app.post("/leave-lobby", response_model=None)
async def leave_lobby(
    request: Request, player_name: str = Form()
) -> RedirectResponse | HTMLResponse:
    """Handle player leaving the lobby"""
    
    try:
        # Use the LobbyService.leave_lobby method we just implemented
        lobby_service.leave_lobby(player_name)
        
        # Redirect to home/login page on success
        return RedirectResponse(url="/", status_code=302)
        
    except ValueError as e:
        # Handle validation errors (empty name, nonexistent player)
        # Return 400 Bad Request for invalid input
        return templates.TemplateResponse(
            request,
            "login.html", 
            {
                "error_message": str(e),
                "player_name": "",
                "css_class": "error",
            },
            status_code=400
        )


@app.get("/lobby/players/{player_name}")
async def lobby_players_partial(request: Request, player_name: str) -> HTMLResponse:
    """Return partial HTML with current player list for polling updates"""
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
