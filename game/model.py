import secrets
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, NamedTuple

from game.exceptions import (
    ShipAlreadyPlacedError,
    ShipPlacementOutOfBoundsError,
    ShipPlacementTooCloseError,
    ShotLimitExceededError,
    ActionAfterFireError,
    NoShotsAimedError,
)

if TYPE_CHECKING:
    from game.player import Player

# Re-export exceptions for backwards compatibility
__all__ = [
    "ShipAlreadyPlacedError",
    "ShipPlacementOutOfBoundsError",
    "ShipPlacementTooCloseError",
    "ShotInfo",
    "ShipHitData",
    "Orientation",
    "ShipType",
    "CoordDetails",
    "Coord",
    "CoordHelper",
    "Ship",
    "GameBoard",
    "GameBoardHelper",
    "GameMode",
    "GameStatus",
    "Game",
]


class ShotInfo(NamedTuple):
    """Information about a shot fired or received.

    Attributes:
        round_number: The round number when the shot was fired/received
        is_hit: Whether the shot hit a ship (True) or missed (False)
        ship_type: The type of ship that was hit (None if miss)
    """

    round_number: int
    is_hit: bool
    ship_type: "ShipType | None"


class ShipHitData(NamedTuple):
    """Hit tracking data for a single ship type.

    Attributes:
        hits: List of (coord_name, round_number) tuples for each hit
        is_sunk: Whether all positions of the ship have been hit
    """

    hits: list[tuple[str, int]]
    is_sunk: bool


class Orientation(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL_UP = "diagonal up"
    DIAGONAL_DOWN = "diagonal down"


class ShipType(Enum):
    CARRIER = ("Carrier", 5, 2, "A")
    BATTLESHIP = ("Battleship", 4, 1, "B")
    CRUISER = ("Cruiser", 3, 1, "C")
    SUBMARINE = ("Submarine", 3, 1, "S")
    DESTROYER = ("Destroyer", 2, 1, "D")

    def __init__(self, ship_name: str, length: int, shots_available: int, code: str):
        self.ship_name = ship_name
        self.length = length
        self.shots_available = shots_available
        self.code = code

    @classmethod
    def from_ship_name(cls, ship_name: str) -> "ShipType":
        for ship_type in cls:
            if ship_type.ship_name == ship_name:
                return ship_type
        raise ValueError(f"No ShipType with ship_name: {ship_name}")


class CoordDetails(NamedTuple):
    row_index: int
    col_index: int


_coords: dict[str, CoordDetails] = {
    f"{letter}{number}": CoordDetails(ord(letter) - 64, number)
    for letter in "ABCDEFGHIJ"
    for number in range(1, 11)
}

Coord = Enum("Coord", _coords)


class CoordHelper:
    _coords_by_value: dict[CoordDetails, Coord] = {
        coord.value: coord for coord in Coord
    }

    @classmethod
    def lookup(cls, row_col_index: CoordDetails) -> Coord:
        return cls._coords_by_value[row_col_index]

    @classmethod
    def coords_for_length_and_orientation(
        cls, start: Coord, length: int, orientation: Orientation
    ) -> list[Coord]:
        coords: list[Coord] = [start]

        if orientation == Orientation.HORIZONTAL:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(start.value.row_index, start.value.col_index + i)
                    )
                )
        elif orientation == Orientation.VERTICAL:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(start.value.row_index + i, start.value.col_index)
                    )
                )
        elif orientation == Orientation.DIAGONAL_DOWN:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(
                            start.value.row_index + i, start.value.col_index + i
                        )
                    )
                )

        elif orientation == Orientation.DIAGONAL_UP:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(
                            start.value.row_index - i, start.value.col_index + i
                        )
                    )
                )
        else:
            raise ValueError(f"Invalid orientation: {orientation}")

        return coords

    @classmethod
    def coords_adjacent_to_a_coord(cls, centre: Coord) -> set[Coord]:
        adjacent_coords: set[Coord] = set()
        for row_delta in [-1, 0, 1]:
            for col_delta in [-1, 0, 1]:
                if row_delta == 0 and col_delta == 0:
                    continue
                try:
                    adjacent_coord: Coord = cls.lookup(
                        CoordDetails(
                            centre.value.row_index + row_delta,
                            centre.value.col_index + col_delta,
                        )
                    )
                    adjacent_coords.add(adjacent_coord)
                except KeyError:
                    pass  # skip any coords that are out of bounds
        return adjacent_coords

    @classmethod
    def coords_adjacent_to_a_coords_list(cls, coords: list[Coord]) -> set[Coord]:
        adjacent_coords: set[Coord] = set()
        for coord in coords:
            adjacent_coords.update(cls.coords_adjacent_to_a_coord(coord))
        adjacent_coords = adjacent_coords - set(coords)
        return adjacent_coords


