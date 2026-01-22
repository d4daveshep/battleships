"""Active game gameplay routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from game.game_service import Game, GameService, GameStatus
from game.player import Player

from routes.helpers import (
    _get_game_service,
    _get_player_from_session,
    _get_templates,
)

router: APIRouter = APIRouter(prefix="", tags=["gameplay"])


def set_up_gameplay_router(
    templates: Jinja2Templates,
    game_service: GameService,
) -> APIRouter:
    """Configure the gameplay router with required dependencies."""
    return router


@router.get("/game/{game_id}", response_class=HTMLResponse)
async def game_page(request: Request, game_id: str) -> HTMLResponse:
    """Display the gameplay page for an active game.

    Args:
        request: The FastAPI request object containing session data
        game_id: The unique identifier for the game

    Returns:
        HTMLResponse with gameplay template showing both player boards

    Raises:
        HTTPException: 404 if game not found, 403 if player not in this game
    """
    templates = _get_templates()
    game_service = _get_game_service()

    # Get current player from session
    player: Player = _get_player_from_session(request)

    # Fetch game from game_service
    game: Game | None = game_service.games.get(game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Game {game_id} not found"
        )

    # Determine if current player is player_1 or player_2
    current_player: Player
    opponent: Player | None

    if game.player_1.id == player.id:
        current_player = game.player_1
        opponent = game.player_2
    elif game.player_2 and game.player_2.id == player.id:
        current_player = game.player_2
        opponent = game.player_1
    else:
        # Player is not part of this game
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a player in this game",
        )

    # Get boards for both players
    from game.model import GameBoard

    player_board: GameBoard = game.board[current_player]
    opponent_board: GameBoard = game.board[opponent] if opponent else GameBoard()

    # Convert boards to template-friendly format
    player_board_data: dict[str, Any] = {
        "ships": player_board.get_placed_ships_for_display()
    }
    opponent_board_data: dict[str, Any] = {
        "ships": opponent_board.get_placed_ships_for_display()
    }

    # Prepare template context
    opponent_name: str = opponent.name if opponent else "Computer"
    status_message: str | None = None

    # Add status message based on game state if needed
    if game.status == GameStatus.CREATED:
        status_message = "Game is starting..."
    elif game.status == GameStatus.SETUP:
        status_message = "Setting up the game..."

    template_context: dict[str, Any] = {
        "player_name": current_player.name,
        "opponent_name": opponent_name,
        "game_id": game_id,
        "player_board": player_board_data,
        "opponent_board": opponent_board_data,
        "round_number": 1,  # Placeholder - will be dynamic later
        "status_message": status_message,
    }

    # Render gameplay template
    return templates.TemplateResponse(
        request=request,
        name="gameplay.html",
        context=template_context,
    )
