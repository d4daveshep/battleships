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

