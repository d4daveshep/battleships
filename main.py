import asyncio
import secrets
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response

from game.game_service import (
    Game,
    GameService,
    GameStatus,
    PlayerAlreadyInGameException,
)
from game.lobby import Lobby
from game.model import (
    Coord,
    CoordHelper,
    GameBoard,
    Orientation,
    Ship,
    ShipAlreadyPlacedError,
    ShipPlacementOutOfBoundsError,
    ShipPlacementTooCloseError,
    ShipType,
)
from game.player import GameRequest, Player, PlayerStatus
from services.auth_service import AuthService, PlayerNameValidation
from services.gameplay_service import AimShotResult, FireShotsResult, GameplayService
from services.lobby_service import LobbyService

app: FastAPI = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates: Jinja2Templates = Jinja2Templates(directory="templates")


# Global lobby instance for state management
_game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(_game_lobby)
gameplay_service: GameplayService = GameplayService()
game_service: GameService = GameService()


def _get_player_id(request: Request) -> str:
    """Get player ID from session

    Args:
        request: The FastAPI request object containing session data

    Returns:
        The player ID from session

    Raises:
        HTTPException: 401 if no session or no player-id
    """
    player_id: str | None = request.session.get("player-id")
    if not player_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found - please login",
        )
    return player_id


def _get_player_from_session(request: Request) -> Player:
    """Get Player object from session

    Args:
        request: The FastAPI request object containing session data

    Returns:
        The Player object for the session

    Raises:
        HTTPException: 401 if no session, 404 if player not found
    """
    player_id: str = _get_player_id(request)
    player: Player | None = game_service.get_player(player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    return player


def _get_validated_player_name(request: Request, claimed_name: str) -> str:
    """Verify the session owns this player name

    Args:
        request: The FastAPI request object containing session data
        claimed_name: The player name being claimed in the request

    Returns:
        The validated player name

    Raises:
        HTTPException: 401 if no session, 403 if session doesn't own player
    """
    player: Player = _get_player_from_session(request)
    if player.name != claimed_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not own this player",
        )
    return claimed_name


def _create_login_error_response(
    request: Request,
    error_message: str,
    player_name: str = "",
    css_class: str = "error",
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTMLResponse:
    """Display the login page with an error message

    Used for login validation errors and lobby operation errors that
    redirect users back to the login page.
    """

    template_context: dict[str, str] = {
        "error_message": error_message,
        "player_name": player_name,
        "css_class": css_class,
    }

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=template_context,
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request) -> HTMLResponse:
    """Welcome page with link to login"""
    return templates.TemplateResponse(request=request, name="welcome.html", context={})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    template_context: dict[str, str] = {
        "player_name": "",
        "error_message": "",
        "css_class": "",
    }

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=template_context,
    )


@app.post("/login", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse | Response:
    validation: PlayerNameValidation = auth_service.validate_player_name(
        player_name, strip_quotes=True
    )

    if not validation.is_valid:
        return _create_login_error_response(
            request=request,
            error_message=validation.error_message,
            player_name="" if validation.error_message else player_name,
            css_class=validation.css_class,
            status_code=status.HTTP_200_OK,  # Login form errors return 200, not 400
        )

    # Generate and store player ID in session and player object in game service
    player: Player = Player(player_name, PlayerStatus.AVAILABLE)
    request.session["player-id"] = player.id
    game_service.add_player(player)

    try:
        redirect_url: str
        if game_mode == "human":
            lobby_service.join_lobby(player)  # Add the player to the lobby
            redirect_url = "/lobby"

        elif game_mode == "computer":
            redirect_url = "/start-game"
        else:
            raise ValueError(f"Invalid game mode: {game_mode}")

        if request.headers.get("HX-Request"):
            response: Response = Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={"HX-Redirect": redirect_url},
            )
            return response
        else:
            return RedirectResponse(
                url=redirect_url, status_code=status.HTTP_303_SEE_OTHER
            )
    except ValueError as e:
        return _create_login_error_response(
            request=request,
            error_message=str(e),
            player_name=player_name,
            css_class="error",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.get("/place-ships", response_class=HTMLResponse)
async def ship_placement_page(request: Request) -> HTMLResponse:
    # Get player from session
    player: Player = _get_player_from_session(request)
    player_id: str = player.id

    # Get board state
    board: GameBoard = game_service.get_or_create_ship_placement_board(player_id)
    placed_ships: dict[str, dict[str, Any]] = board.get_placed_ships_for_display()

    # Check if player is ready
    is_ready: bool = game_service.is_player_ready(player_id)

    # Check if multiplayer
    opponent_id: str | None = game_service.get_opponent_id(player_id)
    if not opponent_id:
        opponent_id = lobby_service.get_opponent(player_id)
    is_multiplayer: bool = opponent_id is not None

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


@app.post("/place-ship", response_class=HTMLResponse)
async def place_ship(
    request: Request,
    player_name: str = Form(),
    ship_name: str = Form(),
    start_coordinate: str = Form(),
    orientation: str = Form(),
) -> HTMLResponse:
    """Handle ship placement on the board"""

    try:
        # Create the ship based on type name
        ship_type: ShipType = ShipType.from_ship_name(ship_name)
        ship: Ship = Ship(ship_type)

        # Create the start coord and orientation
        start: Coord = Coord[start_coordinate.upper()]
        # Replace hyphens with underscores for enum member lookup
        orient: Orientation = Orientation[orientation.upper().replace("-", "_")]

        # Get or create board for ship placement
        validated_player_name: str = _get_validated_player_name(request, player_name)
        board: GameBoard = game_service.get_or_create_ship_placement_board(
            player_id=_get_player_id(request)
        )
        board.place_ship(ship, start, orient)
        # Board is already stored in game_service, no need to store separately

    except (
        ShipAlreadyPlacedError,
        ShipPlacementOutOfBoundsError,
        ShipPlacementTooCloseError,
    ) as e:
        # Get current board state to show what's already placed
        validated_player_name: str = _get_validated_player_name(request, player_name)
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
                "is_multiplayer": game_service.get_opponent_id(_get_player_id(request))
                is not None
                or lobby_service.get_opponent(_get_player_id(request)) is not None,
            },
            status_code=status.HTTP_200_OK,
        )

    except (ValueError, KeyError) as e:
        # Handle invalid direction/orientation
        validated_player_name: str = _get_validated_player_name(request, player_name)
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
                "is_multiplayer": game_service.get_opponent_id(_get_player_id(request))
                is not None
                or lobby_service.get_opponent(_get_player_id(request)) is not None,
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
            "is_multiplayer": game_service.get_opponent_id(_get_player_id(request))
            is not None
            or lobby_service.get_opponent(_get_player_id(request)) is not None,
        },
    )