@dataclass
class Ship:
    ship_type: ShipType
    positions: list[Coord] = field(default_factory=list)
    hits: set[Coord] = field(default_factory=set)

    @property
    def length(self) -> int:
        return self.ship_type.length

    @property
    def shots_available(self) -> int:
        return self.ship_type.shots_available

    def register_hit(self, coord: Coord) -> bool:
        """Register a hit on this ship at the given coordinate.

        Args:
            coord: The coordinate that was hit

        Returns:
            True if the hit was registered (coord is part of ship), False otherwise
        """
        if coord in self.positions:
            self.hits.add(coord)
            return True
        return False

    @property
    def is_sunk(self) -> bool:
        """Check if this ship is sunk (all positions have been hit).

        Returns:
            True if all positions have been hit, False otherwise
        """
        return len(self.positions) > 0 and len(self.hits) == len(self.positions)


class GameBoard:
    """
    Model class representing a players game board. The game board records:
    - where the player has placed their ships
    - the shots received (i.e. fired at them by their opponent)
    - the shops they've fired at their opponent

    Main functionality of the game board includes:
    - placing ships
    - locating ships by coords
    """

    def __init__(self) -> None:
        self.ships: list[Ship] = []
        self.shots_received: dict[Coord, ShotInfo] = {}
        self.shots_fired: dict[Coord, ShotInfo] = {}

    def receive_shots(self, shots: set[Coord], round_number: int) -> None:
        """Record received shots with round tracking and hit detection.

        Args:
            shots: Set of coordinates being shot at
            round_number: The current round number
        """
        for shot in shots:
            # Get the ship at this coordinate (if any)
            ship: Ship | None = self.get_ship_at(shot)
            is_hit: bool = ship is not None
            ship_type: ShipType | None = ship.ship_type if ship else None

            # If hit, register the hit on the ship
            if ship:
                ship.register_hit(shot)

            # Store shot info
            self.shots_received[shot] = ShotInfo(
                round_number=round_number,
                is_hit=is_hit,
                ship_type=ship_type,
            )

    def record_fired_shots(self, shots: set[Coord], round_number: int) -> None:
        """Record shots fired at opponent with round tracking.

        Args:
            shots: Set of coordinates being shot at
            round_number: The current round number

        Note:
            Hit detection for fired shots happens on the opponent's board.
            We store is_hit=False and ship_type=None as placeholders.
        """
        for shot in shots:
            self.shots_fired[shot] = ShotInfo(
                round_number=round_number,
                is_hit=False,  # Placeholder - hit status determined on opponent board
                ship_type=None,
            )

    def get_ship_at(self, coord: Coord) -> Ship | None:
        """Get the ship at a coordinate, or None if empty.

        Args:
            coord: The coordinate to check

        Returns:
            Ship at the coordinate, or None if no ship there
        """
        for ship in self.ships:
            if coord in ship.positions:
                return ship
        return None

    def has_ship_at(self, coord: Coord) -> bool:
        """Check if a coordinate contains a ship (would be a hit if shot).

        Args:
            coord: The coordinate to check

        Returns:
            True if the coordinate has a ship, False otherwise
        """
        return self.get_ship_at(coord) is not None

    def get_shots_received_by_round(self, round_number: int) -> set[Coord]:
        """Get all shots received in a specific round.

        Args:
            round_number: The round number to query

        Returns:
            Set of coordinates shot at in that round
        """
        return {
            coord
            for coord, shot_info in self.shots_received.items()
            if shot_info.round_number == round_number
        }

    def get_shots_fired_by_round(self, round_number: int) -> set[Coord]:
        """Get all shots fired in a specific round.

        Args:
            round_number: The round number to query

        Returns:
            Set of coordinates fired at in that round
        """
        return {
            coord
            for coord, shot_info in self.shots_fired.items()
            if shot_info.round_number == round_number
        }

    def get_hits_made(self, opponent_board: "GameBoard") -> dict[str, ShipHitData]:
        """Get hit tracking data for opponent's ships.

        Cross-references this board's shots_fired with opponent's ships to determine
        which opponent ships have been hit and when.

        Args:
            opponent_board: The opponent's game board with their ships

        Returns:
            Dictionary mapping ship names to ShipHitData:
            {
                "Destroyer": ShipHitData(hits=[("A1", 1), ("A2", 3)], is_sunk=True),
                "Carrier": ShipHitData(hits=[("C1", 2)], is_sunk=False),
                ...
            }
            Where hits are list of (coord_name, round_number) tuples.
        """
        # Initialize result with all 5 ship types
        hits_by_ship: dict[str, list[tuple[str, int]]] = {}
        for ship_type in ShipType:
            hits_by_ship[ship_type.ship_name] = []

        # Cross-reference fired shots with opponent's ships
        for coord, shot_info in self.shots_fired.items():
            # Check if this shot hit an opponent ship
            ship_type: ShipType | None = opponent_board.ship_type_at(coord)
            if ship_type:
                # Add this hit to the ship's hit list with round number
                hits_by_ship[ship_type.ship_name].append(
                    (coord.name, shot_info.round_number)
                )

        # Build final result with ShipHitData
        hits_made: dict[str, ShipHitData] = {}
        for ship_type in ShipType:
            ship_name: str = ship_type.ship_name
            # Check if ship is sunk on opponent's board
            is_sunk: bool = False
            for ship in opponent_board.ships:
                if ship.ship_type == ship_type and ship.is_sunk:
                    is_sunk = True
                    break

            hits_made[ship_name] = ShipHitData(
                hits=hits_by_ship[ship_name], is_sunk=is_sunk
            )

        return hits_made

    def _invalid_coords(self) -> set[Coord]:
        invalid_coords: set[Coord] = set()
        for ship in self.ships:
            invalid_coords.update(
                CoordHelper.coords_adjacent_to_a_coords_list(ship.positions)
            )
            invalid_coords.update(ship.positions)
        return invalid_coords

    def place_ship(self, ship: Ship, start: Coord, orientation: Orientation) -> bool:
        """Place a ship on the board with spacing validation.

        Validates that the ship type hasn't been placed yet, fits within board boundaries,
        and maintains required spacing (no touching or overlapping with other ships).

        Raises ValueError if placement is invalid (duplicate type, out of bounds, or too close to another ship).
        """
        ship_types_already_on_board: set[ShipType] = {
            ship.ship_type for ship in self.ships
        }

        if ship.ship_type not in ship_types_already_on_board:
            # get all invalid positions
            all_invalid_coords: set[Coord] = self._invalid_coords()

            # get planned ship positions
            try:
                positions: list[Coord] = CoordHelper.coords_for_length_and_orientation(
                    start, ship.length, orientation
                )

            except KeyError:
                raise ShipPlacementOutOfBoundsError(
                    f"Ship placement out of bounds: {ship.ship_type.name} {orientation.name} at {start.name}"
                )

            # check ship positions don't include an invalid position
            invalid_ship_positions: set[Coord] = set(positions).intersection(
                all_invalid_coords
            )
            if len(invalid_ship_positions) > 0:
                # Check if this is actual overlap or just touching
                existing_positions: set[Coord] = set()
                for existing_ship in self.ships:
                    existing_positions.update(existing_ship.positions)

                is_overlap: bool = bool(existing_positions.intersection(positions))

                raise ShipPlacementTooCloseError(
                    f"Ship placement is too close to another ship: {ship.ship_type.name} {orientation.name} at {start.name}",
                    is_overlap=is_overlap,
                )

            self.ships.append(ship)
            # add positions to ship
            ship.positions = positions

        else:
            raise ShipAlreadyPlacedError(
                f"Ship type: {ship.ship_type.name} already placed on board"
            )

        return True

    def remove_ship(self, ship_type: ShipType) -> bool:
        """Remove a ship from the board by ship type.

        Args:
            ship_type: The type of ship to remove

        Returns:
            True if ship was removed, False if ship wasn't on the board
        """
        for i, ship in enumerate(self.ships):
            if ship.ship_type == ship_type:
                self.ships.pop(i)
                return True
        return False

    def clear_all_ships(self) -> None:
        """Remove all ships from the board."""
        self.ships.clear()

    def ship_type_at(self, coord: Coord) -> ShipType | None:
        # TODO: Reimplement this using a cached map of Coords to Ship.code
        for ship in self.ships:
            if coord in ship.positions:
                return ship.ship_type
        return None

    def get_placed_ships_for_display(self) -> dict[str, dict[str, Any]]:
        """Get placed ships in template-friendly format

        Returns:
            Dictionary mapping ship names to their display data:
            {
                "Carrier": {"cells": ["A1", "A2", ...], "code": "A"},
                "Battleship": {"cells": ["B1", "B2", ...], "code": "B"},
                ...
            }
        """
        placed_ships: dict[str, dict[str, Any]] = {}
        for ship in self.ships:
            cells: list[str] = [coord.name for coord in ship.positions]
            placed_ships[ship.ship_type.ship_name] = {
                "cells": cells,
                "code": ship.ship_type.code,
            }
        return placed_ships


