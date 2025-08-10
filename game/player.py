from enum import IntEnum
from game.board import GameBoard


class PlayerNum(IntEnum):
    PLAYER_1 = 1
    PLAYER_2 = 2


class Player:
    # def __init__(self, name: str, is_computer: bool = False):
    def __init__(self, name: str):
        self.name: str = name
        # self.is_computer: bool = is_computer
        self.board: GameBoard = GameBoard()
        # self.hits_made: Dict[
        #     ShipType, List[int]
        # ] = {}  # ship_type -> list of round numbers
        # self.opponent_ships_sunk: Set[ShipType] = set()
        #
        # # Initialize hits tracking for all ship types
        # for ship_type in ShipType:
        #     self.hits_made[ship_type] = []

    #
    # def create_fleet(self) -> None:
    #     """Initialize the player's fleet with all required ships"""
    #     for ship_type in ShipType:
    #         ship = Ship(ship_type)
    #         # Note: Ships need to be placed using place_ship method
    #         # This just creates the ship objects
    #
    # def place_ship(self, ship_type: ShipType, start: Coordinate, direction) -> bool:
    #     """Place a ship on the player's board"""
    #     ship = Ship(ship_type)
    #     return self.board.place_ship(ship, start, direction)
    #
    # def fire_shots(
    #     self, targets: List[Coordinate], round_number: int
    # ) -> List[Coordinate]:
    #     """Fire shots at the specified coordinates"""
    #     if len(targets) > self.get_available_shots():
    #         raise ValueError(
    #             f"Cannot fire {len(targets)} shots, only {self.get_available_shots()} available"
    #         )
    #
    #     valid_shots = []
    #     for target in targets:
    #         try:
    #             self.board.fire_shot(target, round_number)
    #             valid_shots.append(target)
    #         except ValueError:
    #             # Shot already fired at this position
    #             continue
    #
    #     return valid_shots
    #
    # def receive_shots(self, shots: List[Coordinate], round_number: int) -> List[Ship]:
    #     """Process shots received from opponent, return list of ships that were hit"""
    #     hit_ships = []
    #     for shot in shots:
    #         hit_ship = self.board.receive_shot(shot, round_number)
    #         if hit_ship:
    #             hit_ships.append(hit_ship)
    #     return hit_ships
    #
    # def record_hits_made(
    #     self, ship_hits: Dict[ShipType, int], round_number: int
    # ) -> None:
    #     """Record hits made on opponent's ships this round"""
    #     for ship_type, hit_count in ship_hits.items():
    #         for _ in range(hit_count):
    #             self.hits_made[ship_type].append(round_number)
    #
    # def record_opponent_ship_sunk(self, ship_type: ShipType) -> None:
    #     """Record that an opponent's ship has been sunk"""
    #     self.opponent_ships_sunk.add(ship_type)
    #
    # def get_available_shots(self) -> int:
    #     """Get number of shots available this round"""
    #     return self.board.get_available_shots()
    #
    # def is_defeated(self) -> bool:
    #     """Check if player has lost (all ships sunk)"""
    #     return self.board.is_all_ships_sunk()
    #
    # def get_fleet_status(self) -> Dict[ShipType, bool]:
    #     """Get status of all ships (sunk/afloat)"""
    #     status = {}
    #     for ship in self.board.ships:
    #         status[ship.ship_type] = ship.is_sunk
    #     return status
    #
    # def get_hits_on_ship_type(self, ship_type: ShipType) -> List[int]:
    #     """Get list of round numbers when hits were made on opponent's ship type"""
    #     return self.hits_made[ship_type].copy()
    #
    # def get_shots_fired_in_round(self, round_number: int) -> List[Coordinate]:
    #     """Get all shots fired in a specific round"""
    #     return [
    #         coord
    #         for coord, round_num in self.board.shots_fired.items()
    #         if round_num == round_number
    #     ]
    #
    # def get_shots_received_in_round(self, round_number: int) -> List[Coordinate]:
    #     """Get all shots received in a specific round"""
    #     return [
    #         coord
    #         for coord, round_num in self.board.shots_received.items()
    #         if round_num == round_number
    #     ]
    #
    # def has_all_ships_placed(self) -> bool:
    #     """Check if player has placed all required ships"""
    #     placed_types = {ship.ship_type for ship in self.board.ships}
    #     required_types = set(ShipType)
    #     return placed_types == required_types
    #
    # def auto_place_ships(self, seed: Optional[int] = None) -> bool:
    #     """Auto-place ships for computer player using random placement"""
    #     if not self.is_computer:
    #         raise ValueError("Can only auto-place ships for computer players")
    #
    #     from .computer_player import ComputerPlayer
    #
    #     computer_logic = ComputerPlayer(self, seed)
    #     return computer_logic.auto_place_ships()
