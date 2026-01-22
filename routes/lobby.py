"""Multiplayer lobby routes."""

import asyncio
from typing import Any

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from game.player import GameRequest, Player, PlayerStatus

from routes.helpers import (
    _get_lobby_service,
    _get_player_from_session,
    _get_templates,
)

router: APIRouter = APIRouter(prefix="", tags=["lobby"])


def set_up_lobby_router(
    templates: Jinja2Templates,
    game_service: "GameService",
    lobby_service: "LobbyService",
) -> APIRouter:
    """Configure the lobby router with required dependencies."""
    return router


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

    # Build template context with all lobby state
    context = _build_lobby_context(
        player_id=player_id,
        player_name=player_name,
        lobby_version=lobby_version,
        lobby_service=lobby_service,
    )

    # Check if we need to redirect (player is IN_GAME)
    redirect_url = context.pop("_redirect_url", None)
    if redirect_url:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={"HX-Redirect": redirect_url},
        )

    return templates.TemplateResponse(
        request, "components/lobby_dynamic_content.html", context
    )


def _build_lobby_context(
    player_id: str,
    player_name: str,
    lobby_version: int,
    lobby_service: "LobbyService",
) -> dict[str, Any]:
    """Build template context for lobby status.

    Args:
        player_id: The player ID
        player_name: The player name
        lobby_version: Current lobby version for long polling
        lobby_service: The LobbyService instance

    Returns:
        dict with all template context for lobby display.
        May contain '_redirect_url' key if player should be redirected.
    """
    context: dict[str, Any] = {
        "player_name": player_name,
        "player_status": "",
        "confirmation_message": "",
        "pending_request": None,
        "decline_confirmation_message": "",
        "available_players": [],
        "error_message": "",
        "lobby_version": lobby_version,
    }

    # Check player status and handle IN_GAME redirect
    redirect_url = _check_player_game_status(
        player_id, player_name, lobby_service, context
    )
    if redirect_url:
        context["_redirect_url"] = redirect_url
        return context

    # Get game notifications (decline confirmations, sent request confirmations)
    _add_game_notifications(player_id, lobby_service, context)

    # Get pending game request (incoming)
    _add_pending_request(player_id, lobby_service, context)

    # Get available players
    _add_available_players(player_id, lobby_service, context)

    return context


def _check_player_game_status(
    player_id: str,
    player_name: str,
    lobby_service: "LobbyService",
    context: dict[str, Any],
) -> str | None:
    """Check player status and set up redirect if IN_GAME.

    Args:
        player_id: The player ID
        player_name: The player name
        lobby_service: The LobbyService instance
        context: Template context dict to update

    Returns:
        Redirect URL if player is IN_GAME, None otherwise
    """
    try:
        player_status: PlayerStatus = lobby_service.get_player_status(player_id)
        context["player_status"] = player_status.value

        # If player is IN_GAME, redirect them to game page
        if player_status == PlayerStatus.IN_GAME:
            opponent_name: str | None = lobby_service.get_opponent_name(player_id)

            if not opponent_name:
                # Edge case: player is IN_GAME but no opponent found
                context["error_message"] = "Game pairing error - opponent not found"
                return None

            return "/start-game"

    except ValueError:
        context["player_status"] = f"Unknown player: {player_name}"

    return None


def _add_game_notifications(
    player_id: str,
    lobby_service: "LobbyService",
    context: dict[str, Any],
) -> None:
    """Add game notifications to template context.

    Handles decline confirmations and sent request confirmations.
    """
    # Check for decline notification (this consumes/clears the notification)
    decliner_name: str | None = lobby_service.get_decline_notification_name(player_id)
    if decliner_name is not None:
        context["decline_confirmation_message"] = (
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
        context["confirmation_message"] = f"Game request sent to {receiver_name}"


def _add_pending_request(
    player_id: str,
    lobby_service: "LobbyService",
    context: dict[str, Any],
) -> None:
    """Add pending game request to template context."""
    pending_request: GameRequest | None = lobby_service.get_pending_request_for_player(
        player_id
    )

    if pending_request:
        sender_name: str | None = lobby_service.get_player_name(
            pending_request.sender_id
        )
        context["pending_request"] = {
            "sender": sender_name or "Unknown",
            "sender_id": pending_request.sender_id,
            "receiver_id": pending_request.receiver_id,
            "timestamp": pending_request.timestamp,
        }
    else:
        context["pending_request"] = None


def _add_available_players(
    player_id: str,
    lobby_service: "LobbyService",
    context: dict[str, Any],
) -> None:
    """Add available players list to template context."""
    try:
        all_players: list[Player] = lobby_service.get_lobby_players_for_player(
            player_id
        )
        # Filter out IN_GAME players for lobby view
        lobby_data: list[Player] = [
            player for player in all_players if player.status != PlayerStatus.IN_GAME
        ]
        context["available_players"] = lobby_data
    except ValueError:
        context["available_players"] = []


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


# Forward references for type hints (resolved at runtime)
from routes.helpers import GameService, LobbyService  # noqa: E402
