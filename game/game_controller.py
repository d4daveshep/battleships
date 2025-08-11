# from game import player
from game.player import Player, PlayerNum
from game.ship import ShipLocation, ShipType


class Game:
    def __init__(self, player_1: Player, player_2: Player):
        self.player_1 = player_1
        self.player_2 = player_2

    def get_player_by_num(self, player_num: PlayerNum) -> Player:
        if player_num == PlayerNum.PLAYER_1:
            return self.player_1
        elif player_num == PlayerNum.PLAYER_2:
            return self.player_2
        else:
            raise ValueError(f"Invalid player_num: {player_num}")

    @property
    def is_ready_to_start(self) -> bool:
        return self.player_1.all_ships_are_placed and self.player_2.all_ships_are_placed


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
        player: Player = game.get_player_by_num(player_num)
        if len(ships) != len(list(ShipType)):
            raise ValueError(f"Wrong number of ships being placed: {len(ships)}")
        for ship_location in ships:
            if not player.place_ship(
                ship_type=ship_location.ship_type,
                start=ship_location.start_point,
                direction=ship_location.direction,
            ):
                raise ValueError(f"Invalid ship location: {ship_location}")
        return True
