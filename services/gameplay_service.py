"""Service for managing gameplay actions: aiming, firing, and resolving rounds."""

from enum import Enum
from typing import NamedTuple
from game.model import Coord, GameBoard
from game.round import Round


class CellState(Enum):
    """State of a cell on the Shots Fired board."""

    FIRED = "fired"  # Previously fired in a past round
    AIMED = "aimed"  # Currently aimed for this round
    AVAILABLE = "available"  # Can be clicked to aim
    UNAVAILABLE = "unavailable"  # Cannot be clicked (limit reached)


class AimShotResult(NamedTuple):
    """Result of attempting to aim a shot."""

    success: bool
    error_message: str | None = None
    aimed_count: int = 0


class GameplayService:
    """Service for managing gameplay actions during a game."""

    def __init__(self) -> None:
        """Initialize the gameplay service."""
        self.active_rounds: dict[str, Round] = {}  # game_id -> Round
        self.player_boards: dict[
            str, dict[str, GameBoard]
        ] = {}  # game_id -> {player_id -> board}
        self.fired_shots: dict[
            str, dict[str, dict[Coord, int]]
        ] = {}  # game_id -> player_id -> coord -> round_number

    def create_round(self, game_id: str, round_number: int) -> Round:
        """Create a new round for a game.

        Args:
            game_id: The ID of the game
            round_number: The round number to create

        Returns:
            The created Round object
        """
        round_obj = Round(round_number=round_number, game_id=game_id)
        self.active_rounds[game_id] = round_obj
        return round_obj

    def register_player_board(
        self, game_id: str, player_id: str, board: GameBoard
    ) -> None:
        """Register a player's board for shot limit calculations.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player
            board: The player's GameBoard
        """
        if game_id not in self.player_boards:
            self.player_boards[game_id] = {}
        self.player_boards[game_id][player_id] = board

    def aim_shot(self, game_id: str, player_id: str, coord: Coord) -> AimShotResult:
        """Add a shot to the aiming queue for the current round.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player aiming
            coord: The coordinate to aim at

        Returns:
            AimShotResult indicating success/failure and current aimed count
        """
        # Get the active round for this game
        round_obj = self.active_rounds.get(game_id)
        if round_obj is None:
            return AimShotResult(
                success=False,
                error_message="No active round for this game",
                aimed_count=0,
            )

        # Initialize player's aimed shots if not present
        if player_id not in round_obj.aimed_shots:
            round_obj.aimed_shots[player_id] = []

        # Check for duplicate coordinate
        if coord in round_obj.aimed_shots[player_id]:
            return AimShotResult(
                success=False,
                error_message=f"Coordinate {coord.name} already selected for this round",
                aimed_count=len(round_obj.aimed_shots[player_id]),
            )

        # Check shot limit
        current_aimed_count = len(round_obj.aimed_shots[player_id])
        shots_available = self._get_shots_available(game_id, player_id)

        if current_aimed_count >= shots_available:
            return AimShotResult(
                success=False,
                error_message=f"Shot limit reached: {shots_available} shots available",
                aimed_count=current_aimed_count,
            )

        # Add the shot to the player's aimed shots
        round_obj.aimed_shots[player_id].append(coord)

        return AimShotResult(
            success=True,
            error_message=None,
            aimed_count=len(round_obj.aimed_shots[player_id]),
        )

    def _get_shots_available(self, game_id: str, player_id: str) -> int:
        """Get the number of shots available for a player.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player

        Returns:
            Number of shots available based on unsunk ships
        """
        if game_id not in self.player_boards:
            return 0

        board = self.player_boards[game_id].get(player_id)
        if board is None:
            return 0

        return board.calculate_shots_available()

    def get_aimed_shots(self, game_id: str, player_id: str) -> list[Coord]:
        """Get the list of currently aimed shots for a player.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player

        Returns:
            List of Coord objects that have been aimed
        """
        round_obj = self.active_rounds.get(game_id)
        if round_obj is None:
            return []

        return round_obj.aimed_shots.get(player_id, [])

    def clear_aimed_shot(self, game_id: str, player_id: str, coord: Coord) -> bool:
        """Remove a shot from the aiming queue.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player
            coord: The coordinate to remove

        Returns:
            True if shot was removed, False if it wasn't in the list
        """
        round_obj = self.active_rounds.get(game_id)
        if round_obj is None:
            return False

        if player_id not in round_obj.aimed_shots:
            return False

        try:
            round_obj.aimed_shots[player_id].remove(coord)
            return True
        except ValueError:
            # Coord not in list
            return False

    def get_cell_state(self, game_id: str, player_id: str, coord: Coord) -> CellState:
        """Determine the state of a cell on the Shots Fired board.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player
            coord: The coordinate to check

        Returns:
            CellState indicating the current state of the cell
        """
        # Check if cell was fired in a previous round (highest priority)
        if game_id in self.fired_shots:
            if player_id in self.fired_shots[game_id]:
                if coord in self.fired_shots[game_id][player_id]:
                    return CellState.FIRED

        # Check if cell is currently aimed
        round_obj = self.active_rounds.get(game_id)
        if round_obj is not None:
            aimed_shots = round_obj.aimed_shots.get(player_id, [])
            if coord in aimed_shots:
                return CellState.AIMED

            # Check if shot limit is reached (cell is unavailable)
            current_aimed_count = len(aimed_shots)
            shots_available = self._get_shots_available(game_id, player_id)
            if current_aimed_count >= shots_available:
                return CellState.UNAVAILABLE

        # Default: cell is available for aiming
        return CellState.AVAILABLE
