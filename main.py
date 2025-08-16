from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse:
    if game_mode == "human":
        return templates.TemplateResponse(
            "lobby.html",
            {
                "request": request,
                "player_name": player_name,
                "game_mode": "Two Player",
            },
        )
    else:
        return templates.TemplateResponse(
            "game.html",
            {
                "request": request,
                "player_name": player_name,
                "game_mode": "Single Player",
            },
        )


@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("game.html", {"request": request})


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("lobby.html", {"request": request})
