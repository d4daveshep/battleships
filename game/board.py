from game.ship import Ship, Coordinate, Direction


class GameBoard:
    def __init__(self):
        self.ships: list[Ship] = []
        self.shots_received: dict[Coordinate, int] = {}  # coord -> round number
        self.shots_fired: dict[Coordinate, int] = {}  # coord -> round number

    # Place a ship on the board if placement is valid
    def place_ship(self, ship: Ship, start: Coordinate, direction: Direction) -> bool:
        try:
            coordinates: set[Coordinate] = ship.place_ship(start, direction)

            if self._is_valid_placement(coordinates):
                self.ships.append(ship)
                return True
            else:
                ship.coordinates = set()  # Reset positions if placement failed
                return False

        except ValueError:
            return False

    # Validate ship placement according to game rules
    def _is_valid_placement(self, coordinates: set[Coordinate]) -> bool:
        # Check if positions are within board bounds (already checked in place_ship)
        for coord in coordinates:
            if not (0 <= coord.row <= 9 and 0 <= coord.col <= 9):
                return False

        # Check for overlaps with existing ships
        occupied_coordinates: set[Coordinate] = self._get_all_occupied_positions()
        for coord in coordinates:
            if coordinates in occupied_coordinates:
                return False

        # Check spacing rule: no ship can be adjacent to another
        forbidden_coordinates = self._get_all_forbidden_positions()
        for coord in coordinates:
            if coord in forbidden_coordinates:
                return False

        return True

    # Get all positions currently occupied by ships"""
    def _get_all_occupied_positions(self) -> set[Coordinate]:
        occupied: set[Coordinate] = set()
        for ship in self.ships:
            occupied.update(ship.coordinates)
        return occupied

    # Get all positions that are forbidden due to spacing rules"""
    def _get_all_forbidden_positions(self) -> set[Coordinate]:
        forbidden: set[Coordinate] = set()
        occupied: set[Coordinate] = self._get_all_occupied_positions()

        for coord in occupied:
            # Add all adjacent positions (8 directions)
            for row_offset in [-1, 0, 1]:
                for col_offset in [-1, 0, 1]:
                    if row_offset == 0 and col_offset == 0:
                        continue  # Skip the position itself

                    adjacent_row = coord.row + row_offset
                    adjacent_col = coord.col + col_offset

                    # Only add if within board bounds
                    if 0 <= adjacent_row <= 9 and 0 <= adjacent_col <= 9:
                        forbidden.add(Coordinate(adjacent_row, adjacent_col))

        # Remove already occupied positions from forbidden set
        return forbidden - occupied

    # def receive_shot(self, coordinate: Coordinate, round_number: int) -> Ship | None:
    #     """Process a shot received at the given coordinate"""
    #     if coordinate in self.shots_received:
    #         raise ValueError(f"Position {coordinate.to_string()} already shot at")
    #
    #     self.shots_received[coordinate] = round_number
    #
    #     # Check if any ship was hit
    #     for ship in self.ships:
    #         if ship.incoming_shot(coordinate):
    #             return ship
    #
    #     return None
    #
    # def fire_shot(self, coordinate: Coordinate, round_number: int) -> None:
    #     """Record a shot fired at the given coordinate"""
    #     if coordinate in self.shots_fired:
    #         raise ValueError(f"Already fired at position {coordinate.to_string()}")
    #
    #     self.shots_fired[coordinate] = round_number
    #
    # def get_ship_at_position(self, coordinate: Coordinate) -> Ship | None:
    #     """Get the ship at the given position, if any"""
    #     for ship in self.ships:
    #         if coordinate in ship.positions:
    #             return ship
    #     return None
    #

    # Calculate total available shots based on unsunk ships
    @property
    def available_shots(self) -> int:
        return sum(ship.guns_available for ship in self.ships)

    # def get_sunk_ships(self) -> list[Ship]:
    #     """Get all ships that have been sunk"""
    #     return [ship for ship in self.ships if ship.is_sunk]
    #
    # def get_unsunk_ships(self) -> list[Ship]:
    #     """Get all ships that are still afloat"""
    #     return [ship for ship in self.ships if not ship.is_sunk]
    #
    # def is_all_ships_sunk(self) -> bool:
    #     """Check if all ships have been sunk"""
    #     return all(ship.is_sunk for ship in self.ships)
    #
    # def get_ship_positions(self) -> dict[ShipType, list[Coordinate]]:
    #     """Get positions of all ships by type"""
    #     positions = {}
    #     for ship in self.ships:
    #         positions[ship.ship_type] = ship.positions.copy()
    #     return positions
