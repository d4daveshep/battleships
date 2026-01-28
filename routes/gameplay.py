"""Active game gameplay routes."""

from typing import Any, NamedTuple

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from game.game_service import AimResult, Game, GameService, GameStatus
from game.model import Coord, GameBoard
from game.player import Player

from routes.helpers import (
    _get_game_service,
    _get_player_from_session,
    _get_templates,
)

router: APIRouter = APIRouter(prefix="", tags=["gameplay"])


class PlayerGameRole(NamedTuple):
    """Represents a player's role in a game."""

    current_player: Player
    opponent: Player | None


def _get_game_or_404(game_id: str) -> Game:
    """Fetch game by ID or raise 404 if not found.

    Args:
        game_id: The unique identifier for the game

    Returns:
        The Game object

    Raises:
        HTTPException: 404 if game not found
    """
    game_service = _get_game_service()
    game: Game | None = game_service.games.get(game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )
    return game


def _get_player_role(game: Game, player: Player) -> PlayerGameRole:
    """Determine if player is player_1, player_2, or not in game.

    Args:
        game: The Game object
        player: The Player object to check

    Returns:
        PlayerGameRole with current_player and opponent

    Raises:
        HTTPException: 403 if player not in this game
    """
    if game.player_1.id == player.id:
        return PlayerGameRole(current_player=game.player_1, opponent=game.player_2)
    elif game.player_2 and game.player_2.id == player.id:
        return PlayerGameRole(current_player=game.player_2, opponent=game.player_1)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a player in this game",
        )


def _format_board_for_template(board: GameBoard) -> dict[str, Any]:
    """Convert board to template-friendly format.

    Args:
        board: The GameBoard to format

    Returns:
        Dictionary with board data for template rendering
    """
    return {"ships": board.get_placed_ships_for_display()}


def _get_game_status_message(game: Game) -> str | None:
    """Get status message based on game state.

    Args:
        game: The Game object

    Returns:
        Status message string or None if no message needed
    """
    if game.status == GameStatus.CREATED:
        return "Game is starting..."
    elif game.status == GameStatus.SETUP:
        return "Setting up the game..."
    return None


def _create_gameplay_context(
    current_player: Player,
    opponent: Player | None,
    player_board: GameBoard,
    opponent_board: GameBoard,
    game_id: str,
    game: Game,
) -> dict[str, Any]:
    """Create the template context for the gameplay page.

    Args:
        current_player: The player whose view this is
        opponent: The opponent player (None for single player vs Computer)
        player_board: Current player's game board
        opponent_board: Opponent's game board
        game_id: The game ID
        game: The Game object (for status message)

    Returns:
        Dictionary with all context needed to render gameplay template
    """
    opponent_name: str = opponent.name if opponent else "Computer"
    status_message: str | None = _get_game_status_message(game)
    round_number: int = game.round
    shots_available: int = game.get_shots_available(current_player.id)
    aimed_coords: set[Coord] = game.get_aimed_shots(current_player.id)
    aimed_count: int = len(aimed_coords)
    aimed_coordinates: list[str] = [c.name for c in aimed_coords]

    return {
        "player_name": current_player.name,
        "opponent_name": opponent_name,
        "game_id": game_id,
        "player_board": _format_board_for_template(player_board),
        "opponent_board": _format_board_for_template(opponent_board),
        "round_number": round_number,
        "shots_available": shots_available,
        "aimed_count": aimed_count,
        "aimed_coordinates": aimed_coordinates,
        "status_message": status_message,
    }


def set_up_gameplay_router(
    templates: Jinja2Templates,
    game_service: GameService,
) -> APIRouter:
    """Configure the gameplay router with required dependencies."""
    return router


@router.post("/aim-shot", response_class=HTMLResponse)
async def aim_shot(
    request: Request,
    game_id: str = Form(...),
    coordinate: str = Form(...),
) -> HTMLResponse:
    """Toggle aiming at a coordinate for the current player.

    This is an HTMX endpoint that returns an updated partial HTML fragment.

    Args:
        request: The FastAPI request object containing session data
        game_id: The unique identifier for the game
        coordinate: The coordinate to toggle (e.g., "A1", "J10")

    Returns:
        HTMLResponse with updated aiming status partial

    Raises:
        HTTPException: 404 if game not found, 403 if player not in this game
    """
    templates = _get_templates()
    game_service = _get_game_service()

    # Get current player from session
    player: Player = _get_player_from_session(request)

    # Fetch game and validate player is in it
    game: Game = _get_game_or_404(game_id)
    role: PlayerGameRole = _get_player_role(game, player)

    # Toggle aim and get result
    try:
        result: AimResult = game_service.toggle_aim(game_id, player.id, coordinate)
    except ValueError as e:
        # Check if it's the shot limit error
        if "Cannot aim more shots than available" in str(e):
            # Get current aimed count for the display
            aimed_coords: set[Coord] = game.get_aimed_shots(player.id)
            aimed_count: int = len(aimed_coords)
            shots_available: int = game.get_shots_available(player.id)
            # Return error message component with shot count
            return templates.TemplateResponse(
                request=request,
                name="components/error_message.html",
                context={
                    "error_message": "All available shots aimed",
                    "aimed_count": aimed_count,
                    "shots_available": shots_available,
                },
            )
        elif "Cannot aim shots after firing" in str(e):
            # Return error message for trying to aim after firing
            aimed_coords: set[Coord] = game.get_aimed_shots(player.id)
            aimed_count: int = len(aimed_coords)
            shots_available: int = game.get_shots_available(player.id)
            return templates.TemplateResponse(
                request=request,
                name="components/error_message.html",
                context={
                    "error_message": "Cannot aim shots after firing - you have already fired",
                    "aimed_count": aimed_count,
                    "shots_available": shots_available,
                },
            )
        else:
            # Re-raise other ValueErrors
            raise

    # Get the current aimed coordinates for the template
    aimed_coords: set[Coord] = game.get_aimed_shots(player.id)

    # Return updated partial HTML
    return templates.TemplateResponse(
        request=request,
        name="components/aiming_status.html",
        context={
            "game_id": game_id,
            "coordinate": coordinate,
            "is_aimed": result.is_aimed,
            "aimed_count": result.aimed_count,
            "shots_available": result.shots_available,
            "aimed_coordinates": [c.name for c in aimed_coords],
        },
    )


