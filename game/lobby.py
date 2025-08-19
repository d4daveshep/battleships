from game.player import Player, PlayerStatus


class Lobby:
    def __init__(self):
        self.players: dict[str, Player] = {}

    def add_player(self, name: str, status: PlayerStatus) -> None:
        self.players[name] = Player(name, status)

    def get_available_players(self) -> list[Player]:
        return [
            player
            for player in self.players.values()
            if player.status == PlayerStatus.AVAILABLE
        ]
