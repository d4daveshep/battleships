from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from game.lobby import Lobby
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


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request, player_name: str = "") -> HTMLResponse:
    # Get lobby data using service layer
    lobby_data = lobby_service.get_lobby_data_for_player(player_name)

    return templates.TemplateResponse(
        request,
        "lobby.html",
        {
            "player_name": player_name,
            "game_mode": "Two Player",
            **lobby_data,
        },
    )