@router.post("/fire-shots", response_class=HTMLResponse)
async def fire_shots(
    request: Request,
    game_id: str = Form(...),
    player_name: str = Form(...),
) -> HTMLResponse:
    """Submit the player's aimed shots and enter waiting state.

    This endpoint handles the "Fire Shots" button action. It submits all
    currently aimed shots and changes the player's status to waiting for
    opponent. The player can then no longer aim additional shots.

    Args:
        request: The FastAPI request object containing session data
        game_id: The unique identifier for the game
        player_name: The name of the player firing shots

    Returns:
        HTMLResponse with updated gameplay template showing waiting status

    Raises:
        HTTPException: 404 if game not found, 403 if player not in this game
        HTTPException: 400 if no shots aimed
    """
    templates = _get_templates()
    game_service = _get_game_service()

    # Get current player from session
    player: Player = _get_player_from_session(request)

    # Validate player name matches session
    if player.name != player_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player name doesn't match session",
        )

    # Fetch game and validate player is in it
    game: Game = _get_game_or_404(game_id)
    role: PlayerGameRole = _get_player_role(game, player)

    # Fire the shots
    try:
        game_service.fire_shots(game_id, player.id)
    except ValueError as e:
        error_msg = str(e)
        if "no shots aimed" in error_msg:
            # Return error message
            return templates.TemplateResponse(
                request=request,
                name="components/error_message.html",
                context={"error_message": error_msg},
            )
        elif "Cannot aim shots after firing" in error_msg:
            # Player already fired - return waiting status
            aimed_coords: set[Coord] = game.get_aimed_shots(player.id)
            aimed_count: int = len(aimed_coords)
            shots_available: int = game.get_shots_available(player.id)
            return templates.TemplateResponse(
                request=request,
                name="components/error_message.html",
                context={"error_message": error_msg},
            )
        else:
            raise

    # Get updated game state
    player_board: GameBoard = game.board[role.current_player]
    opponent_board: GameBoard = (
        game.board[role.opponent] if role.opponent else GameBoard()
    )

    # Check if opponent is also waiting (both fired)
    opponent_waiting = False
    if role.opponent:
        opponent_waiting = game.is_waiting_for_opponent(role.opponent.id)

    # Render updated gameplay template with waiting status
    return templates.TemplateResponse(
        request=request,
        name="gameplay.html",
        context={
            **_create_gameplay_context(
                current_player=role.current_player,
                opponent=role.opponent,
                player_board=player_board,
                opponent_board=opponent_board,
                game_id=game_id,
                game=game,
            ),
            # Add waiting status message
            "status_message": "Waiting for opponent to fire...",
            "waiting_for_opponent": game.is_waiting_for_opponent(player.id),
        },
    )


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

    # Get current player from session
    player: Player = _get_player_from_session(request)

    # Fetch game and determine player roles
    game: Game = _get_game_or_404(game_id)
    role: PlayerGameRole = _get_player_role(game, player)

    # Get boards for both players
    player_board: GameBoard = game.board[role.current_player]
    opponent_board: GameBoard = (
        game.board[role.opponent] if role.opponent else GameBoard()
    )

    # Render gameplay template
    # Check if player is waiting for opponent and add status message
    context = _create_gameplay_context(
        current_player=role.current_player,
        opponent=role.opponent,
        player_board=player_board,
        opponent_board=opponent_board,
        game_id=game_id,
        game=game,
    )

    # Add waiting status if player has fired
    if game.is_waiting_for_opponent(player.id):
        context["status_message"] = "Waiting for opponent to fire..."
        context["waiting_for_opponent"] = True

    return templates.TemplateResponse(
        request=request,
        name="gameplay.html",
        context=context,
    )
