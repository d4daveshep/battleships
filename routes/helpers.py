"""Shared helper functions for route modules.

These helpers are duplicated to avoid circular imports and keep routers self-contained.
"""

from fastapi import HTTPException, Request, status
from fastapi.templating import Jinja2Templates

from game.game_service import GameService
from game.player import Player
from services.lobby_service import LobbyService

# Module-level service references (set during app initialisation)
_templates: Jinja2Templates | None = None
_game_service: GameService | None = None
_lobby_service: LobbyService | None = None


def set_up_helpers(
    templates: Jinja2Templates,
    game_service: GameService,
    lobby_service: LobbyService,
) -> None:
    """Configure the helpers module with required dependencies.

    Must be called before any routes are used.
    """
    global _templates, _game_service, _lobby_service
    _templates = templates
    _game_service = game_service
    _lobby_service = lobby_service


def _get_templates() -> Jinja2Templates:
    """Get templates, raising if not initialised."""
    if _templates is None:
        raise RuntimeError("Helpers not initialised - call set_up_helpers first")
    return _templates


def _get_game_service() -> GameService:
    """Get game_service, raising if not initialised."""
    if _game_service is None:
        raise RuntimeError("Helpers not initialised - call set_up_helpers first")
    return _game_service


def _get_lobby_service() -> LobbyService:
    """Get lobby_service, raising if not initialised."""
    if _lobby_service is None:
        raise RuntimeError("Helpers not initialised - call set_up_helpers first")
    return _lobby_service


def _get_player_id(request: Request) -> str:
    """Get player ID from session.

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
    """Get Player object from session.

    Args:
        request: The FastAPI request object containing session data

    Returns:
        The Player object for the session

    Raises:
        HTTPException: 401 if no session, 404 if player not found
    """
    player_id: str = _get_player_id(request)
    game_service = _get_game_service()
    player: Player | None = game_service.get_player(player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    return player


def _get_validated_player_name(request: Request, claimed_name: str) -> str:
    """Verify the session owns this player name.

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


def _is_multiplayer(player_id: str) -> bool:
    """Check if a player is in a multiplayer (two-player) game.

    Args:
        player_id: The player ID to check

    Returns:
        True if player is in a two-player game, False otherwise
    """
    game_service = _get_game_service()
    return game_service.is_multiplayer(player_id)
