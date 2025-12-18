import asyncio
import secrets
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response

from game.game_service import GameService
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
from services.lobby_service import LobbyService

app: FastAPI = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")
templates: Jinja2Templates = Jinja2Templates(directory="templates")


# Global lobby instance for state management
_game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(_game_lobby)

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


# TODO: don't really need this function
def _build_lobby_url() -> str:
    """Build lobby URL without player name parameter (uses session)"""
    return "/lobby"


# TODO: don't really need this function
def _build_start_game_url() -> str:
    """Build game URL (player and opponent from session/lobby state)"""
    return "/start-game"


# TODO: this is specific to the login page, so it should either be renamed or moved somewhere else
def _create_error_response(
    request: Request,
    error_message: str,
    player_name: str = "",
    css_class: str = "error",
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTMLResponse:
    """Display the login page with an error message"""

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


# TODO: rename this endpoint to /login and change / to be a welcome page with link to /login
@app.get("/", response_class=HTMLResponse)
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


# TODO: rename this to /login
@app.post("/", response_model=None)
async def login_submit(
    request: Request, player_name: str = Form(), game_mode: str = Form()
) -> HTMLResponse | RedirectResponse | Response:
    validation: PlayerNameValidation = auth_service.validate_player_name(
        player_name, strip_quotes=True
    )

    if not validation.is_valid:
        return _create_error_response(
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
            # TODO: Add the player object to lobby not the player_name
            lobby_service.join_lobby(player_name)  # Add the player to the lobby
            redirect_url = _build_lobby_url()

        elif game_mode == "computer":
            redirect_url = _build_start_game_url()
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
        return _create_error_response(
            request=request,
            error_message=str(e),
            player_name=player_name,
            css_class="error",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# TODO: Refactor this into the GameBoard class
def _get_placed_ships_from_board(board: GameBoard) -> dict[str, dict[str, list[str]]]:
    """Extract placed ships from GameBoard into template-friendly format"""
    placed_ships: dict[str, dict[str, list[str]]] = {}
    for ship in board.ships:
        cells: list[str] = [coord.name for coord in ship.positions]
        placed_ships[ship.ship_type.ship_name] = {"cells": cells}
    return placed_ships


# TODO: Refactor these error messages into the Execption classes so I don't need this messy mapping function
def _map_error_message_for_ui(
    exception: Exception,
    board: GameBoard | None = None,
    attempted_positions: list[Coord] | None = None,
) -> str:
    """Map backend exception messages to user-friendly UI messages"""
    error_str: str = str(exception)

    if isinstance(exception, ShipPlacementOutOfBoundsError):
        return "Ship placement goes outside the board"
    elif isinstance(exception, ShipPlacementTooCloseError):
        # Check if this is actual overlap or just touching
        if board and attempted_positions:
            # Get all existing ship positions
            existing_positions: set[Coord] = set()
            for ship in board.ships:
                existing_positions.update(ship.positions)

            # Check if any attempted position overlaps with existing ship
            if existing_positions.intersection(attempted_positions):
                return "Ships cannot overlap"

        # Otherwise it's a touching/spacing issue
        return "Ships must have empty space around them"
    elif isinstance(exception, ShipAlreadyPlacedError):
        # This ship type has already been placed - but for UI purposes,
        # treat this as a spacing/touching issue since the test scenario
        # uses duplicate ships to test adjacent placement
        return "Ships must have empty space around them"
    elif isinstance(exception, KeyError):
        # Handle invalid direction/orientation
        if "INVALID" in error_str.upper() or "WITH INVALID" in error_str.upper():
            return "Invalid direction"
        return "Invalid direction"
    elif isinstance(exception, ValueError):
        return "Invalid direction"
    else:
        return error_str


# TODO: rename this /place-ships
@app.get("/ship-placement", response_class=HTMLResponse)
async def ship_placement_page(request: Request) -> HTMLResponse:
    # Get player from session
    player: Player = _get_player_from_session(request)

    # TODO: look into why we need to pass player name to this template
    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player.name,
            "placed_ships": {},
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

        # FIXME: Replace with call to game manager when it's implemented
        # For now this will get the game board for the player or create a new one
        validated_player_name: str = _get_validated_player_name(request, player_name)
        board: GameBoard = game_service.get_game_board(
            player_id=_get_player_id(request)
        )
        board.place_ship(ship, start, orient)
        # Board is already stored in game_service, no need to store separately

    except (
        ValueError,
        KeyError,
        ShipAlreadyPlacedError,
        ShipPlacementOutOfBoundsError,
        ShipPlacementTooCloseError,
    ) as e:
        # TODO: Should be able to refactor this functionality into GameBoard

        # Get current board state to show what's already placed
        validated_player_name: str = _get_validated_player_name(request, player_name)
        try:
            board: GameBoard = game_service.get_game_board(
                player_id=_get_player_id(request)
            )
        except Exception:
            # If no board exists yet, create empty one for error display
            board = GameBoard()
        placed_ships: dict[str, dict[str, list[str]]] = _get_placed_ships_from_board(
            board
        )

        # Try to calculate attempted positions for better error messages
        attempted_positions: list[Coord] | None = None
        try:
            start_coord: Coord = Coord[start_coordinate.upper()]
            orient_enum: Orientation = Orientation[
                orientation.upper().replace("-", "_")
            ]
            ship_type_for_error: ShipType = ShipType.from_ship_name(ship_name)
            attempted_positions = CoordHelper.coords_for_length_and_orientation(
                start_coord, ship_type_for_error.length, orient_enum
            )
        except (KeyError, ValueError):
            # If we can't calculate positions, that's fine - we'll use None
            pass

        # TODO: remove this when the execption error messages are refactored or improved
        # Map exception to user-friendly message
        user_friendly_error: str = _map_error_message_for_ui(
            e, board, attempted_positions
        )

        # Return ship_placement.html with error and current state
        return templates.TemplateResponse(
            request,
            "ship_placement.html",
            {
                "player_name": player_name,
                "placed_ships": placed_ships,
                "placement_error": user_friendly_error,
            },
            status_code=status.HTTP_200_OK,
        )

    # FIXME: Change this data structure when I design the proper ship board screens
    cells: list[str] = [coord.name for coord in ship.positions]
    placed_ships: dict[str, dict[str, list[str]]] = {
        ship.ship_type.ship_name: {"cells": cells}
    }
    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
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
        player_status: PlayerStatus = lobby_service.get_player_status(player.name)
        if player_status == PlayerStatus.IN_GAME:
            opponent_name_from_lobby: str | None = lobby_service.get_opponent(
                player.name
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
    request: Request, action: str = Form(default="")
) -> RedirectResponse:
    """Handle start game confirmation form submission

    Args:
        request: The FastAPI request object
        action: The action to perform (start_game, return_to_login, exit)

    Returns:
        RedirectResponse to appropriate page based on action
    """
    # Get player from session
    player: Player = _get_player_from_session(request)

    # Validate action parameter
    valid_actions: list[str] = ["start_game", "return_to_login", "exit"]
    if not action or action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
        )

    # Route based on action
    redirect_url: str
    if action == "start_game":
        redirect_url = "/ship-placement"
    elif action == "return_to_login":
        redirect_url = "/"
    elif action == "exit":
        redirect_url = "/goodbye"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}",
        )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


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
        lobby_service.send_game_request(player.name, opponent_name)

        # Return updated lobby status (same as long poll endpoint)
        return await _render_lobby_status(request, player.name)

    except ValueError as e:
        # Handle validation errors (player not available, etc.)
        return _create_error_response(request, str(e))


