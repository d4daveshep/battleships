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
    if not player_name.strip():
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": "Player name is required",
            },
        )
    
    if game_mode == "human":
        return RedirectResponse(url="/lobby", status_code=302)
    else:
        return RedirectResponse(url="/game", status_code=302)


@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("game.html", {
        "request": request,
        "player_name": "Alice",
        "game_mode": "Single Player"
    })


@app.post("/player-name")
async def validate_player_name(request: Request, player_name: str = Form()) -> HTMLResponse:
    """Validate player name and return partial HTML with validation result"""
    error_message = ""
    css_class = ""
    
    if not player_name.strip():
        error_message = "Player name is required"
        css_class = "error"
    elif len(player_name.strip()) < 2:
        error_message = "Player name must be at least 2 characters"
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
async def lobby_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("lobby.html", {
        "request": request,
        "player_name": "Bob", 
        "game_mode": "Two Player"
    })
