from typing import NamedTuple

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


class PlayerNameValidation(NamedTuple):
    is_valid: bool
    error_message: str
    css_class: str


def validate_player_name_input(
    player_name: str, strip_quotes: bool = False
) -> PlayerNameValidation:
    """Centralized player name validation logic"""
    clean_name: str = player_name.strip()
    if strip_quotes:
        clean_name = clean_name.strip("\"'")

    if not clean_name:
        return _validation_error("Player name is required")
    
    if not (2 <= len(clean_name) <= 20):
        return _validation_error("Player name must be between 2 and 20 characters")
    
    if not clean_name.replace(" ", "").isalnum():
        return _validation_error("Player name can only contain letter, numbers and spaces")
    
    return PlayerNameValidation(is_valid=True, error_message="", css_class="valid")


def _validation_error(message: str) -> PlayerNameValidation:
    """Helper function to create validation error responses"""
    return PlayerNameValidation(is_valid=False, error_message=message, css_class="error")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "player_name": "", "error_message": "", "css_class": ""},
    )


@app.post("/", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse:
    validation: PlayerNameValidation = validate_player_name_input(player_name, strip_quotes=True)

    if not validation.is_valid:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
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
        "game.html",
        {"request": request, "player_name": player_name, "game_mode": "Single Player"},
    )


@app.post("/player-name")
async def validate_player_name(
    request: Request, player_name: str = Form()
) -> HTMLResponse:
    """Validate player name and return partial HTML with validation result"""
    validation: PlayerNameValidation = validate_player_name_input(player_name, strip_quotes=False)

    return templates.TemplateResponse(
        "components/player_name_input.html",
        {
            "request": request,
            "player_name": player_name,
            "error_message": validation.error_message,
            "css_class": validation.css_class,
        },
    )


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request, player_name: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        "lobby.html",
        {"request": request, "player_name": player_name, "game_mode": "Two Player"},
    )