class GameBoardHelper:
    @classmethod
    def print(cls, board: GameBoard, show_invalid: bool = False) -> list[str]:
        """Generate ASCII visualization of game board with ships and optionally invalid placement zones.

        Returns list of strings representing board rows with ship codes (A/B/C/S/D), empty cells (.),
        and optionally invalid placement zones (x) if show_invalid=True.
        """
        ship_coords: dict[Coord, ShipType] = {
            coord: ship.ship_type for ship in board.ships for coord in ship.positions
        }
        invalid_coords: set[Coord] = board._invalid_coords() if show_invalid else set()

        output: list[str] = []
        output.append("  1 2 3 4 5 6 7 8 9 10")
        output.append("-|--------------------")
        for row_index, row_letter in enumerate("ABCDEFGHIJ", start=1):
            row_output: str = f"{row_letter}|"
            for col_index in range(1, 11):
                coord: Coord = CoordHelper.lookup(CoordDetails(row_index, col_index))
                ship_type: ShipType | None = ship_coords.get(coord)
                if ship_type:
                    row_output += ship_type.code + " "
                elif show_invalid and coord in invalid_coords:
                    row_output += "x "
                else:
                    row_output += ". "

            output.append(row_output)
        return output


class GameMode(StrEnum):
    """Game mode enumeration for distinguishing single vs multiplayer games."""

    SINGLE_PLAYER = "single Player"
    TWO_PLAYER = "two Player"


