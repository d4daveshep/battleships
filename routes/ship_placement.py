"""Ship placement routes."""

import asyncio
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from game.game_service import GameService, PlayerAlreadyInGameException
from game.model import (
    Coord,
    GameBoard,
    Orientation,
    Ship,
    ShipAlreadyPlacedError,
    ShipPlacementOutOfBoundsError,
    ShipPlacementTooCloseError,
    ShipType,
)
from game.player import Player, PlayerStatus
from services.lobby_service import LobbyService

from routes.helpers import (
    _get_game_service,
    _get_lobby_service,
    _get_player_from_session,
    _get_player_id,
    _get_templates,
    _get_validated_player_name,
    _is_multiplayer,
)

router: APIRouter = APIRouter(prefix="", tags=["ship_placement"])


def set_up_ship_placement_router(
    templates: Jinja2Templates,
    game_service: GameService,
    lobby_service: LobbyService,
) -> APIRouter:
    """Configure the ship placement router with required dependencies."""
    return router


@router.get("/place-ships", response_class=HTMLResponse)
async def ship_placement_page(request: Request) -> HTMLResponse:
    """Display the ship placement page"""
    templates = _get_templates()
    game_service = _get_game_service()

    # Get player from session
    player: Player = _get_player_from_session(request)
    player_id: str = player.id

    # Get board state
    board: GameBoard = game_service.get_or_create_ship_placement_board(player_id)
    placed_ships: dict[str, dict[str, Any]] = board.get_placed_ships_for_display()

    # Check if player is ready
    is_ready: bool = game_service.is_player_ready(player_id)

    # Check if multiplayer
    is_multiplayer: bool = _is_multiplayer(player_id)

    # Determine status message
    ships_count: int = len(placed_ships)
    status_message: str = ""
    if is_ready:
        status_message = "Waiting for opponent to finish placing ships..."
    elif ships_count < 5:
        status_message = "Place all ships to continue"
    else:
        status_message = "All ships placed - click Ready when done"

    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player.name,
            "placed_ships": placed_ships,
            "is_ready": is_ready,
            "status_message": status_message,
            "is_multiplayer": is_multiplayer,
        },
    )


@router.post("/place-ship", response_class=HTMLResponse)
async def place_ship(
    request: Request,
    player_name: str = Form(),
    ship_name: str = Form(),
    start_coordinate: str = Form(),
    orientation: str = Form(),
) -> HTMLResponse:
    """Handle ship placement on the board"""
    templates = _get_templates()
    game_service = _get_game_service()

    try:
        # Create the ship based on type name
        ship_type: ShipType = ShipType.from_ship_name(ship_name)
        ship: Ship = Ship(ship_type)

        # Create the start coord and orientation
        start: Coord = Coord[start_coordinate.upper()]
        # Replace hyphens with underscores for enum member lookup
        orient: Orientation = Orientation[orientation.upper().replace("-", "_")]

        # Get or create board for ship placement
        _get_validated_player_name(request, player_name)
        board: GameBoard = game_service.get_or_create_ship_placement_board(
            player_id=_get_player_id(request)
        )
        board.place_ship(ship, start, orient)

    except (
        ShipAlreadyPlacedError,
        ShipPlacementOutOfBoundsError,
        ShipPlacementTooCloseError,
    ) as e:
        # Get current board state to show what's already placed
        _get_validated_player_name(request, player_name)
        try:
            board: GameBoard = game_service.get_or_create_ship_placement_board(
                player_id=_get_player_id(request)
            )
        except Exception:
            # If no board exists yet, create empty one for error display
            board = GameBoard()
        placed_ships: dict[str, dict[str, list[str]]] = (
            board.get_placed_ships_for_display()
        )

        # Use the user-friendly message from the exception
        user_friendly_error: str = e.user_message

        # Check if player is ready
        is_ready: bool = game_service.is_player_ready(_get_player_id(request))

        # Return ship_placement.html with error and current state
        return templates.TemplateResponse(
            request,
            "ship_placement.html",
            {
                "player_name": player_name,
                "placed_ships": placed_ships,
                "placement_error": user_friendly_error,
                "is_ready": is_ready,
                "is_multiplayer": _is_multiplayer(_get_player_id(request)),
            },
            status_code=status.HTTP_200_OK,
        )

    except (ValueError, KeyError):
        # Handle invalid direction/orientation
        _get_validated_player_name(request, player_name)
        try:
            board: GameBoard = game_service.get_or_create_ship_placement_board(
                player_id=_get_player_id(request)
            )
        except Exception:
            board = GameBoard()
        placed_ships: dict[str, dict[str, list[str]]] = (
            board.get_placed_ships_for_display()
        )

        user_friendly_error: str = "Invalid direction"

        # Check if player is ready
        is_ready: bool = game_service.is_player_ready(_get_player_id(request))

        # Return ship_placement.html with error and current state
        return templates.TemplateResponse(
            request,
            "ship_placement.html",
            {
                "player_name": player_name,
                "placed_ships": placed_ships,
                "placement_error": user_friendly_error,
                "is_ready": is_ready,
                "is_multiplayer": _is_multiplayer(_get_player_id(request)),
            },
            status_code=status.HTTP_200_OK,
        )

    # Get all placed ships from the board to display
    placed_ships: dict[str, dict[str, list[str]]] = board.get_placed_ships_for_display()

    # Check if player is ready
    is_ready: bool = game_service.is_player_ready(_get_player_id(request))

    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
            "is_ready": is_ready,
            "is_multiplayer": _is_multiplayer(_get_player_id(request)),
        },
    )