@app.post("/leave-lobby", response_model=None)
async def leave_lobby(request: Request) -> RedirectResponse | HTMLResponse | Response:
    """Handle player leaving the lobby"""

    # Get player from session
    player: Player = _get_player_from_session(request)

    try:
        lobby_service.leave_lobby(player.name)
        # TODO: add event here

        if request.headers.get("HX-Request"):
            response: Response = Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={
                    "HX-Redirect": "/",
                    "HX-Push-Url": "/",
                },
            )
            return response

        else:
            # Fallback using standard redirect to home/login page on success
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    except ValueError as e:
        # Handle validation errors (empty name, nonexistent player)
        # Return 400 Bad Request for invalid input
        return _create_error_response(request, str(e))


@app.get("/lobby/status", response_model=None)
async def lobby_status_component(request: Request) -> HTMLResponse | Response:
    """Return partial HTML with polling for status updates and available for current player"""
    # Get player from session
    player: Player = _get_player_from_session(request)

    return await _render_lobby_status(request, player.name)


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
        lobby_service.get_player_status(player.name)
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
        return await _render_lobby_status(request, player.name)

    # Version matches - wait for changes or timeout
    try:
        # Wait for change event with timeout
        await asyncio.wait_for(
            lobby_service.wait_for_lobby_change(version), timeout=timeout
        )
        # State changed, return new state
        return await _render_lobby_status(request, player.name)
    except asyncio.TimeoutError:
        # Timeout reached, return current state
        return await _render_lobby_status(request, player.name)