@app.post("/remove-ship", response_class=HTMLResponse)
async def remove_ship(
    request: Request,
    player_name: str = Form(),
    ship_name: str = Form(),
) -> HTMLResponse:
    """Remove a placed ship from the board

    Args:
        request: The FastAPI request object
        player_name: The player's name (for validation)
        ship_name: The name of the ship to remove

    Returns:
        HTMLResponse with ship placement page showing updated board
    """
    # Validate player owns this session
    validated_player_name: str = _get_validated_player_name(request, player_name)
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
            "is_multiplayer": game_service.get_opponent_id(player_id) is not None
            or lobby_service.get_opponent(player_id) is not None,
        },
    )


@app.post("/random-ship-placement", response_class=HTMLResponse)
async def random_ship_placement(
    request: Request,
    player_name: str = Form(),
) -> HTMLResponse:
    """Place all ships randomly on the board

    Args:
        request: The FastAPI request object
        player_name: The player's name (for validation)

    Returns:
        HTMLResponse with ship placement page showing randomly placed ships
    """
    # Validate player owns this session
    validated_player_name: str = _get_validated_player_name(request, player_name)
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
            "is_multiplayer": game_service.get_opponent_id(player_id) is not None
            or lobby_service.get_opponent(player_id) is not None,
        },
    )


@app.post("/reset-all-ships", response_class=HTMLResponse)
async def reset_all_ships(
    request: Request,
    player_name: str = Form(),
) -> HTMLResponse:
    """Reset all placed ships (clear the board)

    Args:
        request: The FastAPI request object
        player_name: The player's name (for validation)

    Returns:
        HTMLResponse with ship placement page showing empty board
    """
    # Validate player owns this session
    validated_player_name: str = _get_validated_player_name(request, player_name)
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
            "is_multiplayer": game_service.get_opponent_id(player_id) is not None
            or lobby_service.get_opponent(player_id) is not None,
        },
    )


@app.get("/start-game", response_class=HTMLResponse)
async def start_game_page(request: Request) -> HTMLResponse:
    """Start game confirmation page

    Args:
        request: The FastAPI request object

    Returns:
        HTMLResponse with start game confirmation page or error
    """
    # Get player from session
    player: Player = _get_player_from_session(request)

    # Get opponent from lobby if player is in a multiplayer game
    # Only check lobby if player status is IN_GAME
    opponent_name: str = ""
    try:
        # Check if player is in lobby and has IN_GAME status
        player_status: PlayerStatus = lobby_service.get_player_status(player.id)
        if player_status == PlayerStatus.IN_GAME:
            opponent_name_from_lobby: str | None = lobby_service.get_opponent_name(
                player.id
            )
            if opponent_name_from_lobby:
                opponent_name = opponent_name_from_lobby
    except ValueError:
        # Player not in lobby - single player mode
        pass

    game_mode: str = "Two Player" if opponent_name else "Single Player"
    return templates.TemplateResponse(
        request=request,
        name="start_game.html",
        context={
            "player_name": player.name,
            "opponent_name": opponent_name,
            "game_mode": game_mode,
        },
    )


