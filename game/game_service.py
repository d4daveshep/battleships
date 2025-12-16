from dataclasses import dataclass
from enum import StrEnum


class GameMode(StrEnum):
    """Game mode enumeration for distinguishing single vs multiplayer games"""

    SINGLE_PLAYER = "Single Player"
    MULTIPLAYER = "Multiplayer"


@dataclass
class GameState:
    """Game state management for tracking game sessions"""

    player_name: str
    game_mode: GameMode
    opponent_name: str | None

    def __post_init__(self):
        # Validate that multiplayer games have an opponent
        if self.game_mode == GameMode.MULTIPLAYER and not self.opponent_name:
            raise ValueError("Multiplayer games must have an opponent")

        # Validate that single player games don't have an opponent
        if self.game_mode == GameMode.SINGLE_PLAYER and self.opponent_name:
            raise ValueError("Single player games cannot have an opponent")


class PlayerAlreadyInGameException(Exception):
    pass


class GameService:
    def __init__(self) -> None:
        self.games: dict[str, GameState] = {}

    # FIXME: change games key to game_id and store both players and player_ids
    def create_single_player_game(self, player_id: str, player_name: str) -> str:
        if player_id in self.games:
            raise PlayerAlreadyInGameException(
                f"Player {player_name} with player_id {player_id} is already in a game"
            )
        else:
            self.games[player_id] = GameState(
                player_name=player_name, game_mode=GameMode.SINGLE_PLAYER
            )
