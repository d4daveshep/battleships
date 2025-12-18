import asyncio
from datetime import datetime
from game.player import GameRequest, Player, PlayerStatus


class Lobby:
    def __init__(self):
        self.players: dict[str, Player] = {}  # player_id -> Player
        self.game_requests: dict[str, GameRequest] = {}  # receiver_id -> GameRequest
        self.active_games: dict[str, str] = {}  # player_id -> opponent_id
        self.decline_notifications: dict[str, str] = {}  # sender_id -> decliner_id
        self.version: int = 0
        self.change_event: asyncio.Event = asyncio.Event()

    def _notify_change(self) -> None:
        """Increment version and notify all waiters of state change"""
        self.version += 1
        self.change_event.set()

    def add_player(self, player: Player) -> None:
        """Add a player to the lobby

        Args:
            player: The Player object to add to the lobby
        """
        self.players[player.id] = player
        self._notify_change()

    def remove_player(self, player_id: str) -> None:
        """Remove a player from the lobby

        Args:
            player_id: The ID of the player to remove
        """
        if player_id in self.players:
            del self.players[player_id]
            self._notify_change()
        else:
            raise ValueError(f"Player with ID '{player_id}' not found in lobby")

    def clear_all_except(self, player_id: str) -> None:
        """Keep only the specified player in the lobby

        Args:
            player_id: The ID of the player to keep
        """
        if player_id in self.players:
            player = self.players[player_id]
            self.players.clear()
            self.players[player_id] = player
        else:
            self.players.clear()

    def get_available_players(self) -> list[Player]:
        return [
            player
            for player in self.players.values()
            if player.status == PlayerStatus.AVAILABLE
        ]

    def update_player_status(self, player_id: str, status: PlayerStatus) -> None:
        """Update a player's status in the lobby

        Args:
            player_id: The ID of the player
            status: The new status to set
        """
        if player_id not in self.players:
            raise ValueError(f"Player with ID '{player_id}' not found in lobby")
        self.players[player_id].status = status
        self._notify_change()

    def get_player_status(self, player_id: str) -> PlayerStatus:
        """Get a player's current status

        Args:
            player_id: The ID of the player

        Returns:
            The player's current status
        """
        if player_id not in self.players:
            raise ValueError(f"Player with ID '{player_id}' not found in lobby")
        return self.players[player_id].status

    def send_game_request(self, sender_id: str, receiver_id: str) -> None:
        """Send a game request from sender to receiver

        Args:
            sender_id: The ID of the player sending the request
            receiver_id: The ID of the player receiving the request
        """
        # Validate that both players exist
        if sender_id not in self.players:
            raise ValueError(f"Player with ID '{sender_id}' not found in lobby")
        if receiver_id not in self.players:
            raise ValueError(f"Player with ID '{receiver_id}' not found in lobby")

        # Validate that sender is available
        if self.players[sender_id].status != PlayerStatus.AVAILABLE:
            raise ValueError(f"Sender with ID {sender_id} is not available")

        # Validate that receiver is available
        if self.players[receiver_id].status != PlayerStatus.AVAILABLE:
            raise ValueError(f"Receiver with ID {receiver_id} is not available")

        # Create the game request
        request = GameRequest(
            sender_id=sender_id, receiver_id=receiver_id, timestamp=datetime.now()
        )

        # Store the request
        self.game_requests[receiver_id] = request

        # Update player statuses
        self.players[sender_id].status = PlayerStatus.REQUESTING_GAME
        self.players[receiver_id].status = PlayerStatus.PENDING_RESPONSE
        self._notify_change()

    def get_pending_request(self, receiver_id: str) -> GameRequest | None:
        """Get any pending game request for the specified player

        Args:
            receiver_id: The ID of the player to check for pending requests

        Returns:
            The GameRequest if one exists, None otherwise
        """
        return self.game_requests.get(receiver_id)

    def get_pending_request_by_sender(self, sender_id: str) -> GameRequest | None:
        """Get any pending game request sent by the specified player

        Args:
            sender_id: The ID of the player who sent the request

        Returns:
            The GameRequest if one exists, None otherwise
        """
        for request in self.game_requests.values():
            if request.sender_id == sender_id:
                return request
        return None

    def accept_game_request(self, receiver_id: str) -> tuple[str, str]:
        """Accept a game request

        Args:
            receiver_id: The ID of the player accepting the request

        Returns:
            Tuple of (sender_id, receiver_id)
        """
        # Check if there's a pending request
        if receiver_id not in self.game_requests:
            raise ValueError(
                f"No pending game request for player with ID {receiver_id}"
            )

        request = self.game_requests[receiver_id]
        sender_id = request.sender_id

        # Update both players to IN_GAME
        self.players[sender_id].status = PlayerStatus.IN_GAME
        self.players[receiver_id].status = PlayerStatus.IN_GAME

        # Create bidirectional pairing
        self.active_games[sender_id] = receiver_id
        self.active_games[receiver_id] = sender_id

        # Remove the request
        del self.game_requests[receiver_id]

        self._notify_change()

        return sender_id, receiver_id

    def decline_game_request(self, receiver_id: str) -> str:
        """Decline a game request

        Args:
            receiver_id: The ID of the player declining the request

        Returns:
            The sender_id of the player whose request was declined
        """
        # Check if there's a pending request
        if receiver_id not in self.game_requests:
            raise ValueError(
                f"No pending game request for player with ID {receiver_id}"
            )

        request = self.game_requests[receiver_id]
        sender_id = request.sender_id

        # Return both players to AVAILABLE
        self.players[sender_id].status = PlayerStatus.AVAILABLE
        self.players[receiver_id].status = PlayerStatus.AVAILABLE

        # Store decline notification for sender
        self.decline_notifications[sender_id] = receiver_id

        # Remove the request
        del self.game_requests[receiver_id]

        self._notify_change()

        return sender_id

    def get_opponent(self, player_id: str) -> str | None:
        """Get the opponent for a player in an active game.

        Args:
            player_id: The ID of the player to get opponent for

        Returns:
            The opponent's ID if the player is in an active game, None otherwise
        """
        return self.active_games.get(player_id)

    def get_decline_notification(self, player_id: str) -> str | None:
        """Get and clear decline notification for a player.

        Args:
            player_id: The ID of the player to get notification for

        Returns:
            The ID of the player who declined, or None if no notification
        """
        return self.decline_notifications.pop(player_id, None)

    def get_version(self) -> int:
        """Return the current version of the lobby state"""
        return self.version

    async def wait_for_change(self, since_version: int) -> None:
        """Wait for lobby state to change from the given version.

        Args:
            since_version: The version to wait for changes from

        Returns immediately if the current version is different from since_version.
        Otherwise, waits for the change_event to be set.
        """
        # If version already changed, return immediately
        if self.get_version() != since_version:
            return

        # Clear the event for this wait cycle
        self.change_event.clear()

        # Check version again after clearing (in case it changed)
        if self.get_version() != since_version:
            return

        # Wait for the event to be set
        await self.change_event.wait()