@app.post("/start-game", response_model=None)
async def start_game_submit(
    request: Request,
    action: str = Form(default=""),
    player_name: str = Form(default=""),
) -> RedirectResponse:
    """Handle start game confirmation form submission

    Args:
        request: The FastAPI request object
        action: The action to perform (start_game, abandon_game)
        player_name: The player name (optional, from ship placement)

    Returns:
        RedirectResponse to appropriate page based on action
    """
    # Get player from session
    player: Player = _get_player_from_session(request)

    # Validate action parameter
    valid_actions: list[str] = ["start_game", "abandon_game", "launch_game"]
    if not action or action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
        )

    # Route based on action
    redirect_url: str
    if action == "start_game":
        redirect_url = "/place-ships"
    elif action == "launch_game":
        # Start single player game
        # TODO: Handle multiplayer game start
        game_id = game_service.start_single_player_game(player.id)
        return RedirectResponse(
            url=f"/game/{game_id}", status_code=status.HTTP_303_SEE_OTHER
        )
    elif action == "abandon_game":
        redirect_url = "/login"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}",
        )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.post("/ready-for-game", response_model=None)
async def ready_for_game(
    request: Request,
    player_name: str = Form(),
) -> HTMLResponse | Response | RedirectResponse:
    """Handle player ready state

    Args:
        request: The FastAPI request object
        player_name: The player's name

    Returns:
        HTMLResponse with ship placement page in ready state, or redirect if game starts
    """
    # Validate player
    validated_player_name = _get_validated_player_name(request, player_name)
    player_id = _get_player_id(request)

    # Mark player as ready
    game_service.set_player_ready(player_id)

    # Check if in multiplayer (has opponent in lobby)
    opponent_id: str | None = lobby_service.get_opponent(player_id)

    if opponent_id:
        # Check if opponent is ready
        if game_service.is_player_ready(opponent_id):
            # Both ready! Create game.
            try:
                # Reset status to allow game creation (transition from Lobby to Game)
                player = game_service.get_player(player_id)
                opponent = game_service.get_player(opponent_id)

                if not player or not opponent:
                    raise HTTPException(
                        status_code=500, detail="Player or opponent not found"
                    )

                player.status = PlayerStatus.AVAILABLE
                opponent.status = PlayerStatus.AVAILABLE

                game_id = game_service.create_two_player_game(player_id, opponent_id)

                # Transfer ship placement boards to game
                game = game_service.games[game_id]
                if player_id in game_service.ship_placement_boards:
                    game.board[player] = game_service.ship_placement_boards[player_id]
                    del game_service.ship_placement_boards[player_id]
                if opponent_id in game_service.ship_placement_boards:
                    game.board[opponent] = game_service.ship_placement_boards[
                        opponent_id
                    ]
                    del game_service.ship_placement_boards[opponent_id]

                # Remove players from lobby (they are now in game)
                # Note: create_two_player_game sets status to IN_GAME
                # We should probably remove them from lobby active_games too
                # But lobby_service.leave_lobby might be too aggressive?
                # For now, let's leave them in lobby as IN_GAME (which is what accept_request did)
                # But we need to ensure get_opponent_id works.

            except PlayerAlreadyInGameException:
                # Game might have been created by opponent concurrently
                try:
                    game = game_service.games_by_player[player_id]
                    game_id = game.id
                except KeyError:
                    # Should not happen if logic is correct
                    raise HTTPException(status_code=500, detail="Game creation failed")

            redirect_url = f"/game/{game_id}"
            if request.headers.get("HX-Request"):
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": redirect_url},
                )
            return RedirectResponse(
                url=redirect_url, status_code=status.HTTP_303_SEE_OTHER
            )

    # Get board state
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


# === Ship Placement Opponent Status Endpoints ===


def _get_opponent_id_or_404(player_id: str) -> str:
    """Get opponent ID or raise 404 if player is not in an active game."""
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


def _render_opponent_status(
    request: Request, opponent_id: str
) -> HTMLResponse | Response:
    """Render opponent status component.

    Args:
        request: The FastAPI request object
        opponent_id: The opponent's player ID

    Returns:
        HTMLResponse with opponent status component
    """
    # Check if game started for current player
    player = _get_player_from_session(request)
    try:
        # Check if player is in a game in GameService
        if player.id in game_service.games_by_player:
            game = game_service.games_by_player[player.id]
            redirect_url = f"/game/{game.id}"

            if request.headers.get("HX-Request"):
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": redirect_url},
                )
    except Exception:
        pass

    # Check if opponent is still in lobby
    opponent_left = False
    try:
        status_val = lobby_service.get_player_status(opponent_id)
        # If opponent is not IN_GAME, they have left the placement/game
        if status_val != PlayerStatus.IN_GAME:
            opponent_left = True
    except ValueError:
        opponent_left = True

    opponent_ready: bool = False
    if not opponent_left:
        opponent_ready = game_service.is_player_ready(opponent_id)

    version: int = game_service.get_placement_version()

    return templates.TemplateResponse(
        request=request,
        name="components/opponent_status.html",
        context={
            "opponent_ready": opponent_ready,
            "version": version,
            "opponent_left": opponent_left,
        },
    )


