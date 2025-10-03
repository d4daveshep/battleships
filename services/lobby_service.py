from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus


class LobbyService:
    def __init__(self, lobby: Lobby):
        self.lobby = lobby
        # self.initialized_scenarios: set[str] = set()

    def _validate_and_clean_player_name(
        self,
        player_name: str,
        error_msg_template: str = "Player name '{player_name}' is invalid",
    ) -> str:
        """Validate and sanitize player name input"""
        current_player: str = player_name.strip()
        if not current_player:
            if "{player_name}" in error_msg_template:
                raise ValueError(error_msg_template.format(player_name=player_name))
            else:
                raise ValueError(error_msg_template)
        return current_player

    def join_lobby(self, player_name: str) -> None:
        """Add a player to the lobby - this is the write operation"""

        current_player: str = self._validate_and_clean_player_name(player_name)

        if player_name in self.lobby.players:
            raise ValueError(f"Player name '{player_name}' already exists in lobby")

        self.lobby.add_player(current_player, PlayerStatus.AVAILABLE)

    def get_available_players(self) -> list[Player]:
        return self.lobby.get_available_players()

    def get_lobby_data_for_player(self, player_name: str) -> list[str]:
        """Get lobby data for a specific player - READ-ONLY operation"""
        current_player: str = self._validate_and_clean_player_name(player_name)

        # Get all available players from lobby, excluding current player
        all_players: list[Player] = self.get_available_players()
        available_players: list[str] = [
            player.name
            for player in all_players
            if (
                player.name != current_player
                and player.status == PlayerStatus.AVAILABLE
            )
        ]

        return available_players

    def get_lobby_players_for_player(self, player_name: str) -> list[Player]:
        """Get lobby players visible to a specific player - READ-ONLY operation"""
        current_player: str = self._validate_and_clean_player_name(player_name)

        # Get all players from lobby, excluding current player (include all statuses)
        all_players: list[Player] = list(self.lobby.players.values())
        lobby_players: list[Player] = [
            player for player in all_players if player.name != current_player
        ]

        return lobby_players

    def update_player_status(self, player_name: str, status: PlayerStatus) -> None:
        """Update a player's status in the lobby"""
        self.lobby.update_player_status(player_name, status)

    def get_player_status(self, player_name: str) -> PlayerStatus:
        """Get a player's current status"""
        return self.lobby.get_player_status(player_name)

    def leave_lobby(self, player_name: str) -> None:
        """Remove a player from the lobby"""

        # Step 1: Validate and clean input
        current_player: str = self._validate_and_clean_player_name(
            player_name, "Player name cannot be empty"
        )

        # Step 2: Use existing lobby.remove_player method
        # This will handle:
        # - Checking if player exists (raises ValueError if not)
        # - Removing player from self.lobby.players dict
        self.lobby.remove_player(current_player)

    def send_game_request(self, sender: str, receiver: str) -> None:
        """Send a game request from sender to receiver"""
        # Validate player names
        sender_clean = self._validate_and_clean_player_name(sender)
        receiver_clean = self._validate_and_clean_player_name(receiver)

        # Use the lobby method to send the request
        self.lobby.send_game_request(sender_clean, receiver_clean)

    def get_pending_request_for_player(self, player_name: str) -> GameRequest | None:
        """Get any pending game request for the specified player"""
        # Validate player name
        clean_name = self._validate_and_clean_player_name(player_name)

        # Get the request from the lobby
        return self.lobby.get_pending_request(clean_name)

    def get_pending_request_by_sender(self, sender_name: str) -> GameRequest | None:
        """Get any pending game request sent by the specified player"""
        clean_name = self._validate_and_clean_player_name(sender_name)
        return self.lobby.get_pending_request_by_sender(clean_name)

    def accept_game_request(self, receiver: str) -> tuple[str, str]:
        """Accept a game request"""
        # Validate player name
        receiver_clean = self._validate_and_clean_player_name(receiver)

        # Use the lobby method to accept the request
        return self.lobby.accept_game_request(receiver_clean)

    def decline_game_request(self, receiver: str) -> str:
        """Decline a game request"""
        # Validate player name
        receiver_clean = self._validate_and_clean_player_name(receiver)

        # Use the lobby method to decline the request
        return self.lobby.decline_game_request(receiver_clean)

    def get_lobby_version(self) -> int:
        """Get the current version of the lobby state"""
        return self.lobby.get_version()

    async def wait_for_lobby_change(self, since_version: int) -> None:
        """Wait for lobby state to change from the given version"""
        await self.lobby.wait_for_change(since_version)
