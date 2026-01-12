"""Service for managing gameplay actions: aiming, firing, and resolving rounds."""

from enum import Enum
from typing import NamedTuple
from game.model import Coord, GameBoard
from game.round import Round, RoundResult, Shot, HitResult


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


class FireShotsResult(NamedTuple):
    """Result of firing shots."""

    success: bool
    message: str
    waiting_for_opponent: bool = False


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

        # Check if player has already submitted shots for this round
        if player_id in round_obj.submitted_players:
            return AimShotResult(
                success=False,
                error_message="Shots already submitted for this round - waiting for opponent",
                aimed_count=len(round_obj.aimed_shots.get(player_id, [])),
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

        # Check if coordinate was already fired in previous rounds
        if game_id in self.fired_shots:
            if player_id in self.fired_shots[game_id]:
                if coord in self.fired_shots[game_id][player_id]:
                    return AimShotResult(
                        success=False,
                        error_message=f"Coordinate {coord.name} already fired at in previous round",
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

            # Check if player has already submitted shots (waiting state)
            if player_id in round_obj.submitted_players:
                return CellState.UNAVAILABLE

        # Default: cell is available for aiming
        return CellState.AVAILABLE

    def fire_shots(self, game_id: str, player_id: str) -> FireShotsResult:
        """Submit aimed shots for the current round.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player firing

        Returns:
            FireShotsResult indicating success/failure
        """
        round_obj = self.active_rounds.get(game_id)
        if round_obj is None:
            return FireShotsResult(success=False, message="No active round")

        # Check if player has already submitted shots for this round
        if player_id in round_obj.submitted_players:
            return FireShotsResult(success=False, message="Shots already submitted for this round")

        if (
            player_id not in round_obj.aimed_shots
            or not round_obj.aimed_shots[player_id]
        ):
            return FireShotsResult(success=False, message="No shots aimed")

        # Add to submitted players
        round_obj.submitted_players.add(player_id)

        # Record fired shots (for validation in future rounds)
        if game_id not in self.fired_shots:
            self.fired_shots[game_id] = {}
        if player_id not in self.fired_shots[game_id]:
            self.fired_shots[game_id][player_id] = {}

        for coord in round_obj.aimed_shots[player_id]:
            self.fired_shots[game_id][player_id][coord] = round_obj.round_number

        # Check if both players have submitted - if so, resolve the round
        # Assuming 2-player game for now
        if len(round_obj.submitted_players) == 2:
            self.resolve_round(game_id)
            return FireShotsResult(
                success=True,
                message="Round resolved!",
                waiting_for_opponent=False,
            )

        return FireShotsResult(
            success=True,
            message="Shots fired!",
            waiting_for_opponent=True,
        )

    def resolve_round(self, game_id: str) -> None:
        """Resolve the current round after both players have fired.

        Args:
            game_id: The ID of the game
        """
        round_obj = self.active_rounds.get(game_id)
        if round_obj is None or round_obj.is_resolved:
            return

        # Create Shot objects for each player
        player_shots: dict[str, list[Shot]] = {}
        for player_id, coords in round_obj.aimed_shots.items():
            player_shots[player_id] = [
                Shot(coord=coord, round_number=round_obj.round_number, player_id=player_id)
                for coord in coords
            ]

        # Detect hits for each player
        player_ids = list(round_obj.submitted_players)
        hits_made: dict[str, list[HitResult]] = {}
        
        # For 2-player game, detect hits for each player against their opponent
        if len(player_ids) == 2:
            player1_id = player_ids[0]
            player2_id = player_ids[1]
            
            # Player 1 hits on player 2's board
            hits_made[player1_id] = self._detect_hits(
                game_id=game_id,
                player_id=player1_id,
                shots=round_obj.aimed_shots[player1_id],
                opponent_id=player2_id,
            )
            
            # Player 2 hits on player 1's board
            hits_made[player2_id] = self._detect_hits(
                game_id=game_id,
                player_id=player2_id,
                shots=round_obj.aimed_shots[player2_id],
                opponent_id=player1_id,
            )

        # Create RoundResult
        result = RoundResult(
            round_number=round_obj.round_number,
            player_shots=player_shots,
            hits_made=hits_made,
            ships_sunk={},
            game_over=False,
            winner_id=None,
            is_draw=False,
        )

        # Mark round as resolved
        round_obj.is_resolved = True
        round_obj.result = result

    def _detect_hits(
        self, game_id: str, player_id: str, shots: list[Coord], opponent_id: str
    ) -> list[HitResult]:
        """Detect which shots hit opponent ships.

        Args:
            game_id: The ID of the game
            player_id: The ID of the player who fired the shots
            shots: List of coordinates that were fired at
            opponent_id: The ID of the opponent whose board to check

        Returns:
            List of HitResult objects for shots that hit ships
        """
        hits: list[HitResult] = []

        # Get opponent's board
        if game_id not in self.player_boards:
            return hits

        opponent_board = self.player_boards[game_id].get(opponent_id)
        if opponent_board is None:
            return hits

        # Check each shot against opponent's ships
        for coord in shots:
            ship_type = opponent_board.ship_type_at(coord)
            if ship_type is not None:
                # Hit! Create HitResult (is_sinking_hit will be determined in Phase 5)
                hits.append(
                    HitResult(
                        ship_type=ship_type,
                        coord=coord,
                        is_sinking_hit=False,  # Will be implemented in Phase 5
                    )
                )

        return hits