@app.post("/leave-placement", response_model=None)
async def leave_placement(request: Request) -> RedirectResponse:
    """Handle leaving ship placement (e.g. when opponent disconnects)"""
    player = _get_player_from_session(request)

    # Reset player status to AVAILABLE
    try:
        lobby_service.update_player_status(player.id, PlayerStatus.AVAILABLE)

        # Notify placement change so opponent's long-poll detects the status change
        game_service.notify_placement_change()

        # Remove from active games if present (cleanup pairing)
        # Lobby doesn't have a direct method for this, but update_status might be enough?
        # No, active_games persists.
        # We should probably leave lobby and rejoin?

        # For now, just redirect to lobby. The state might be messy but it allows navigation.
    except ValueError:
        pass

    return RedirectResponse(url="/lobby", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/place-ships/opponent-status", response_model=None)
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


@app.get("/place-ships/opponent-status/long-poll", response_model=None)
async def ship_placement_opponent_status_long_poll(
    request: Request, timeout: int = 30, version: int | None = None
) -> HTMLResponse | Response:
    """Long polling endpoint for opponent status updates.

    Returns immediately if version is None or has changed.
    Otherwise waits up to `timeout` seconds for a state change.
    """
    player: Player = _get_player_from_session(request)
    opponent_id: str = _get_opponent_id_or_404(player.id)

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


@app.get("/game/{game_id}", response_class=HTMLResponse)
async def game_page(request: Request, game_id: str) -> HTMLResponse:
    """Display the gameplay page for an active game

    Args:
        request: The FastAPI request object containing session data
        game_id: The unique identifier for the game

    Returns:
        HTMLResponse with gameplay template showing both player boards

    Raises:
        HTTPException: 404 if game not found, 403 if player not in this game
    """
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
    player_board: GameBoard = game.board[current_player]
    opponent_board: GameBoard = game.board[opponent] if opponent else GameBoard()

    # Convert boards to template-friendly format
    player_board_data: dict[str, Any] = {
        "ships": player_board.get_placed_ships_for_display()
    }

    # Get incoming shots (shots received from opponent)
    shots_received: dict[str, int] = {}
    for ship_type, hits in player_board.hits_by_ship.items():
        for coord, round_num in hits:
            shots_received[coord.name] = round_num

    player_board_data = {
        "ships": player_board.get_placed_ships_for_display(),
        "shots_received": shots_received,
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


def _ensure_gameplay_initialized(game_id: str, player_id: str) -> Game:
    """Ensure game exists, player is authorized, and gameplay is initialized.

    Args:
        game_id: The ID of the game
        player_id: The ID of the player

    Returns:
        The Game object

    Raises:
        HTTPException: 404 if game not found, 403 if player not authorized
    """
    # Verify game exists
    game: Game | None = game_service.games.get(game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Game {game_id} not found"
        )

    # Verify player is in this game
    if game.player_1.id != player_id and (
        not game.player_2 or game.player_2.id != player_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a player in this game",
        )

    # At this point, we know player_2 exists (either player_1 or player_2 matched)
    assert game.player_2 is not None, "Two-player game must have player_2"

    # Ensure round exists and boards are registered
    if game_id not in gameplay_service.active_rounds:
        # Create round 1 for this game
        gameplay_service.create_round(game_id=game_id, round_number=1)

        # Register player boards
        current_player: Player = (
            game.player_1 if game.player_1.id == player_id else game.player_2
        )
        opponent: Player = (
            game.player_2 if game.player_1.id == player_id else game.player_1
        )

        gameplay_service.register_player_board(
            game_id=game_id,
            player_id=current_player.id,
            board=game.board[current_player],
        )
        gameplay_service.register_player_board(
            game_id=game_id, player_id=opponent.id, board=game.board[opponent]
        )

    return game


@app.post("/game/{game_id}/aim-shot", response_class=HTMLResponse)
async def aim_shot(
    request: Request, game_id: str, coord: str = Form(...)
) -> HTMLResponse:
    """Add a shot to the aiming queue for current round.

    Args:
        request: The FastAPI request object containing session data
        game_id: The ID of the game
        coord: The coordinate string (from form data)

    Returns:
        HTML response with updated aiming interface

    Raises:
        HTTPException: 401 if not authenticated, 400 if validation fails, 404 if game not found
    """
    # Get player from session
    player_id: str = _get_player_id(request)

    # Ensure game exists and gameplay is initialized
    _ensure_gameplay_initialized(game_id, player_id)

    # Parse coordinate
    try:
        coord_enum: Coord = Coord[coord.upper()]
    except KeyError:
        # If invalid coordinate, render interface with error
        return _render_aiming_interface(
            request, game_id, player_id, error_message=f"Invalid coordinate: {coord}"
        )

    # Aim the shot
    result: AimShotResult = gameplay_service.aim_shot(
        game_id=game_id, player_id=player_id, coord=coord_enum
    )

    if not result.success:
        # If aiming failed (e.g. duplicate or limit reached), render interface with error
        return _render_aiming_interface(
            request, game_id, player_id, error_message=result.error_message
        )

    # Return updated aiming interface
    return _render_aiming_interface(request, game_id, player_id)


@app.get("/game/{game_id}/aimed-shots")
async def get_aimed_shots(request: Request, game_id: str) -> dict[str, Any]:
    """Get currently aimed shots for player.

    Args:
        request: The FastAPI request object containing session data
        game_id: The ID of the game

    Returns:
        JSON response with list of aimed coordinates

    Raises:
        HTTPException: 401 if not authenticated, 404 if game not found
    """
    # Get player from session
    player_id: str = _get_player_id(request)

    # Ensure game exists and gameplay is initialized
    _ensure_gameplay_initialized(game_id, player_id)

    # Get aimed shots
    aimed_coords: list[Coord] = gameplay_service.get_aimed_shots(game_id, player_id)
    coord_names: list[str] = [coord.name for coord in aimed_coords]

    # Get shots available
    shots_available: int = gameplay_service._get_shots_available(game_id, player_id)

    return {
        "coords": coord_names,
        "count": len(coord_names),
        "shots_available": shots_available,
    }


@app.delete("/game/{game_id}/aim-shot/{coord}", response_class=HTMLResponse)
async def clear_aimed_shot(request: Request, game_id: str, coord: str) -> HTMLResponse:
    """Remove a shot from aiming queue.

    Args:
        request: The FastAPI request object containing session data
        game_id: The ID of the game
        coord: The coordinate to remove

    Returns:
        HTML response with updated aiming interface

    Raises:
        HTTPException: 401 if not authenticated, 400 if invalid coord, 404 if game not found
    """
    # Get player from session
    player_id: str = _get_player_id(request)

    # Ensure game exists and gameplay is initialized
    _ensure_gameplay_initialized(game_id, player_id)

    # Parse coordinate
    try:
        coord_enum: Coord = Coord[coord.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid coordinate: {coord}",
        )

    # Remove the shot
    gameplay_service.clear_aimed_shot(
        game_id=game_id, player_id=player_id, coord=coord_enum
    )

    # Return updated aiming interface
    return _render_aiming_interface(request, game_id, player_id)


def _render_aiming_interface(
    request: Request,
    game_id: str,
    player_id: str,
    error_message: str | None = None,
    waiting_message: str | None = None,
) -> HTMLResponse:
    """Render the aiming interface component.

    Args:
        request: The FastAPI request object
        game_id: The ID of the game
        player_id: The ID of the player
        error_message: Optional error message to display
        waiting_message: Optional waiting message to display

    Returns:
        HTML response with aiming interface component
    """
    # Get aimed shots
    aimed_coords: list[Coord] = gameplay_service.get_aimed_shots(game_id, player_id)
    aimed_shots: list[str] = [coord.name for coord in aimed_coords]

    # Get shots available
    shots_available: int = gameplay_service._get_shots_available(game_id, player_id)

    # Get previously fired shots
    shots_fired: dict[str, int] = {}
    if game_id in gameplay_service.fired_shots:
        if player_id in gameplay_service.fired_shots[game_id]:
            for coord, round_num in gameplay_service.fired_shots[game_id][
                player_id
            ].items():
                shots_fired[coord.name] = round_num

    return templates.TemplateResponse(
        request=request,
        name="components/aiming_interface.html",
        context={
            "game_id": game_id,
            "aimed_shots": aimed_shots,
            "shots_fired": shots_fired,
            "shots_available": shots_available,
            "aimed_count": len(aimed_shots),
            "error_message": error_message,
            "waiting_message": waiting_message,
        },
    )


@app.post("/game/{game_id}/fire-shots", response_class=HTMLResponse)
async def fire_shots(request: Request, game_id: str) -> HTMLResponse:
    """Submit aimed shots."""
    player_id = _get_player_id(request)
    _ensure_gameplay_initialized(game_id, player_id)

    result: FireShotsResult = gameplay_service.fire_shots(game_id, player_id)

    if not result.success:
        return _render_aiming_interface(
            request, game_id, player_id, error_message=result.message
        )

    # Check if round is resolved or still waiting
    if result.waiting_for_opponent:
        return _render_aiming_interface(
            request,
            game_id,
            player_id,
            waiting_message="Waiting for opponent to fire...",
        )
    else:
        # Round is resolved - show round results
        round_obj = gameplay_service.active_rounds.get(game_id)
        if round_obj is None or round_obj.result is None:
            return _render_aiming_interface(
                request, game_id, player_id, error_message="Round not found"
            )

        round_result = round_obj.result

        # Get opponent ID
        game = game_service.games.get(game_id)
        if game is None:
            return _render_aiming_interface(
                request, game_id, player_id, error_message="Game not found"
            )

        opponent_id: str
        if game.player_1.id == player_id:
            opponent_id = game.player_2.id if game.player_2 else ""
        else:
            opponent_id = game.player_1.id

        # Calculate hit feedback for display
        my_hits = gameplay_service.calculate_hit_feedback(
            round_result.hits_made.get(player_id, [])
        )
        opponent_hits = gameplay_service.calculate_hit_feedback(
            round_result.hits_made.get(opponent_id, [])
        )

        return templates.TemplateResponse(
            request=request,
            name="components/round_results.html",
            context={
                "round_number": round_result.round_number,
                "my_hits": my_hits,
                "opponent_hits": opponent_hits,
                "game_id": game_id,
            },
        )


@app.get("/game/{game_id}/aiming-interface")
async def get_aiming_interface(request: Request, game_id: str) -> HTMLResponse:
    """Get the aiming interface component for HTMX.

    Args:
        request: The FastAPI request object containing session data
        game_id: The ID of the game

    Returns:
        HTML response with aiming interface component or round results

    Raises:
        HTTPException: 401 if not authenticated, 404 if game not found
    """
    # Get player from session
    player_id: str = _get_player_id(request)

    # Ensure game exists and gameplay is initialized
    _ensure_gameplay_initialized(game_id, player_id)

    # Check if there's an active round and if it's resolved
    round_obj = gameplay_service.active_rounds.get(game_id)

    # If round exists and is resolved, show round results
    if round_obj is not None and round_obj.is_resolved:
        round_result = round_obj.result
        if round_result is None:
            return _render_aiming_interface(
                request, game_id, player_id, error_message="Round not found"
            )

        # Get opponent ID
        game = game_service.games.get(game_id)
        if game is None:
            return _render_aiming_interface(
                request, game_id, player_id, error_message="Game not found"
            )

        opponent_id: str
        if game.player_1.id == player_id:
            opponent_id = game.player_2.id if game.player_2 else ""
        else:
            opponent_id = game.player_1.id

        # Calculate hit feedback for display
        my_hits = gameplay_service.calculate_hit_feedback(
            round_result.hits_made.get(player_id, [])
        )
        opponent_hits = gameplay_service.calculate_hit_feedback(
            round_result.hits_made.get(opponent_id, [])
        )

        return templates.TemplateResponse(
            request=request,
            name="components/round_results.html",
            context={
                "round_number": round_result.round_number,
                "my_hits": my_hits,
                "opponent_hits": opponent_hits,
                "game_id": game_id,
            },
        )

    # Check if player is waiting for opponent
    if round_obj is not None and player_id in round_obj.submitted_players:
        # Player has submitted but round not resolved yet - show waiting message
        return _render_aiming_interface(
            request,
            game_id,
            player_id,
            waiting_message="Waiting for opponent to fire...",
        )

    # Normal aiming interface
    return _render_aiming_interface(request, game_id, player_id)


@app.post("/player-name")
async def validate_player_name(
    request: Request, player_name: str = Form()
) -> HTMLResponse:
    """Validate player name and return partial HTML with validation result"""
    validation: PlayerNameValidation = auth_service.validate_player_name(
        player_name, strip_quotes=False
    )

    return templates.TemplateResponse(
        request=request,
        name="components/player_name_input.html",
        context={
            "player_name": player_name,
            "error_message": validation.error_message,
            "css_class": validation.css_class,
        },
    )


@app.get("/goodbye", response_class=HTMLResponse)
async def goodbye_page(request: Request) -> HTMLResponse:
    """Goodbye page when user exits the game"""
    # TODO: Create a proper template the Goodbye page with a link back to the Welcome page
    return HTMLResponse(content="<html><body><h1>Goodbye</h1></body></html>")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for test infrastructure"""
    # TODO: return game stats e.g. number of games completed, number of games in progress, players in lobby
    return {"status": "healthy"}


# === Lobby Endpoints ===


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request) -> HTMLResponse:
    # Get player from session
    player: Player = _get_player_from_session(request)

    # Default template context
    template_context: dict[str, str] = {
        "player_name": player.name,
    }

    return templates.TemplateResponse(
        request=request,
        name="lobby.html",
        context=template_context,
    )


@app.post("/select-opponent", response_model=None)
async def select_opponent(
    request: Request, opponent_name: str = Form()
) -> HTMLResponse | Response:
    """Handle opponent selection and return updated lobby view"""

    # Get player from session
    player: Player = _get_player_from_session(request)

    try:
        # Look up opponent ID by name
        opponent_id: str | None = lobby_service.get_player_id_by_name(opponent_name)
        if not opponent_id:
            raise ValueError(f"Opponent '{opponent_name}' not found in lobby")

        lobby_service.send_game_request(player.id, opponent_id)

        # Return updated lobby status (same as long poll endpoint)
        return await _render_lobby_status(request, player.id, player.name)

    except ValueError as e:
        # Handle validation errors (player not available, etc.)
        return _create_login_error_response(request, str(e))


@app.post("/leave-lobby", response_model=None)
async def leave_lobby(request: Request) -> RedirectResponse | HTMLResponse | Response:
    """Handle player leaving the lobby"""

    # Get player from session
    player: Player = _get_player_from_session(request)

    try:
        lobby_service.leave_lobby(player.id)
        # TODO: add event here

        if request.headers.get("HX-Request"):
            response: Response = Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={
                    "HX-Redirect": "/login",
                    "HX-Push-Url": "/login",
                },
            )
            return response

        else:
            # Fallback using standard redirect to home/login page on success
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    except ValueError as e:
        # Handle validation errors (empty name, nonexistent player)
        # Return 400 Bad Request for invalid input
        return _create_login_error_response(request, str(e))


@app.get("/lobby/status", response_model=None)
async def lobby_status_component(request: Request) -> HTMLResponse | Response:
    """Return partial HTML with polling for status updates and available for current player"""
    # Get player from session
    player: Player = _get_player_from_session(request)

    return await _render_lobby_status(request, player.id, player.name)


@app.get("/lobby/status/long-poll", response_model=None)
async def lobby_status_long_poll(
    request: Request, timeout: int = 30, version: int | None = None
) -> HTMLResponse | Response:
    """Long polling endpoint for lobby status updates.

    Returns immediately if:
    - This is the first call (version is None)
    - The lobby version has changed since the provided version

    Otherwise waits up to `timeout` seconds for a state change.
    """

    # Get player from session
    player: Player = _get_player_from_session(request)

    # Validate player exists
    try:
        lobby_service.get_player_status(player.id)
    except ValueError:
        return Response(
            content=f"Player '{player.name}' not found in lobby",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Get current lobby version
    current_version = lobby_service.get_lobby_version()

    # If no version provided or version has changed, return immediately
    if version is None or current_version != version:
        # Return current state immediately
        return await _render_lobby_status(request, player.id, player.name)

    # Version matches - wait for changes or timeout
    try:
        # Wait for change event with timeout
        await asyncio.wait_for(
            lobby_service.wait_for_lobby_change(version), timeout=timeout
        )
        # State changed, return new state
        return await _render_lobby_status(request, player.id, player.name)
    except asyncio.TimeoutError:
        # Timeout reached, return current state
        return await _render_lobby_status(request, player.id, player.name)


async def _render_lobby_status(
    request: Request, player_id: str, player_name: str
) -> HTMLResponse | Response:
    """Helper function to render lobby status (shared by both endpoints)

    Args:
        request: The FastAPI request object
        player_id: The ID of the player
        player_name: The name of the player (for display)
    """

    # Get current lobby version for long polling
    lobby_version = lobby_service.get_lobby_version()

    template_context: dict[str, Any] = {
        "player_name": player_name,
        "player_status": "",
        "confirmation_message": "",
        "pending_request": None,
        "decline_confirmation_message": "",
        "available_players": [],
        "error_message": "",
        "lobby_version": lobby_version,
    }

    try:
        # Get current player status
        try:
            player_status: PlayerStatus = lobby_service.get_player_status(player_id)
            template_context["player_status"] = player_status.value

            # If player is IN_GAME, redirect them to game page
            if player_status == PlayerStatus.IN_GAME:
                # Find their opponent from the lobby
                opponent_name: str | None = lobby_service.get_opponent_name(player_id)

                if not opponent_name:
                    # Edge case: player is IN_GAME but no opponent found
                    # This shouldn't happen in normal flow, but handle gracefully
                    template_context["error_message"] = (
                        "Game pairing error - opponent not found"
                    )
                    return templates.TemplateResponse(
                        request=request,
                        name="lobby_status_component.html",
                        context=template_context,
                    )

                game_url: str = "/start-game"

                # Return HTMX redirect
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": game_url},
                )

        except ValueError:
            template_context["player_status"] = f"Unknown player: {player_name}"

        # Check for decline notification (this consumes/clears the notification)
        decliner_name: str | None = lobby_service.get_decline_notification_name(
            player_id
        )
        if decliner_name is not None:
            template_context["decline_confirmation_message"] = (
                f"Game request from {decliner_name} declined"
            )

        # Check for pending game request sent
        pending_request_sent: GameRequest | None = (
            lobby_service.get_pending_request_by_sender(player_id)
        )
        if pending_request_sent is not None:
            receiver_name: str | None = lobby_service.get_player_name(
                pending_request_sent.receiver_id
            )
            template_context["confirmation_message"] = (
                f"Game request sent to {receiver_name}"
            )

        # Check for pending game request
        pending_request: GameRequest | None = (
            lobby_service.get_pending_request_for_player(player_id)
        )

        if pending_request:
            sender_name: str | None = lobby_service.get_player_name(
                pending_request.sender_id
            )
            template_context["pending_request"] = {
                "sender": sender_name or "Unknown",
                "sender_id": pending_request.sender_id,
                "receiver_id": pending_request.receiver_id,
                "timestamp": pending_request.timestamp,
            }
        else:
            template_context["pending_request"] = None

        all_players: list[Player] = lobby_service.get_lobby_players_for_player(
            player_id
        )
        # Filter out IN_GAME players for lobby view
        lobby_data: list[Player] = [
            player for player in all_players if player.status != PlayerStatus.IN_GAME
        ]
        template_context["available_players"] = lobby_data

    except ValueError as e:
        template_context["player_name"] = ""
        template_context["error_message"] = str(e)

    return templates.TemplateResponse(
        request, "components/lobby_dynamic_content.html", template_context
    )


@app.post("/decline-game-request")
async def decline_game_request(
    request: Request,
    show_confirmation: str = Form(default=""),
) -> HTMLResponse:
    """Decline a game request and return to lobby"""

    # Get player from session
    player: Player = _get_player_from_session(request)

    try:
        # Decline the game request
        sender_id: str = lobby_service.decline_game_request(player.id)
        sender_name: str | None = lobby_service.get_player_name(sender_id)
        # TODO: add event here

        # Get updated lobby data
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(player.id)
        player_status: str = lobby_service.get_player_status(player.id).value

        return templates.TemplateResponse(
            request=request,
            name="components/lobby_dynamic_content.html",
            context={
                "player_name": player.name,
                "game_mode": "Two Player",
                "available_players": lobby_data,
                "decline_confirmation_message": f"Game request from {sender_name} declined",
                "player_status": player_status,
            },
        )

    except ValueError as e:
        # Handle validation errors (no pending request, etc.)
        return _create_login_error_response(request, str(e))


@app.post("/accept-game-request", response_model=None)
async def accept_game_request(
    request: Request,
    show_confirmation: str = Form(default=""),
) -> Response | RedirectResponse:
    """Accept a game request and redirect to game page"""

    # Get player from session
    player: Player = _get_player_from_session(request)

    try:
        # Accept the game request
        sender_id: str
        receiver_id: str
        sender_id, receiver_id = lobby_service.accept_game_request(player.id)
        # TODO: add notification event to the requester that their request has been accepted
        # TODO: remove both Player objects from Lobby and add them to GameState

        # Opponent is now stored in lobby state, no need to pass via URL
        redirect_url: str = "/start-game"

        if request.headers.get("HX-Request"):
            response: Response = Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={"HX-Redirect": redirect_url},
            )
            return response
        else:
            # Normal flow: Redirect to game page
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    except ValueError as e:
        # Handle validation errors (no pending request, etc.)
        return _create_login_error_response(request, str(e))


# === Testing Endpoints ===


@app.post("/test/reset-lobby")
async def reset_lobby() -> dict[str, str]:
    """Reset the lobby state for testing"""
    global _game_lobby
    _game_lobby = Lobby()
    # Update service references
    lobby_service.lobby = _game_lobby
    # Clear game service state
    game_service.games = {}
    game_service.games_by_player = {}
    game_service.ship_placement_boards = {}
    # Clear gameplay service state
    gameplay_service.active_rounds = {}
    gameplay_service.player_boards = {}
    gameplay_service.fired_shots = {}
    return {"status": "lobby cleared"}


@app.post("/test/set-gamestate")
async def set_gamestate(
    game_id: str = Form(...),
    player_id: str = Form(...),
    fired_coords: str = Form(...),  # Comma separated
    round_number: int = Form(...),
) -> dict[str, str]:
    """Set game state for testing."""
    if game_id not in gameplay_service.fired_shots:
        gameplay_service.fired_shots[game_id] = {}
    if player_id not in gameplay_service.fired_shots[game_id]:
        gameplay_service.fired_shots[game_id][player_id] = {}

    coords = [c.strip() for c in fired_coords.split(",")]
    for coord_str in coords:
        try:
            coord = Coord[coord_str]
            gameplay_service.fired_shots[game_id][player_id][coord] = round_number
        except KeyError:
            pass

    return {"status": "updated"}


@app.post("/test/add-player-to-lobby")
async def add_player_to_lobby_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Add a player to the lobby bypassing authentication - for testing only"""
    try:
        # Create a player object for testing
        test_player: Player = Player(player_name, PlayerStatus.AVAILABLE)
        lobby_service.join_lobby(test_player)
        return {"status": "player added", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/remove-player-from-lobby")
async def remove_player_from_lobby_for_testing(
    player_name: str = Form(),
) -> dict[str, str]:
    """Remove a player from the lobby bypassing authentication - for testing only"""
    try:
        # Look up player ID by name
        player_id: str | None = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        lobby_service.leave_lobby(player_id)
        return {"status": "player removed", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/send-game-request")
async def send_game_request_for_testing(
    sender_name: str = Form(), target_name: str = Form()
) -> dict[str, str]:
    """Send a game request bypassing session validation - for testing only"""
    try:
        # Look up player IDs by names
        sender_id: str | None = lobby_service.get_player_id_by_name(sender_name)
        target_id: str | None = lobby_service.get_player_id_by_name(target_name)
        if not sender_id:
            raise ValueError(f"Sender '{sender_name}' not found in lobby")
        if not target_id:
            raise ValueError(f"Target '{target_name}' not found in lobby")
        lobby_service.send_game_request(sender_id, target_id)
        return {
            "status": "game request sent",
            "sender": sender_name,
            "target": target_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/accept-game-request")
async def accept_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Accept a game request bypassing session validation - for testing only"""
    try:
        # Look up player ID by name
        player_id: str | None = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        sender_id, receiver_id = lobby_service.accept_game_request(player_id)
        sender_name: str | None = lobby_service.get_player_name(sender_id)
        receiver_name: str | None = lobby_service.get_player_name(receiver_id)
        return {
            "status": "game request accepted",
            "player": receiver_name or receiver_id,
            "sender": sender_name or sender_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/decline-game-request")
async def decline_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Decline a game request bypassing session validation - for testing only"""
    try:
        # Look up player ID by name
        player_id: str | None = lobby_service.get_player_id_by_name(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found in lobby")
        sender_id: str = lobby_service.decline_game_request(player_id)
        sender_name: str | None = lobby_service.get_player_name(sender_id)
        return {
            "status": "game request declined",
            "player": player_name,
            "sender": sender_name or sender_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