@router.post("/remove-ship", response_class=HTMLResponse)
async def remove_ship(
    request: Request,
    player_name: str = Form(),
    ship_name: str = Form(),
) -> HTMLResponse:
    """Remove a placed ship from the board"""
    templates = _get_templates()
    game_service = _get_game_service()

    # Validate player owns this session
    _get_validated_player_name(request, player_name)
    player_id: str = _get_player_id(request)

    # Check if player is ready - if so, don't allow modifications
    is_ready: bool = game_service.is_player_ready(player_id)

    # Get the board
    board: GameBoard = game_service.get_or_create_ship_placement_board(player_id)

    # Only remove ship if player is not ready
    if not is_ready:
        try:
            ship_type: ShipType = ShipType.from_ship_name(ship_name)
            board.remove_ship(ship_type)
        except ValueError:
            # Invalid ship name - just ignore and return current state
            pass

    # Get updated placed ships
    placed_ships: dict[str, dict[str, Any]] = board.get_placed_ships_for_display()

    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
            "is_ready": is_ready,
            "status_message": "Waiting for opponent to place their ships..."
            if is_ready
            else "",
            "is_multiplayer": _is_multiplayer(player_id),
        },
    )


@router.post("/random-ship-placement", response_class=HTMLResponse)
async def random_ship_placement(
    request: Request,
    player_name: str = Form(),
) -> HTMLResponse:
    """Place all ships randomly on the board"""
    templates = _get_templates()
    game_service = _get_game_service()

    # Validate player owns this session
    _get_validated_player_name(request, player_name)
    player_id: str = _get_player_id(request)

    # Check if player is ready - if so, don't allow modifications
    is_ready: bool = game_service.is_player_ready(player_id)

    # Only place ships randomly if player is not ready
    if not is_ready:
        game_service.place_ships_randomly(player_id)

    # Get the board with placed ships
    board: GameBoard = game_service.get_or_create_ship_placement_board(player_id)

    # Get placed ships for template
    placed_ships: dict[str, dict[str, Any]] = board.get_placed_ships_for_display()

    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
            "is_ready": is_ready,
            "status_message": "Waiting for opponent to place their ships..."
            if is_ready
            else "",
            "is_multiplayer": _is_multiplayer(player_id),
        },
    )


@router.post("/reset-all-ships", response_class=HTMLResponse)
async def reset_all_ships(
    request: Request,
    player_name: str = Form(),
) -> HTMLResponse:
    """Reset all placed ships (clear the board)"""
    templates = _get_templates()
    game_service = _get_game_service()

    # Validate player owns this session
    _get_validated_player_name(request, player_name)
    player_id: str = _get_player_id(request)

    # Check if player is ready - if so, don't allow modifications
    is_ready: bool = game_service.is_player_ready(player_id)

    # Get the board
    board: GameBoard = game_service.get_or_create_ship_placement_board(player_id)

    # Only clear ships if player is not ready
    if not is_ready:
        board.clear_all_ships()

    # Get placed ships for template
    placed_ships: dict[str, dict[str, Any]] = board.get_placed_ships_for_display()

    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
            "is_ready": is_ready,
            "status_message": "Waiting for opponent to place their ships..."
            if is_ready
            else "",
            "is_multiplayer": _is_multiplayer(player_id),
        },
    )


