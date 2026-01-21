"""Routes package for Battleships game.

This package contains router modules organized by domain:
- auth: Authentication and login routes
- lobby: Multiplayer lobby routes
- ship_placement: Ship placement routes
- gameplay: Active game gameplay routes
- start_game: Game start confirmation routes
"""

from routes.auth import router as auth_router
from routes.lobby import router as lobby_router
from routes.ship_placement import router as ship_placement_router
from routes.gameplay import router as gameplay_router
from routes.start_game import router as start_game_router

__all__ = [
    "auth_router",
    "lobby_router",
    "ship_placement_router",
    "gameplay_router",
    "start_game_router",
]
