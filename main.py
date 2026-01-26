"""Battleships game FastAPI application.

This is the main entry point for the application. Routes are organized
into separate router modules in the `routes` package.
"""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from game.lobby import Lobby
from services.auth_service import AuthService
from services.lobby_service import LobbyService
from game.game_service import GameService

# Import routers
from routes.helpers import set_up_helpers
from routes.auth import set_up_auth_router, router as auth_router
from routes.lobby import set_up_lobby_router, router as lobby_router
from routes.ship_placement import (
    set_up_ship_placement_router,
    router as ship_placement_router,
)
from routes.gameplay import set_up_gameplay_router, router as gameplay_router
from routes.start_game import set_up_start_game_router, router as start_game_router

app: FastAPI = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates: Jinja2Templates = Jinja2Templates(directory="templates")


# Global lobby instance for state management
_game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(_game_lobby)
game_service: GameService = GameService()


# Set up helpers module first (shared by all routers)
set_up_helpers(templates, game_service, lobby_service)

# Set up all routers with their dependencies
set_up_auth_router(templates, auth_service, game_service, lobby_service)
set_up_lobby_router(templates, game_service, lobby_service)
set_up_ship_placement_router(templates, game_service, lobby_service)
set_up_gameplay_router(templates, game_service)
set_up_start_game_router(templates, game_service, lobby_service)

# Include all routers
app.include_router(auth_router)
app.include_router(lobby_router)
app.include_router(ship_placement_router)
app.include_router(gameplay_router)
app.include_router(start_game_router)


# === Testing Endpoints ===
# Include testing router only when TESTING environment variable is set
# or when running in development mode (always include for now during development)
_include_testing = os.environ.get("TESTING", "true").lower() == "true"

if _include_testing:
    from routes.testing import set_up_testing_router, router as testing_router

    set_up_testing_router(_game_lobby, game_service, lobby_service)
    app.include_router(testing_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for infrastructure monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