@router.post("/ready-for-game", response_model=None)
async def ready_for_game(
    request: Request,
    player_name: str = Form(),
) -> HTMLResponse | Response | RedirectResponse:
    """Handle player ready state."""
    templates = _get_templates()
    game_service = _get_game_service()
    lobby_service = _get_lobby_service()

    # Validate player
    _get_validated_player_name(request, player_name)
    player_id = _get_player_id(request)

    # Mark player as ready
    game_service.set_player_ready(player_id)

    # Check if in multiplayer (has opponent in lobby)
    opponent_id: str | None = lobby_service.get_opponent(player_id)

    if opponent_id:
        # Check if opponent is ready
        if game_service.is_player_ready(opponent_id):
            # Both ready! Create game.
            game_id = _create_game_for_ready_players(
                player_id, opponent_id, game_service, lobby_service
            )

            # Return redirect to game
            redirect_url = f"/game/{game_id}"
            if request.headers.get("HX-Request"):
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": redirect_url},
                )
            return RedirectResponse(
                url=redirect_url, status_code=status.HTTP_303_SEE_OTHER
            )

    # Single player or waiting for opponent - show placement page with ready state
    return _render_placement_page_waiting(
        request, player_name, player_id, templates, game_service
    )


def _create_game_for_ready_players(
    player_id: str,
    opponent_id: str,
    game_service: GameService,
    lobby_service: LobbyService,
) -> str:
    """Handle player ready state - game already exists from accept.

    Args:
        player_id: The first player's ID
        opponent_id: The second player's ID
        game_service: The GameService instance
        lobby_service: The LobbyService instance

    Returns:
        The existing game ID

    Raises:
        HTTPException: If player/opponent not found or game doesn't exist
    """
    # Get players
    player = game_service.get_player(player_id)
    opponent = game_service.get_player(opponent_id)

    if not player or not opponent:
        raise HTTPException(status_code=500, detail="Player or opponent not found")

    # Game should already exist from accept-game-request
    # Just transfer the ship placement board to the game
    try:
        game = game_service.games_by_player[player_id]
        game_id = game.id
    except KeyError:
        raise HTTPException(
            status_code=500,
            detail="Game not found - should have been created when request was accepted",
        )

    # Transfer ship placement board to game (only for the player who just became ready)
    game_service.transfer_ship_placement_board_to_game(game_id, player_id, player)

    # Update game status to PLAYING (game is now starting)
    from game.game_service import GameStatus

    game.status = GameStatus.PLAYING

    return game_id


def _render_placement_page_waiting(
    request: Request,
    player_name: str,
    player_id: str,
    templates: Jinja2Templates,
    game_service: GameService,
) -> HTMLResponse:
    """Render ship placement page in waiting state.

    Args:
        request: The FastAPI request object
        player_name: The player's name
        player_id: The player's ID
        templates: The Jinja2 templates
        game_service: The GameService instance

    Returns:
        HTMLResponse with the rendered template
    """
    board = game_service.get_or_create_ship_placement_board(player_id)
    placed_ships = board.get_placed_ships_for_display()

    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
            "is_ready": True,
            "is_multiplayer": True,
            "status_message": "Waiting for opponent to finish placing ships...",
        },
    )


def _get_opponent_id_or_404(player_id: str) -> str:
    """Get opponent ID or raise 404 if player is not in an active game."""
    game_service = _get_game_service()
    lobby_service = _get_lobby_service()

    # Check GameService first (active game)
    opponent_id = game_service.get_opponent_id(player_id)

    # If not in active game, check Lobby (paired)
    if not opponent_id:
        opponent_id = lobby_service.get_opponent(player_id)

    if not opponent_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player is not in an active game",
        )
    return opponent_id


