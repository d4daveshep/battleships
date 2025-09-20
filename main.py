from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
from typing import AsyncGenerator

from starlette.responses import Response

from game import player
from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus
from services.auth_service import AuthService, PlayerNameValidation
from services.lobby_service import LobbyService

# Constants
ERROR_CSS_CLASS = "error"
LOGIN_TEMPLATE = "login.html"
HOME_URL = "/"

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")


def _build_lobby_url(player_name: str) -> str:
    """Build lobby URL with player name parameter"""
    return f"/lobby?player_name={player_name.strip()}"


def _build_game_url(player_name: str, opponent_name: str = "") -> str:
    """Build game URL with player name parameter"""
    if not opponent_name:
        return f"/game?player_name={player_name.strip()}"
    else:
        return f"/game?player_name={player_name.strip()}&opponent_name={opponent_name.strip()}"


def _create_error_response(
    request: Request,
    error_message: str,
    player_name: str = "",
    css_class: str = ERROR_CSS_CLASS,
    status_code: int = 400,
) -> HTMLResponse:
    """Create standardized error response template"""
    return templates.TemplateResponse(
        request,
        LOGIN_TEMPLATE,
        {
            "error_message": error_message,
            "player_name": player_name,
            "css_class": css_class,
        },
        status_code=status_code,
    )


# Global lobby instance for state management
game_lobby: Lobby = Lobby()

# Service instances
auth_service: AuthService = AuthService()
lobby_service: LobbyService = LobbyService(game_lobby)


# All validation and lobby logic moved to service classes


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        LOGIN_TEMPLATE,
        {"player_name": "", "error_message": "", "css_class": ""},
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
            request,
            validation.error_message,
            "" if validation.error_message else player_name,
            validation.css_class,
            status.HTTP_200_OK,  # Login form errors return 200, not 400
        )

    redirect_url: str
    if game_mode == "human":
        lobby_service.join_lobby(player_name)  # Add the player to the lobby
        # TODO: add event here
        redirect_url = _build_lobby_url(player_name)

    else:
        redirect_url = _build_game_url(player_name)

    if request.headers.get("HX-Request"):
        response = Response(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={"HX-Redirect": redirect_url},
        )
        return response
    else:
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/game", response_class=HTMLResponse)
async def game_page(
    request: Request, player_name: str = "", opponent_name: str = ""
) -> HTMLResponse:
    game_mode = "Two Player" if opponent_name else "Single Player"
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
        request,
        "components/player_name_input.html",
        {
            "player_name": player_name,
            "error_message": validation.error_message,
            "css_class": validation.css_class,
        },
    )


@app.post("/accept-game-request", response_model=None)
async def accept_game_request(
    request: Request,
    player_name: str = Form(),
    show_confirmation: str = Form(default=""),
) -> Response | RedirectResponse:
    """Accept a game request and redirect to game page"""

    try:
        # Accept the game request
        sender, receiver = lobby_service.accept_game_request(player_name)
        # TODO: add event here

        # The player_name is the receiver, sender is the opponent_name
        opponent_name = sender
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


