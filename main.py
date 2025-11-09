import asyncio
from typing import Any

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus
from services.auth_service import AuthService, PlayerNameValidation
from services.lobby_service import LobbyService

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


# Global lobby instance for state management
_game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(_game_lobby)


def _build_lobby_url(player_name: str) -> str:
    """Build lobby URL with player name parameter"""
    return f"/lobby?player_name={player_name.strip()}"


def _build_game_url(player_name: str, opponent_name: str = "") -> str:
    """Build game URL with player name parameter"""
    if not opponent_name:
        return f"/game?player_name={player_name.strip()}"
    else:
        return f"/game?player_name={player_name.strip()}&opponent_name={opponent_name.strip()}"


def _calculate_end_coordinate(start: str, orientation: str, length: int) -> str:
    """Calculate end coordinate based on start, orientation, and ship length"""
    # Parse start coordinate (e.g., "A1" -> row='A', col=1)
    start_row: str = start[0]
    start_col: int = int(start[1:])
    
    if orientation == "horizontal":
        # Same row, increment column
        end_col: int = start_col + length - 1
        return f"{start_row}{end_col}"
    elif orientation == "vertical":
        # Same column, increment row
        end_row_ord: int = ord(start_row) + length - 1
        return f"{chr(end_row_ord)}{start_col}"
    elif orientation == "diagonal-down":
        # Diagonal down-right: increment both row and column
        end_row_ord: int = ord(start_row) + length - 1
        end_col: int = start_col + length - 1
        return f"{chr(end_row_ord)}{end_col}"
    elif orientation == "diagonal-up":
        # Diagonal up-right: decrement row, increment column
        end_row_ord: int = ord(start_row) - length + 1
        end_col: int = start_col + length - 1
        return f"{chr(end_row_ord)}{end_col}"
    else:
        # Invalid orientation, return start as fallback
        return start


def _calculate_ship_cells(start: str, end: str, orientation: str) -> list[str]:
    """Calculate all cells occupied by a ship between start and end coordinates"""
    # Parse coordinates (e.g., "A1" -> row='A', col=1)
    start_row: str = start[0]
    start_col: int = int(start[1:])
    end_row: str = end[0]
    end_col: int = int(end[1:])
    
    cells: list[str] = []
    
    if orientation == "horizontal":
        # Same row, different columns
        row: str = start_row
        for col in range(start_col, end_col + 1):
            cells.append(f"{row}{col}")
    elif orientation == "vertical":
        # Same column, different rows
        col: int = start_col
        start_ord: int = ord(start_row)
        end_ord: int = ord(end_row)
        for row_ord in range(start_ord, end_ord + 1):
            cells.append(f"{chr(row_ord)}{col}")
    elif orientation in ["diagonal-down", "diagonal-up"]:
        # Diagonal: increment/decrement both row and column
        row_ord: int = ord(start_row)
        end_row_ord: int = ord(end_row)
        col: int = start_col
        
        # Determine direction
        row_step: int = 1 if end_row_ord >= row_ord else -1
        col_step: int = 1 if end_col >= start_col else -1
        
        # Generate cells along diagonal
        current_row: int = row_ord
        current_col: int = col
        while True:
            cells.append(f"{chr(current_row)}{current_col}")
            if current_row == end_row_ord and current_col == end_col:
                break
            current_row += row_step
            current_col += col_step
    else:
        # For unknown orientation, just return start and end
        cells = [start, end]
    
    return cells


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
    try:
        redirect_url: str
        if game_mode == "human":
            lobby_service.join_lobby(player_name)  # Add the player to the lobby
            # TODO: add event here
            redirect_url = _build_lobby_url(player_name)

        elif game_mode == "computer":
            redirect_url = f"/ship-placement?player_name={player_name.strip()}"
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


