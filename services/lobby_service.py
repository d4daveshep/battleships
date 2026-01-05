from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus


class LobbyService:
    def __init__(self, lobby: Lobby):
        self.lobby = lobby
        # self.initialized_scenarios: set[str] = set()

    def join_lobby(self, player: Player) -> None:
        """Add a player to the lobby - this is the write operation

        Args:
            player: The Player object to add to the lobby
        """
        if player.id in self.lobby.players:
            raise ValueError(f"Player with ID '{player.id}' already exists in lobby")

        self.lobby.add_player(player)

    def get_available_players(self) -> list[Player]:
        """Get all available players in the lobby

        Returns:
            List of Player objects with AVAILABLE status
        """
        return self.lobby.get_available_players()

    def get_lobby_data_for_player(self, player_id: str) -> list[str]:
        """Get lobby data for a specific player - READ-ONLY operation

        Args:
            player_id: The ID of the player requesting lobby data

        Returns:
            List of player names (for display) of available players
        """
        # Get all available players from lobby, excluding current player
        all_players: list[Player] = self.get_available_players()
        # Check the specified player is actually in the lobby and available
        all_player_ids: set[str] = {player.id for player in all_players}
        if player_id not in all_player_ids:
            raise KeyError(f"Player with id:{player_id} is not available in the Lobby")
        available_players: list[str] = [
            player.name
            for player in all_players
            if (player.id != player_id and player.status == PlayerStatus.AVAILABLE)
        ]

        return available_players

    def get_lobby_players_for_player(self, player_id: str) -> list[Player]:
        """Get lobby players visible to a specific player - READ-ONLY operation

        Args:
            player_id: The ID of the player requesting lobby data

        Returns:
            List of Player objects (excluding the requesting player)
        """
        # Get all players from lobby, excluding current player (include all statuses)
        all_players: list[Player] = list(self.lobby.players.values())
        lobby_players: list[Player] = [
            player for player in all_players if player.id != player_id
        ]

        return lobby_players

    def update_player_status(self, player_id: str, status: PlayerStatus) -> None:
        """Update a player's status in the lobby

        Args:
            player_id: The ID of the player
            status: The new status to set
        """
        self.lobby.update_player_status(player_id, status)

    def get_player_status(self, player_id: str) -> PlayerStatus:
        """Get a player's current status

        Args:
            player_id: The ID of the player

        Returns:
            The player's current status
        """
        return self.lobby.get_player_status(player_id)

    def leave_lobby(self, player_id: str) -> None:
        """Remove a player from the lobby

        Args:
            player_id: The ID of the player leaving the lobby
        """
        # Use existing lobby.remove_player method
        # This will handle:
        # - Checking if player exists (raises ValueError if not)
        # - Removing player from self.lobby.players dict
        self.lobby.remove_player(player_id)

    def send_game_request(self, sender_id: str, receiver_id: str) -> None:
        """Send a game request from sender to receiver

        Args:
            sender_id: The ID of the player sending the request
            receiver_id: The ID of the player receiving the request
        """
        # Use the lobby method to send the request
        self.lobby.send_game_request(sender_id, receiver_id)

    def get_pending_request_for_player(self, player_id: str) -> GameRequest | None:
        """Get any pending game request for the specified player

        Args:
            player_id: The ID of the player to check for pending requests

        Returns:
            The GameRequest if one exists, None otherwise
        """
        # Get the request from the lobby
        return self.lobby.get_pending_request(player_id)

    def get_pending_request_by_sender(self, sender_id: str) -> GameRequest | None:
        """Get any pending game request sent by the specified player

        Args:
            sender_id: The ID of the player who sent the request

        Returns:
            The GameRequest if one exists, None otherwise
        """
        return self.lobby.get_pending_request_by_sender(sender_id)

    def accept_game_request(self, receiver_id: str) -> tuple[str, str]:
        """Accept a game request

        Args:
            receiver_id: The ID of the player accepting the request

        Returns:
            Tuple of (sender_id, receiver_id)
        """
        # Use the lobby method to accept the request
        return self.lobby.accept_game_request(receiver_id)

    def decline_game_request(self, receiver_id: str) -> str:
        """Decline a game request

        Args:
            receiver_id: The ID of the player declining the request

        Returns:
            The sender_id whose request was declined
        """
        # Use the lobby method to decline the request
        return self.lobby.decline_game_request(receiver_id)

    def get_decline_notification(self, player_id: str) -> str | None:
        """Get and clear decline notification for a player

        Args:
            player_id: The ID of the player to get notification for

        Returns:
            The ID of the player who declined, or None if no notification
        """
        return self.lobby.get_decline_notification(player_id)

    def get_lobby_version(self) -> int:
        """Get the current version of the lobby state"""
        return self.lobby.get_version()

    async def wait_for_lobby_change(self, since_version: int) -> None:
        """Wait for lobby state to change from the given version"""
        await self.lobby.wait_for_change(since_version)

    def get_opponent(self, player_id: str) -> str | None:
        """Get the opponent for a player in an active game.

        Args:
            player_id: The ID of the player to get opponent for

        Returns:
            The opponent's ID if the player is in an active game, None otherwise
        """
        # Handle empty IDs
        if not player_id:
            return None

        # Get opponent from lobby
        return self.lobby.get_opponent(player_id)

    # Display helper methods - convert IDs to names for UI

    def get_player_id_by_name(self, player_name: str) -> str | None:
        """Get a player's ID by their display name

        Args:
            player_name: The name of the player to find

        Returns:
            The player's ID if found, None otherwise
        """
        for player in self.lobby.players.values():
            if player.name == player_name:
                return player.id
        return None

    def get_player_name(self, player_id: str) -> str | None:
        """Get a player's display name by their ID

        Args:
            player_id: The ID of the player

        Returns:
            The player's name if found, None otherwise
        """
        player = self.lobby.players.get(player_id)
        return player.name if player else None

    def get_opponent_name(self, player_id: str) -> str | None:
        """Get the opponent's display name for a player in an active game

        Args:
            player_id: The ID of the player to get opponent name for

        Returns:
            The opponent's name if player is in an active game, None otherwise
        """
        opponent_id = self.get_opponent(player_id)
        if not opponent_id:
            return None
        return self.get_player_name(opponent_id)

    def get_pending_request_sender_name(self, player_id: str) -> str | None:
        """Get the sender's display name for a pending game request

        Args:
            player_id: The ID of the player who received the request

        Returns:
            The sender's name if there's a pending request, None otherwise
        """
        request = self.get_pending_request_for_player(player_id)
        if not request:
            return None
        return self.get_player_name(request.sender_id)

    def get_decline_notification_name(self, player_id: str) -> str | None:
        """Get the decliner's display name and clear the notification

        Args:
            player_id: The ID of the player to get notification for

        Returns:
            The name of the player who declined, or None if no notification
        """
        decliner_id = self.get_decline_notification(player_id)
        if not decliner_id:
            return None
        return self.get_player_name(decliner_id)
