import random
from typing import List, Tuple, Optional
from .models import Coordinate, ShipType, Direction
from .player import Player


class ComputerPlayer:
    """Computer player logic for automated ship placement and shot selection"""
    
    def __init__(self, player: Player, seed: Optional[int] = None):
        self.player = player
        self.random = random.Random(seed) if seed is not None else random.Random()
    
    def auto_place_ships(self, max_attempts: int = 1000) -> bool:
        """Automatically place all ships for a computer player using random placement"""
        if not self.player.is_computer:
            raise ValueError("Can only auto-place ships for computer players")
        
        # Clear any existing ships
        self.player.board.ships.clear()
        
        # Place each ship type
        ship_types = list(ShipType)
        self.random.shuffle(ship_types)  # Random order for placement
        
        for ship_type in ship_types:
            if not self._place_ship_randomly(ship_type, max_attempts):
                # Failed to place this ship, clear board and try again
                self.player.board.ships.clear()
                return False
        
        return True
    
    def _place_ship_randomly(self, ship_type: ShipType, max_attempts: int) -> bool:
        """Attempt to place a single ship randomly on the board"""
        directions = list(Direction)
        
        for _ in range(max_attempts):
            # Random starting position
            start_row = self.random.randint(0, 9)
            start_col = self.random.randint(0, 9)
            start_coord = Coordinate(start_row, start_col)
            
            # Random direction
            direction = self.random.choice(directions)
            
            # Try to place the ship
            if self.player.place_ship(ship_type, start_coord, direction):
                return True
        
        return False
    
    def get_all_possible_positions(self, ship_type: ShipType) -> List[Tuple[Coordinate, Direction]]:
        """Get all valid positions where a ship could be placed (useful for testing)"""
        valid_positions = []
        
        for row in range(10):
            for col in range(10):
                start_coord = Coordinate(row, col)
                for direction in Direction:
                    # Create a temporary ship to test placement
                    from .models import Ship
                    temp_ship = Ship(ship_type)
                    
                    try:
                        # Test if ship can be placed here
                        temp_positions = temp_ship.place_ship(start_coord, direction)
                        
                        # Check if this placement would be valid on the current board
                        if self.player.board._is_valid_placement(temp_positions):
                            valid_positions.append((start_coord, direction))
                    except ValueError:
                        # Position is invalid (out of bounds, etc.)
                        continue
        
        return valid_positions
    
    def auto_place_ships_deterministic(self) -> bool:
        """Place ships in a deterministic pattern (useful for testing)"""
        if not self.player.is_computer:
            raise ValueError("Can only auto-place ships for computer players")
        
        # Clear any existing ships
        self.player.board.ships.clear()
        
        # Deterministic placement pattern
        placements = [
            (ShipType.CARRIER, Coordinate(0, 0), Direction.HORIZONTAL),
            (ShipType.BATTLESHIP, Coordinate(2, 0), Direction.HORIZONTAL),
            (ShipType.CRUISER, Coordinate(4, 0), Direction.HORIZONTAL),
            (ShipType.SUBMARINE, Coordinate(6, 0), Direction.HORIZONTAL),
            (ShipType.DESTROYER, Coordinate(8, 0), Direction.HORIZONTAL),
        ]
        
        for ship_type, coord, direction in placements:
            if not self.player.place_ship(ship_type, coord, direction):
                return False
        
        return True


def create_computer_player(name: str = "Computer", seed: Optional[int] = None) -> Tuple[Player, ComputerPlayer]:
    """Factory function to create a computer player with auto-placement logic"""
    player = Player(name, is_computer=True)
    computer_logic = ComputerPlayer(player, seed)
    return player, computer_logic