"""Domain models for round-based gameplay."""

from dataclasses import dataclass, field
from game.model import Coord, ShipType


class Round:
    """Manages a single round of gameplay where both players fire shots simultaneously."""

    def __init__(self, round_number: int, game_id: str) -> None:
        """Initialize a new round.

        Args:
            round_number: The sequential round number (1, 2, 3, ...)
            game_id: The ID of the game this round belongs to
        """
        self.round_number: int = round_number
        self.game_id: str = game_id
        self.aimed_shots: dict[str, list[Coord]] = {}  # player_id -> aimed coords
        self.submitted_players: set[str] = set()
        self.is_resolved: bool = False
        self.result: "RoundResult | None" = None


@dataclass
class Shot:
    """Represents a single shot fired at a coordinate."""

    coord: Coord
    round_number: int
    player_id: str


@dataclass
class HitResult:
    """Result of a shot hitting a ship."""

    ship_type: ShipType
    coord: Coord
    is_sinking_hit: bool  # Was this the hit that sunk the ship?


@dataclass
class RoundResult:
    """Complete results for a round after both players fire."""

    round_number: int
    player_shots: dict[str, list[Shot]] = field(
        default_factory=dict
    )  # player_id -> shots
    hits_made: dict[str, list[HitResult]] = field(
        default_factory=dict
    )  # player_id -> hits they made
    ships_sunk: dict[str, list[ShipType]] = field(
        default_factory=dict
    )  # player_id -> ships they sunk
    game_over: bool = False
    winner_id: str | None = None
    is_draw: bool = False
