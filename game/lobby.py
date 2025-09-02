from game.player import Player, PlayerStatus


class Lobby:
    def __init__(self):
        self.players: dict[str, Player] = {}

    def add_player(self, name: str, status: PlayerStatus) -> None:
        self.players[name] = Player(name, status)

    def remove_player(self, name: str) -> None:
        if name in self.players:
            del self.players[name]
        else:
            raise ValueError(f"Player '{name}' not found in lobby")

    def clear_all_except(self, player_name: str) -> None:
        # Keep only the specified player in the lobby
        if player_name in self.players:
            player = self.players[player_name]
            self.players.clear()
            self.players[player_name] = player
        else:
            self.players.clear()

    def get_available_players(self) -> list[Player]:
        return [
            player
            for player in self.players.values()
            if player.status == PlayerStatus.AVAILABLE
        ]