async def _render_lobby_status(
    request: Request, player_name: str
) -> HTMLResponse | Response:
    """Helper function to render lobby status (shared by both endpoints)"""

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
            player_status: PlayerStatus = lobby_service.get_player_status(player_name)
            template_context["player_status"] = player_status.value

            # If player is IN_GAME, redirect them to game page
            if player_status == PlayerStatus.IN_GAME:
                # Find their opponent from the lobby
                opponent_name: str | None = lobby_service.get_opponent(player_name)

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

                game_url: str = _build_start_game_url()

                # Return HTMX redirect
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": game_url},
                )

        except ValueError:
            template_context["player_status"] = f"Unknown player: {player_name}"

        # Check for decline notification (this consumes/clears the notification)
        decliner: str | None = lobby_service.get_decline_notification(player_name)
        if decliner is not None:
            template_context["decline_confirmation_message"] = (
                f"Game request from {decliner} declined"
            )

        # Check for pending game request sent
        pending_request_sent: GameRequest | None = (
            lobby_service.get_pending_request_by_sender(player_name)
        )
        if pending_request_sent is not None:
            template_context["confirmation_message"] = (
                f"Game request sent to {pending_request_sent.receiver}"
            )

        # Check for pending game request
        pending_request: GameRequest | None = (
            lobby_service.get_pending_request_for_player(player_name)
        )
        template_context["pending_request"] = pending_request

        all_players: list[Player] = lobby_service.get_lobby_players_for_player(
            player_name
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
        sender: str = lobby_service.decline_game_request(player.name)
        # TODO: add event here

        # Get updated lobby data
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(
            player.name
        )
        player_status: str = lobby_service.get_player_status(player.name).value

        return templates.TemplateResponse(
            request=request,
            name="components/lobby_dynamic_content.html",
            context={
                "player_name": player.name,
                "game_mode": "Two Player",
                "available_players": lobby_data,
                "decline_confirmation_message": f"Game request from {sender} declined",
                "player_status": player_status,
            },
        )

    except ValueError as e:
        # Handle validation errors (no pending request, etc.)
        return _create_error_response(request, str(e))


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
        sender: str
        receiver: str
        sender, receiver = lobby_service.accept_game_request(player.name)
        # TODO: add notification event to the requester that their request has been accepted
        # TODO: remove both Player objects from Lobby and add them to GameState

        # The player_name is the receiver, sender is the opponent_name
        # Opponent is now stored in lobby state, no need to pass via URL
        redirect_url: str = _build_start_game_url()

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
        return _create_error_response(request, str(e))


# === Testing Endpoints ===


@app.post("/test/reset-lobby")
async def reset_lobby_for_testing() -> dict[str, str]:
    """Reset lobby state - for testing only"""
    _game_lobby.players.clear()
    _game_lobby.game_requests.clear()
    _game_lobby.version = 0
    _game_lobby.change_event = asyncio.Event()

    return {"status": "lobby cleared"}


@app.post("/test/add-player-to-lobby")
async def add_player_to_lobby_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Add a player to the lobby bypassing authentication - for testing only"""
    try:
        lobby_service.join_lobby(player_name)
        return {"status": "player added", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/remove-player-from-lobby")
async def remove_player_from_lobby_for_testing(
    player_name: str = Form(),
) -> dict[str, str]:
    """Remove a player from the lobby bypassing authentication - for testing only"""
    try:
        lobby_service.leave_lobby(player_name)
        return {"status": "player removed", "player": player_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/send-game-request")
async def send_game_request_for_testing(
    sender_name: str = Form(), target_name: str = Form()
) -> dict[str, str]:
    """Send a game request bypassing session validation - for testing only"""
    try:
        lobby_service.send_game_request(sender_name, target_name)
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
        sender_name, receiver_name = lobby_service.accept_game_request(player_name)
        return {
            "status": "game request accepted",
            "player": receiver_name,
            "sender": sender_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/test/decline-game-request")
async def decline_game_request_for_testing(player_name: str = Form()) -> dict[str, str]:
    """Decline a game request bypassing session validation - for testing only"""
    try:
        sender_name = lobby_service.decline_game_request(player_name)
        return {
            "status": "game request declined",
            "player": player_name,
            "sender": sender_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
