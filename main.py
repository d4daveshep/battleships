from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse:
    hx_request: str | None = request.headers.get("HX-Request")
    if hx_request:
        return templates.TemplateResponse("game.html", {
            "request": request,
            "player_name": player_name,
            "game_mode": "Single Player" if game_mode == "computer" else "Two Player"
        })
    return RedirectResponse(url="/game", status_code=302)


@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("game.html", {"request": request})
