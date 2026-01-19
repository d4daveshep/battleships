"""Service for managing gameplay actions: aiming, firing, and resolving rounds."""

import asyncio
from enum import Enum
from typing import NamedTuple
from game.model import Coord, GameBoard, ShipType
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
        self.round_versions: dict[str, int] = {}  # game_id -> version
        self.round_events: dict[str, asyncio.Event] = {}  # game_id -> Event

    def get_round_version(self, game_id: str) -> int:
        """Get the current version of the round for a game."""
        return self.round_versions.get(game_id, 0)

    async def wait_for_round_change(self, game_id: str, since_version: int) -> None:
        """Wait for the round version to change."""
        if self.get_round_version(game_id) != since_version:
            return

        if game_id not in self.round_events:
            self.round_events[game_id] = asyncio.Event()

        await self.round_events[game_id].wait()

    def _notify_round_change(self, game_id: str) -> None:
        """Increment version and notify waiters."""
        self.round_versions[game_id] = self.get_round_version(game_id) + 1
        if game_id in self.round_events:
            self.round_events[game_id].set()
            self.round_events[game_id] = asyncio.Event()  # Reset for next change

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

        # If current round is resolved, create next round
        if round_obj is not None and round_obj.is_resolved:
            next_round_number: int = round_obj.round_number + 1
            round_obj = self.create_round(
                game_id=game_id, round_number=next_round_number
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
        if round_obj is None or round_obj.is_resolved:
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
            return FireShotsResult(
                success=False, message="Shots already submitted for this round"
            )

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
            message="Waiting for opponent to fire...",
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
                Shot(
                    coord=coord,
                    round_number=round_obj.round_number,
                    player_id=player_id,
                )
                for coord in coords
            ]

        # Detect hits for each player
        player_ids = list(round_obj.submitted_players)
        hits_made: dict[str, list[HitResult]] = {}
        ships_sunk: dict[str, list[ShipType]] = {}

        # For 2-player game, detect hits for each player against their opponent
        if len(player_ids) == 2:
            for i in range(2):
                attacker_id = player_ids[i]
                defender_id = player_ids[1 - i]

                hits_made[attacker_id] = []
                ships_sunk[attacker_id] = []

                defender_board = self.player_boards.get(game_id, {}).get(defender_id)
                if defender_board:
                    for coord in round_obj.aimed_shots.get(attacker_id, []):
                        # Record shot received on defender board (hit or miss)
                        defender_board.record_shot_received(
                            coord, round_obj.round_number
                        )

                        ship_type = defender_board.ship_type_at(coord)
                        if ship_type:
                            is_sunk = defender_board.record_hit(
                                ship_type, coord, round_obj.round_number
                            )
                            hits_made[attacker_id].append(
                                HitResult(
                                    ship_type=ship_type,
                                    coord=coord,
                                    is_sinking_hit=is_sunk,
                                )
                            )
                            if is_sunk:
                                ships_sunk[attacker_id].append(ship_type)

        # Check for game over
        game_over, winner_id, is_draw = self.check_game_over(game_id)

        # Create RoundResult
        result = RoundResult(
            round_number=round_obj.round_number,
            player_shots=player_shots,
            hits_made=hits_made,
            ships_sunk=ships_sunk,
            game_over=game_over,
            winner_id=winner_id,
            is_draw=is_draw,
        )

        # Mark round as resolved
        round_obj.is_resolved = True
        round_obj.result = result
        self._notify_round_change(game_id)

    def check_game_over(self, game_id: str) -> tuple[bool, str | None, bool]:
        """Check if the game is over.

        Returns:
            tuple of (game_over, winner_id, is_draw)
        """
        if game_id not in self.player_boards:
            return False, None, False

        boards = self.player_boards[game_id]
        if len(boards) < 2:
            return False, None, False

        player_ids = list(boards.keys())
        p1_id = player_ids[0]
        p2_id = player_ids[1]

        p1_all_sunk = self._all_ships_sunk(game_id, p1_id)
        p2_all_sunk = self._all_ships_sunk(game_id, p2_id)

        if p1_all_sunk and p2_all_sunk:
            return True, None, True
        if p1_all_sunk:
            return True, p2_id, False
        if p2_all_sunk:
            return True, p1_id, False

        return False, None, False

    def _all_ships_sunk(self, game_id: str, player_id: str) -> bool:
        """Check if all ships of a player are sunk."""
        board = self.player_boards.get(game_id, {}).get(player_id)
        if not board:
            return False

        if not board.ships:
            return False

        for ship in board.ships:
            if not board.is_ship_sunk(ship.ship_type):
                return False
        return True

    def calculate_hit_feedback(self, hits: list[HitResult]) -> dict[str, int]:
        """Calculate ship-based hit feedback from hit results.

        Converts coordinate-based hits into ship-based feedback showing
        which ships were hit and how many times (without exposing coordinates).

        Args:
            hits: List of HitResult objects

        Returns:
            Dictionary mapping ship names to hit counts
            Example: {"Carrier": 2, "Destroyer": 1}
        """
        feedback: dict[str, int] = {}

        for hit in hits:
            ship_name: str = hit.ship_type.ship_name
            feedback[ship_name] = feedback.get(ship_name, 0) + 1

        return feedback
