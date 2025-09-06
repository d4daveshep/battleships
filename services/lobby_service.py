from game.lobby import Lobby
from game.player import Player, PlayerStatus


class LobbyService:
    def __init__(self, lobby: Lobby):
        self.lobby = lobby
        # self.initialized_scenarios: set[str] = set()

    def join_lobby(self, player_name: str) -> None:
        """Add a player to the lobby - this is the write operation"""

        current_player = player_name.strip()

        if not current_player:
            raise ValueError(f"Player name '{player_name}' is invalid")

        if player_name in self.lobby.players:
            raise ValueError(f"Player name '{player_name}' already exists in lobby")

        self.lobby.add_player(current_player, PlayerStatus.AVAILABLE)

    def get_available_players(self) -> list[Player]:
        return self.lobby.get_available_players()

    def get_lobby_data_for_player(self, player_name: str) -> list[str]:
        # Get lobby data for a specific player - READ-ONLY operation
        current_player = player_name.strip()

        # Handle empty/whitespace names
        if not current_player:
            raise ValueError(f"Player name '{player_name}' is invalid")

        # Get all available players from lobby, excluding current player
        all_players = self.get_available_players()
        available_players = [
            player.name
            for player in all_players
            if (
                player.name != current_player
                and player.status == PlayerStatus.AVAILABLE
            )
        ]

        return available_players

    def get_lobby_players_for_player(self, player_name: str) -> list[Player]:
        # Get all players (with status info) for a specific player - READ-ONLY operation
        current_player = player_name.strip()

        # Handle empty/whitespace names
        if not current_player:
            raise ValueError(f"Player name '{player_name}' is invalid")

        # Get all players from lobby, excluding current player
        all_players = list(self.lobby.players.values())
        other_players = [
            player for player in all_players if player.name != current_player
        ]

        return other_players

    def update_player_status(self, player_name: str, status: PlayerStatus) -> None:
        """Update a player's status in the lobby"""
        self.lobby.update_player_status(player_name, status)

    def get_player_status(self, player_name: str) -> PlayerStatus:
        """Get a player's current status"""
        return self.lobby.get_player_status(player_name)

    def leave_lobby(self, player_name: str) -> None:
        """Remove a player from the lobby"""

        # Step 1: Validate and clean input
        current_player: str = player_name.strip()

        if not current_player:
            raise ValueError("Player name cannot be empty")

        # Step 2: Use existing lobby.remove_player method
        # This will handle:
        # - Checking if player exists (raises ValueError if not)
        # - Removing player from self.lobby.players dict
        self.lobby.remove_player(current_player)
