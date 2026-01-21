"""Multiplayer lobby routes."""

import asyncio
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from game.game_service import GameService
from game.player import GameRequest, Player, PlayerStatus
from services.lobby_service import LobbyService

router: APIRouter = APIRouter(prefix="", tags=["lobby"])

# Module-level service references (set during app initialization)
_templates: Jinja2Templates | None = None
_game_service: GameService | None = None
_lobby_service: LobbyService | None = None


def set_up_lobby_router(
    templates: Jinja2Templates,
    game_service: GameService,
    lobby_service: LobbyService,
) -> APIRouter:
    """Configure the lobby router with required dependencies."""
    global _templates, _game_service, _lobby_service
    _templates = templates
    _game_service = game_service
    _lobby_service = lobby_service
    return router


def _get_templates() -> Jinja2Templates:
    """Get templates, raising if not initialized."""
    if _templates is None:
        raise RuntimeError("Router not initialized - call set_up_lobby_router first")
    return _templates


def _get_game_service() -> GameService:
    """Get game_service, raising if not initialized."""
    if _game_service is None:
        raise RuntimeError("Router not initialized - call set_up_lobby_router first")
    return _game_service


def _get_lobby_service() -> LobbyService:
    """Get lobby_service, raising if not initialized."""
    if _lobby_service is None:
        raise RuntimeError("Router not initialized - call set_up_lobby_router first")
    return _lobby_service


def _get_player_id(request: Request) -> str:
    """Get player ID from session."""
    player_id: str | None = request.session.get("player-id")
    if not player_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found - please login",
        )
    return player_id


def _get_player_from_session(request: Request) -> Player:
    """Get Player object from session."""
    player_id: str = _get_player_id(request)
    game_service = _get_game_service()
    player: Player | None = game_service.get_player(player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    return player


def _create_login_error_response(
    request: Request,
    error_message: str,
    player_name: str = "",
    css_class: str = "error",
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTMLResponse:
    """Display the login page with an error message."""
    templates = _get_templates()

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


@router.get("/lobby", response_class=HTMLResponse)
async def lobby_page(request: Request) -> HTMLResponse:
    """Display the multiplayer lobby page"""
    templates = _get_templates()
    player: Player = _get_player_from_session(request)

    template_context: dict[str, str] = {
        "player_name": player.name,
    }

    return templates.TemplateResponse(
        request=request,
        name="lobby.html",
        context=template_context,
    )


@router.post("/select-opponent", response_model=None)
async def select_opponent(
    request: Request, opponent_name: str = Form()
) -> HTMLResponse | Response:
    """Handle opponent selection and return updated lobby view"""
    player: Player = _get_player_from_session(request)
    lobby_service = _get_lobby_service()

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


@router.post("/leave-lobby", response_model=None)
async def leave_lobby(request: Request) -> RedirectResponse | HTMLResponse | Response:
    """Handle player leaving the lobby"""
    player: Player = _get_player_from_session(request)
    lobby_service = _get_lobby_service()

    try:
        lobby_service.leave_lobby(player.id)

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
        return _create_login_error_response(request, str(e))


@router.get("/lobby/status", response_model=None)
async def lobby_status_component(request: Request) -> HTMLResponse | Response:
    """Return partial HTML with polling for status updates and available for current player"""
    player: Player = _get_player_from_session(request)

    return await _render_lobby_status(request, player.id, player.name)


@router.get("/lobby/status/long-poll", response_model=None)
async def lobby_status_long_poll(
    request: Request, timeout: int = 30, version: int | None = None
) -> HTMLResponse | Response:
    """Long polling endpoint for lobby status updates.

    Returns immediately if:
    - This is the first call (version is None)
    - The lobby version has changed since the provided version

    Otherwise waits up to `timeout` seconds for a state change.
    """
    player: Player = _get_player_from_session(request)
    lobby_service = _get_lobby_service()

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
    """Helper function to render lobby status (shared by both endpoints)"""
    templates = _get_templates()
    lobby_service = _get_lobby_service()

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
                    template_context["error_message"] = (
                        "Game pairing error - opponent not found"
                    )
                    return templates.TemplateResponse(
                        request=request,
                        name="components/lobby_dynamic_content.html",
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


@router.post("/decline-game-request")
async def decline_game_request(
    request: Request,
    show_confirmation: str = Form(default=""),
) -> HTMLResponse:
    """Decline a game request and return to lobby"""
    player: Player = _get_player_from_session(request)
    lobby_service = _get_lobby_service()
    templates = _get_templates()

    try:
        # Decline the game request
        sender_id: str = lobby_service.decline_game_request(player.id)
        sender_name: str | None = lobby_service.get_player_name(sender_id)

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


@router.post("/accept-game-request", response_model=None)
async def accept_game_request(
    request: Request,
    show_confirmation: str = Form(default=""),
) -> Response | RedirectResponse:
    """Accept a game request and redirect to game page"""
    player: Player = _get_player_from_session(request)
    lobby_service = _get_lobby_service()

    try:
        # Accept the game request
        sender_id: str
        receiver_id: str
        sender_id, receiver_id = lobby_service.accept_game_request(player.id)

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