def _check_game_redirect_url(request: Request, player_id: str) -> str | None:
    """Check if player's game has started, return redirect URL or None.

    Only redirects if:
    1. Player is in a game
    2. Game status is PLAYING (game has actually started)

    During ship placement phase (game status is SETUP or CREATED),
    players should stay on /place-ships.

    Args:
        request: The FastAPI request object
        player_id: The player ID to check

    Returns:
        Redirect URL if game has started, None otherwise
    """
    from game.game_service import GameStatus

    game_service = _get_game_service()
    player = _get_player_from_session(request)

    if player.id in game_service.games_by_player:
        game = game_service.games_by_player[player.id]
        # Only redirect if game has actually started
        if game.status == GameStatus.PLAYING:
            return f"/game/{game.id}"
    return None


def _fetch_opponent_status(opponent_id: str) -> dict[str, bool]:
    """Fetch opponent status for ship placement.

    Args:
        opponent_id: The opponent's player ID

    Returns:
        dict with 'left' (opponent left lobby) and 'ready' (opponent ready)
    """
    game_service = _get_game_service()
    lobby_service = _get_lobby_service()

    # Check if opponent has left the lobby
    opponent_left = True
    try:
        player_status = lobby_service.get_player_status(opponent_id)
        opponent_left = player_status != PlayerStatus.IN_GAME
    except ValueError:
        pass  # Opponent not found, so they left

    # Check if opponent is ready (only if they haven't left)
    opponent_ready = not opponent_left and game_service.is_player_ready(opponent_id)

    return {"left": opponent_left, "ready": opponent_ready}


def _render_opponent_status(
    request: Request, opponent_id: str
) -> HTMLResponse | Response:
    """Render opponent status component.

    Args:
        request: The FastAPI request object
        opponent_id: The opponent's player ID

    Returns:
        HTMLResponse with opponent status or redirect Response
    """
    templates = _get_templates()
    game_service = _get_game_service()

    # Check if game started for current player (redirect if so)
    redirect_url = _check_game_redirect_url(request, opponent_id)
    if redirect_url and request.headers.get("HX-Request"):
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={"HX-Redirect": redirect_url},
        )

    # Fetch opponent status
    opponent_status = _fetch_opponent_status(opponent_id)

    return templates.TemplateResponse(
        request=request,
        name="components/opponent_status.html",
        context={
            "opponent_ready": opponent_status["ready"],
            "version": game_service.get_placement_version(),
            "opponent_left": opponent_status["left"],
        },
    )


@router.post("/leave-placement", response_model=None)
async def leave_placement(request: Request) -> RedirectResponse:
    """Handle leaving ship placement (e.g. when opponent disconnects)"""
    player = _get_player_from_session(request)
    lobby_service = _get_lobby_service()
    game_service = _get_game_service()

    # Reset player status to AVAILABLE
    try:
        lobby_service.update_player_status(player.id, PlayerStatus.AVAILABLE)

        # Notify placement change so opponent's long-poll detects the status change
        game_service.notify_placement_change()

    except ValueError:
        pass

    return RedirectResponse(url="/lobby", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/place-ships/opponent-status", response_model=None)
async def ship_placement_opponent_status(
    request: Request,
) -> HTMLResponse | Response:
    """Get opponent's ship placement status.

    Returns HTML component showing whether opponent is ready or still placing ships.
    Used for HTMX partial updates during multiplayer ship placement.
    """
    player: Player = _get_player_from_session(request)
    opponent_id: str = _get_opponent_id_or_404(player.id)
    return _render_opponent_status(request, opponent_id)


@router.get("/place-ships/opponent-status/long-poll", response_model=None)
async def ship_placement_opponent_status_long_poll(
    request: Request, timeout: int = 30, version: int | None = None
) -> HTMLResponse | Response:
    """Long polling endpoint for opponent status updates.

    Returns immediately if version is None or has changed.
    Otherwise waits up to `timeout` seconds for a state change.
    """
    player: Player = _get_player_from_session(request)
    opponent_id: str = _get_opponent_id_or_404(player.id)
    game_service = _get_game_service()

    current_version: int = game_service.get_placement_version()

    # Return immediately if no version provided or version has changed
    if version is None or current_version != version:
        return _render_opponent_status(request, opponent_id)

    # Wait for changes or timeout
    try:
        await asyncio.wait_for(
            game_service.wait_for_placement_change(version), timeout=timeout
        )
    except asyncio.TimeoutError:
        pass  # Timeout is fine, just return current state

    return _render_opponent_status(request, opponent_id)


# Forward references for type hints (resolved at runtime)
from routes.helpers import LobbyService  # noqa: E402