class GameStatus(StrEnum):
    """Game status enumeration for tracking game lifecycle stages."""

    CREATED = "created"
    SETUP = "setup"
    PLAYING = "playing"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class Game:
    """Game state management for tracking game sessions.

    Manages the lifecycle of a battleships game, including player assignments,
    game mode, status tracking, and individual player boards.
    """

    def __init__(
        self, player_1: "Player", game_mode: GameMode, player_2: "Player | None" = None
    ) -> None:
        self.player_1: "Player" = player_1
        self.game_mode: GameMode = game_mode
        self.player_2: "Player | None" = player_2
        self._id: str = self._generate_id()
        self.status: GameStatus = GameStatus.CREATED
        self.round: int = 1
        self.aimed_shots: dict[str, set[Coord]] = {}
        self.fired_shots: dict[str, set[Coord]] = {}
        self._waiting_for_opponent: dict[str, bool] = {}

        # Validate that two player games have an opponent
        if self.game_mode == GameMode.TWO_PLAYER and not self.player_2:
            raise ValueError("Two player games must have two players")

        # Validate that single player games don't have an opponent
        if self.game_mode == GameMode.SINGLE_PLAYER and self.player_2:
            raise ValueError("Single player games cannot have two players")

        # Create game boards
        self.board: dict["Player", GameBoard] = {}
        self.board[self.player_1] = GameBoard()
        if self.player_2:
            self.board[self.player_2] = GameBoard()

    @property
    def id(self) -> str:
        """Read-only game ID that is automatically generated at creation."""
        return self._id

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique game ID using a cryptographically secure random token.

        Returns:
            A URL-safe random token string (always 22 characters, from 16 random bytes)
        """
        return secrets.token_urlsafe(16)

    def _get_player_by_id(self, player_id: str) -> "Player":
        """Get player by ID or raise ValueError."""
        if self.player_1.id == player_id:
            return self.player_1
        if self.player_2 and self.player_2.id == player_id:
            return self.player_2
        raise ValueError(f"Player with ID {player_id} not found in this game")

    def get_shots_available(self, player_id: str) -> int:
        player = self._get_player_by_id(player_id)
        return sum(ship.shots_available for ship in self.board[player].ships)

    def aim_at(self, player_id: str, coord: Coord) -> None:
        """Add a coordinate to the player's aimed shots for this round."""
        if not self.can_aim(player_id):
            raise ActionAfterFireError("Cannot aim shots after firing")

        if player_id not in self.aimed_shots:
            self.aimed_shots[player_id] = set()

        # Check if already aimed at this coordinate (no validation needed)
        if coord in self.aimed_shots[player_id]:
            return

        # Validate we haven't exceeded available shots
        shots_available: int = self.get_shots_available(player_id)
        current_aimed: int = self.get_aimed_shots_count(player_id)
        if current_aimed >= shots_available:
            raise ShotLimitExceededError("Cannot aim more shots than available")

        self.aimed_shots[player_id].add(coord)

    def get_aimed_shots(self, player_id: str) -> set[Coord]:
        """Get the set of coordinates the player has aimed at this round."""
        return self.aimed_shots.get(player_id, set())

    def unaim_at(self, player_id: str, coord: Coord) -> None:
        """Remove a coordinate from the player's aimed shots."""
        if player_id in self.aimed_shots:
            self.aimed_shots[player_id].discard(coord)

    def get_aimed_shots_count(self, player_id: str) -> int:
        """Get the number of coordinates the player has aimed at this round."""
        return len(self.get_aimed_shots(player_id))

    def get_shot_counter_display(self, player_id: str) -> str:
        """Get formatted shot counter display for a player."""
        aimed = self.get_aimed_shots_count(player_id)
        available = self.get_shots_available(player_id)
        return f"Shots Aimed: {aimed}/{available}"

    def is_coordinate_selectable(self, player_id: str, coord: Coord) -> bool:
        """Check if a coordinate can be selected for aiming.

        Args:
            player_id: The player ID
            coord: The coordinate to check

        Returns:
            True if coordinate can be selected, False if already aimed or no shots available
        """
        # Check if already aimed at this coordinate
        if coord in self.get_aimed_shots(player_id):
            return False

        # Check if player has shots available
        shots_available = self.get_shots_available(player_id)
        aimed_count = self.get_aimed_shots_count(player_id)

        return aimed_count < shots_available

    def fire_shots(self, player_id: str) -> None:
        """Submit the player's aimed shots and enter waiting state.

        Args:
            player_id: The ID of the player firing shots

        Raises:
            NoShotsAimedError: If player has no shots aimed
            ActionAfterFireError: If player has already fired and is waiting for opponent
        """
        if self._waiting_for_opponent.get(player_id, False):
            raise ActionAfterFireError("Cannot aim shots after firing")

        aimed = self.get_aimed_shots(player_id)

        if len(aimed) == 0:
            raise NoShotsAimedError("Cannot fire shots - no shots aimed")

        if player_id not in self.fired_shots:
            self.fired_shots[player_id] = set()

        self.fired_shots[player_id].update(aimed)
        self.aimed_shots[player_id] = set()
        self._waiting_for_opponent[player_id] = True

        if self.game_mode == GameMode.TWO_PLAYER and len(self.fired_shots) == 2:
            self._resolve_round()

    def _resolve_round(self) -> None:
        """Process shots for both players and advance the round."""
        if not self.player_2:
            return

        # Apply shots to boards (use current round number before incrementing)
        p1_shots = self.get_fired_shots(self.player_1.id)
        self.board[self.player_2].receive_shots(p1_shots, self.round)
        self.board[self.player_1].record_fired_shots(p1_shots, self.round)

        p2_shots = self.get_fired_shots(self.player_2.id)
        self.board[self.player_1].receive_shots(p2_shots, self.round)
        self.board[self.player_2].record_fired_shots(p2_shots, self.round)

        # Clear pending shots and waiting status
        self.fired_shots = {}
        self._waiting_for_opponent = {}

        # Increment round
        self.round += 1

    def get_fired_shots(self, player_id: str) -> set[Coord]:
        """Get the set of coordinates the player has fired this round.

        Args:
            player_id: The ID of the player

        Returns:
            Set of fired coordinates
        """
        return self.fired_shots.get(player_id, set())

    def is_waiting_for_opponent(self, player_id: str) -> bool:
        """Check if player is waiting for opponent to fire.

        Args:
            player_id: The ID of the player

        Returns:
            True if player has fired and is waiting for opponent
        """
        return self._waiting_for_opponent.get(player_id, False)

    def can_aim(self, player_id: str) -> bool:
        """Check if player can aim at coordinates.

        Args:
            player_id: The ID of the player

        Returns:
            False if player has already fired and is waiting for opponent
        """
        return not self._waiting_for_opponent.get(player_id, False)