@app.post("/decline-game-request")
async def decline_game_request(
    request: Request,
    player_name: str = Form(),
    show_confirmation: str = Form(default=""),
) -> HTMLResponse:
    """Decline a game request and return to lobby"""

    try:
        # Decline the game request
        sender = lobby_service.decline_game_request(player_name)
        # TODO: add event here

        # Get updated lobby data
        lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(
            player_name
        )
        player_status = lobby_service.get_player_status(player_name).value

        return templates.TemplateResponse(
            request,
            "components/lobby_dynamic_content.html",
            {
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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for test infrastructure"""
    return {"status": "healthy"}


@app.post("/test/reset-lobby")
async def reset_lobby_for_testing() -> dict[str, str]:
    """Reset lobby state - for testing only"""
    game_lobby.players.clear()

    return {"status": "lobby cleared"}


@app.post("/select-opponent")
async def select_opponent(
    request: Request, player_name: str = Form(), opponent_name: str = Form()
) -> HTMLResponse:
    """Handle opponent selection and return updated lobby view"""

    try:
        # Use the new game request system
        lobby_service.send_game_request(player_name, opponent_name)
        # TODO: add event here

        # # Get updated lobby data after status changes
        # lobby_data: list[Player] = lobby_service.get_lobby_players_for_player(
        #     player_name
        # )
        # player_status = lobby_service.get_player_status(player_name).value
        #
        # # Check for pending game request
        # pending_request: GameRequest | None = (
        #     lobby_service.get_pending_request_for_player(player_name)
        # )

        context = {
            "player_name": player_name,
            # "available_players": lobby_data,
            # "confirmation_message": f"Game request sent to {opponent_name}",
            # "player_status": player_status,
            # "pending_request": pending_request,
        }
        print(f"Lobby.html context: {context}")

        # If this is an HTMX request, return just the lobby content div
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="lobby.html",
                context=context,
            )
        else:
            # For non-HTMX requests, return the full lobby page
            return templates.TemplateResponse(
                request=request,
                name="lobby.html",
                context=context,
            )

    except ValueError as e:
        # Handle validation errors (player not available, etc.)
        return _create_error_response(request, str(e))


@app.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request, player_name: str = "") -> HTMLResponse:
    # Default template context
    template_context = {
        "player_name": player_name,
        # "game_mode": "Two Player",
        # "available_players": [],
        # "confirmation_message": "",
        # "player_status": PlayerStatus.AVAILABLE,
        # "pending_request": None,
        # "error_message": "",
    }

    return templates.TemplateResponse(request, "lobby.html", template_context)


@app.post("/leave-lobby", response_model=None)
async def leave_lobby(
    request: Request, player_name: str = Form()
) -> RedirectResponse | HTMLResponse | Response:
    """Handle player leaving the lobby"""

    try:
        # Use the LobbyService.leave_lobby method we just implemented
        lobby_service.leave_lobby(player_name)
        # TODO: add event here

        if request.headers.get("HX-Request"):
            response = Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={
                    "HX-Redirect": HOME_URL,
                    "HX-Push-Url": HOME_URL,
                    # "HX-Replace-Url": HOME_URL,
                },
            )
            return response

        else:
            # Fallback using standard redirect to home/login page on success
            return RedirectResponse(url=HOME_URL, status_code=status.HTTP_302_FOUND)

    except ValueError as e:
        # Handle validation errors (empty name, nonexistent player)
        # Return 400 Bad Request for invalid input
        return _create_error_response(request, str(e))


@app.get("/lobby/status/{player_name}", response_model=None)
async def lobby_status_partial(
    request: Request, player_name: str
) -> HTMLResponse | Response:
    """Return partial HTML with polling for status updates and available for current player"""

    template_context = {
        "player_name": player_name,
        "player_status": "",
        "confirmation_message": "",
        "pending_request": None,
        "decline_confirmation_message": "",
        "available_players": [],
        "error_message": "",
    }

    try:
        # Get current player status
        try:
            player_status: PlayerStatus = lobby_service.get_player_status(player_name)
            template_context["player_status"] = player_status.value

            # If player is IN_GAME, redirect them to game page
            if player_status == PlayerStatus.IN_GAME:
                # Find their opponent from the lobby
                opponent_name: str = "ABC"
                # for player in all_players:
                #     if (
                #         player.name != player_name
                #         and player.status == PlayerStatus.IN_GAME
                #     ):
                #         opponent_name = player.name
                #         break

                game_url = _build_game_url(player_name, opponent_name)

                # Return HTMX redirect
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": game_url},
                )

        except ValueError:
            template_context["player_status"] = f"Unknown player: {player_name}"

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


@app.get("/lobby/players/{player_name}", response_model=None)
async def lobby_players_partial(
    request: Request, player_name: str
) -> HTMLResponse | Response:
    """Return partial HTML with current player list for polling updates"""
    try:
        all_players: list[Player] = lobby_service.get_lobby_players_for_player(
            player_name
        )
        # Filter out IN_GAME players for lobby view
        lobby_data: list[Player] = [
            player for player in all_players if player.status != PlayerStatus.IN_GAME
        ]

        player_status = PlayerStatus.AVAILABLE
        try:
            player_status_enum = lobby_service.get_player_status(player_name)
            player_status = player_status_enum.value

            # If player is IN_GAME, redirect them to game page
            if player_status_enum == PlayerStatus.IN_GAME:
                # Find their opponent from the lobby
                opponent_name: str = ""
                for player in all_players:
                    if (
                        player.name != player_name
                        and player.status == PlayerStatus.IN_GAME
                    ):
                        opponent_name = player.name
                        break

                game_url = _build_game_url(player_name, opponent_name)

                # Return HTMX redirect
                return Response(
                    status_code=status.HTTP_204_NO_CONTENT,
                    headers={"HX-Redirect": game_url},
                )

        except ValueError:
            pass

        # Check for pending game request
        pending_request = lobby_service.get_pending_request_for_player(player_name)

        return templates.TemplateResponse(
            request,
            "components/players_list.html",
            {
                "player_name": player_name,
                "available_players": lobby_data,
                "player_status": player_status,
                # "pending_request": pending_request,
            },
        )
    except ValueError:
        return templates.TemplateResponse(
            request,
            "components/players_list.html",
            {
                "player_name": player_name,
                "available_players": [],
                "player_status": PlayerStatus.AVAILABLE,
            },
        )
