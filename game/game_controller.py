from game import player
from game.player import Player, PlayerNum
from game.ship import ShipLocation


class Game:
    def __init__(self, player_1: Player, player_2: Player):
        self.player_1 = player_1
        self.player_2 = player_2


class GameController:
    @staticmethod
    def create_game(player_1_name: str, player_2_name: str) -> Game:
        player_1: Player = Player(name=player_1_name)
        player_2: Player = Player(name=player_2_name)
        return Game(player_1=player_1, player_2=player_2)

    @staticmethod
    def place_ships(
        game: Game, player_num: PlayerNum, ships: list[ShipLocation]
    ) -> bool:
        return False
