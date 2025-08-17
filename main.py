from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {
        "request": request,
        "player_name": "",
        "error_message": "",
        "css_class": ""
    })


@app.post("/", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse:
    # Strip quotes and whitespace for validation
    clean_name = player_name.strip().strip('"\'')
    
    if not clean_name:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": "Player name is required",
                "player_name": "",
                "css_class": ""
            },
        )
    elif len(clean_name) < 2:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": "Player name must be at least 2 characters long",
                "player_name": player_name,
                "css_class": "error"
            },
        )
    elif len(clean_name) > 20:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": "Player name must be 20 characters or less",
                "player_name": player_name,
                "css_class": "error"
            },
        )
    
    if game_mode == "human":
        return RedirectResponse(url=f"/lobby?player_name={player_name.strip()}", status_code=302)
    else:
        return RedirectResponse(url=f"/game?player_name={player_name.strip()}", status_code=302)


@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request, player_name: str = "") -> HTMLResponse:
    return templates.TemplateResponse("game.html", {
        "request": request,
        "player_name": player_name,
        "game_mode": "Single Player"
    })


@app.post("/player-name")
async def validate_player_name(request: Request, player_name: str = Form()) -> HTMLResponse:
    """Validate player name and return partial HTML with validation result"""
    error_message = ""
    css_class = ""
    
    # Strip quotes and whitespace for validation
    clean_name = player_name.strip().strip('"\'')
    
    if not clean_name:
        error_message = "Player name is required"
        css_class = "error"
    elif len(clean_name) < 2:
        error_message = "Player name must be at least 2 characters long"
        css_class = "error"
    elif len(clean_name) > 20:
        error_message = "Player name must be 20 characters or less"
        css_class = "error"
    else:
        css_class = "valid"
    
    return templates.TemplateResponse("components/player_name_input.html", {
        "request": request,
        "player_name": player_name,
        "error_message": error_message,
        "css_class": css_class
    })


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request, player_name: str = "") -> HTMLResponse:
    return templates.TemplateResponse("lobby.html", {
        "request": request,
        "player_name": player_name,
        "game_mode": "Two Player"
    })