@app.get("/ship-placement", response_class=HTMLResponse)
async def ship_placement_page(
    request: Request, player_name: str = ""
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
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
    # Ship lengths
    ship_lengths: dict[str, int] = {
        "Carrier": 5,
        "Battleship": 4,
        "Cruiser": 3,
        "Submarine": 3,
        "Destroyer": 2,
    }
    
    # Get ship length
    ship_length: int = ship_lengths.get(ship_name, 0)
    
    # Calculate end coordinate based on start, orientation, and ship length
    end_coordinate: str = _calculate_end_coordinate(start_coordinate, orientation, ship_length)
    
    # Calculate which cells the ship occupies
    cells: list[str] = _calculate_ship_cells(start_coordinate, end_coordinate, orientation)
    
    # For now, just accept the placement and return the updated page
    # TODO: Add validation logic
    placed_ships: dict[str, dict[str, Any]] = {
        ship_name: {
            "start": start_coordinate,
            "end": end_coordinate,
            "orientation": orientation,
            "cells": cells,
        }
    }
    
    return templates.TemplateResponse(
        request,
        "ship_placement.html",
        {
            "player_name": player_name,
            "placed_ships": placed_ships,
        },
    )


@app.get("/game", response_class=HTMLResponse)
async def game_page(
    request: Request, player_name: str = "", opponent_name: str = ""
) -> HTMLResponse:
    game_mode: str = "Two Player" if opponent_name else "Single Player"
    return templates.TemplateResponse(
        request,
        "game.html",
        {
            "player_name": player_name,
            "opponent_name": opponent_name,
            "game_mode": game_mode,
        },
    )


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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for test infrastructure"""
    return {"status": "healthy"}


@app.post("/test/reset-lobby")
async def reset_lobby_for_testing() -> dict[str, str]:
    """Reset lobby state - for testing only"""
    _game_lobby.players.clear()
    _game_lobby.game_requests.clear()
    _game_lobby.version = 0
    _game_lobby.change_event = asyncio.Event()

    return {"status": "lobby cleared"}


@app.post("/select-opponent")
async def select_opponent(
    request: Request, player_name: str = Form(), opponent_name: str = Form()
) -> HTMLResponse:
    """Handle opponent selection and return updated lobby view"""

    try:
        lobby_service.send_game_request(player_name, opponent_name)

        # Return updated lobby status (same as long poll endpoint)
        return await _render_lobby_status(request, player_name)

    except ValueError as e:
        # Handle validation errors (player not available, etc.)
        return _create_error_response(request, str(e))


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request, player_name: str = "") -> HTMLResponse:
    # Default template context
    template_context: dict[str, str] = {
        "player_name": player_name,
    }

    return templates.TemplateResponse(
        request=request,
        name="lobby.html",
        context=template_context,
    )


@app.post("/leave-lobby", response_model=None)
async def leave_lobby(
    request: Request, player_name: str = Form()
) -> RedirectResponse | HTMLResponse | Response:
    """Handle player leaving the lobby"""

    try:
        lobby_service.leave_lobby(player_name)
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


@app.get("/lobby/status/{player_name}", response_model=None)
async def lobby_status_component(
    request: Request, player_name: str
) -> HTMLResponse | Response:
    """Return partial HTML with polling for status updates and available for current player"""
    return await _render_lobby_status(request, player_name)


@app.get("/lobby/status/{player_name}/long-poll", response_model=None)
async def lobby_status_long_poll(
    request: Request, player_name: str, timeout: int = 30, version: int | None = None
) -> HTMLResponse | Response:
    """Long polling endpoint for lobby status updates.

    Returns immediately if:
    - This is the first call (version is None)
    - The lobby version has changed since the provided version

    Otherwise waits up to `timeout` seconds for a state change.
    """

    # Validate player exists
    try:
        lobby_service.get_player_status(player_name)
    except ValueError:
        return Response(
            content=f"Player '{player_name}' not found in lobby",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Get current lobby version
    current_version = lobby_service.get_lobby_version()

    # If no version provided or version has changed, return immediately
    if version is None or current_version != version:
        # Return current state immediately
        return await _render_lobby_status(request, player_name)

    # Version matches - wait for changes or timeout
    try:
        # Wait for change event with timeout
        await asyncio.wait_for(
            lobby_service.wait_for_lobby_change(version), timeout=timeout
        )
        # State changed, return new state
        return await _render_lobby_status(request, player_name)
    except asyncio.TimeoutError:
        # Timeout reached, return current state
        return await _render_lobby_status(request, player_name)


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

                game_url: str = _build_game_url(player_name, opponent_name)

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
    player_name: str = Form(),
    show_confirmation: str = Form(default=""),
) -> HTMLResponse:
    """Decline a game request and return to lobby"""

    try:
        # Decline the game request
        sender: str = lobby_service.decline_game_request(player_name)
        # TODO: add event here

        # Get updated lobby data
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(
            player_name
        )
        player_status: str = lobby_service.get_player_status(player_name).value

        return templates.TemplateResponse(
            request=request,
            name="components/lobby_dynamic_content.html",
            context={
                "player_name": player_name,
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
    player_name: str = Form(),
    show_confirmation: str = Form(default=""),
) -> Response | RedirectResponse:
    """Accept a game request and redirect to game page"""

    try:
        # Accept the game request
        sender: str
        receiver: str
        sender, receiver = lobby_service.accept_game_request(player_name)
        # TODO: add event here

        # The player_name is the receiver, sender is the opponent_name
        opponent_name: str = sender
        redirect_url: str = _build_game_url(player_name, opponent_name)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
