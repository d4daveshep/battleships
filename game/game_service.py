import secrets
from enum import StrEnum

from game.model import GameBoard
from game.player import Player, PlayerStatus


class GameMode(StrEnum):
    """Game mode enumeration for distinguishing single vs multiplayer games"""

    SINGLE_PLAYER = "Single Player"
    TWO_PLAYER = "Two Player"


class Game:
    """Game state management for tracking game sessions"""

    def __init__(
        self, player_1: Player, game_mode: GameMode, player_2: Player | None = None
    ) -> None:
        self.player_1: Player = player_1
        self.game_mode: GameMode = game_mode
        self.player_2: Player | None = player_2
        self._id: str = Game.generate_id()

        # Validate that two player games have an opponent
        if self.game_mode == GameMode.TWO_PLAYER and not self.player_2:
            raise ValueError("Two player games must two players")

        # Validate that single player games don't have an opponent
        if self.game_mode == GameMode.SINGLE_PLAYER and self.player_2:
            raise ValueError("Single player games cannot have two players")

        # Create game boards
        self.board: dict[Player, GameBoard] = {}
        self.board[self.player_1] = GameBoard()
        if self.player_2:
            self.board[self.player_2] = GameBoard()

    @property
    def id(self) -> str:
        """Read-only player ID that is automatically generated at creation."""
        return self._id

    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique player ID using a cryptographically secure random token.

        Returns:
            str: A URL-safe random token string (always 22 characters, from 16 random bytes)
        """
        return secrets.token_urlsafe(16)


class PlayerAlreadyInGameException(Exception):
    pass


class UnknownPlayerException(Exception):
    pass


class PlayerNotInGameException(Exception):
    pass


class GameService:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}  # game_id->Game
        self.games_by_player: dict[str, Game] = {}  # player_id->Game
        self.players: dict[str, Player] = {}  # player_id->Player

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def create_single_player_game(self, player_id: str) -> str:
        try:
            player = self.players[player_id]
        except KeyError:
            raise UnknownPlayerException(f"Player with id:{player_id} does not exist")

        if player_id in self.games_by_player or player.status == PlayerStatus.IN_GAME:
            raise PlayerAlreadyInGameException(
                f"Player {player.name} with player_id {player_id} is already in a game"
            )

        new_game: Game = Game(player_1=player, game_mode=GameMode.SINGLE_PLAYER)
        self.games[new_game.id] = new_game
        self.games_by_player[player_id] = new_game
        # TODO: Set the game phase to something like "starting"
        player.status = PlayerStatus.IN_GAME
        return new_game.id

    def get_game_board(self, player_id: str) -> GameBoard:
        player: Player
        game: Game
        try:
            player = self.players[player_id]
        except KeyError:
            raise UnknownPlayerException(f"Player with id:{player_id} does not exist")
        try:
            game = self.games_by_player[player_id]
        except KeyError:
            raise PlayerNotInGameException(
                f"Player {player.name} with id:{player_id} exists but is not in a game"
            )
        return game.board[player]
