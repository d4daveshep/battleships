import secrets
from enum import StrEnum

from game.model import GameBoard
from game.player import Player, PlayerStatus


class GameMode(StrEnum):
    """Game mode enumeration for distinguishing single vs multiplayer games"""

    SINGLE_PLAYER = "single Player"
    TWO_PLAYER = "two Player"


class GameStatus(StrEnum):
    """Game status enumeration for various stages of the game"""

    CREATED = "created"
    SETUP = "setup"
    PLAYING = "playing"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class Game:
    """Game state management for tracking game sessions"""

    def __init__(
        self, player_1: Player, game_mode: GameMode, player_2: Player | None = None
    ) -> None:
        self.player_1: Player = player_1
        self.game_mode: GameMode = game_mode
        self.player_2: Player | None = player_2
        self._id: str = Game.generate_id()
        self.status: GameStatus = GameStatus.CREATED

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


class DuplicatePlayerException(Exception):
    pass


class UnknownGameException(Exception):
    pass


class GameService:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}  # game_id->Game
        self.games_by_player: dict[str, Game] = {}  # player_id->Game
        self.players: dict[str, Player] = {}  # player_id->Player

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def get_player(self, player_id: str) -> Player | None:
        """Get player by ID

        Args:
            player_id: The player ID to look up

        Returns:
            Player object if found, None otherwise
        """
        return self.players.get(player_id)

    def create_single_player_game(self, player_id: str) -> str:
        try:
            player = self.players[player_id]
        except KeyError:
            raise UnknownPlayerException(f"Player with id:{player_id} does not exist")

        if player_id in self.games_by_player or player.status == PlayerStatus.IN_GAME:
            raise PlayerAlreadyInGameException(
                f"Player {player.name} with id: {player_id} is already in a game"
            )

        new_game: Game = Game(player_1=player, game_mode=GameMode.SINGLE_PLAYER)
        self.games[new_game.id] = new_game
        self.games_by_player[player_id] = new_game
        player.status = PlayerStatus.IN_GAME
        return new_game.id

    def create_two_player_game(self, player_1_id: str, player_2_id: str) -> str:
        try:
            player_1: Player = self.players[player_1_id]
            player_2: Player = self.players[player_2_id]
        except KeyError as e:
            key = e.args[0]
            raise UnknownPlayerException(f"Player with id:{key} does not exist")

        if (
            player_1_id in self.games_by_player
            or player_1.status == PlayerStatus.IN_GAME
        ):
            raise PlayerAlreadyInGameException(
                f"Player {player_1.name} with id: {player_1_id} is already in a game"
            )

        if (
            player_2_id in self.games_by_player
            or player_2.status == PlayerStatus.IN_GAME
        ):
            raise PlayerAlreadyInGameException(
                f"Player {player_2.name} with id: {player_2_id} is already in a game"
            )

        if player_1_id == player_2_id:
            raise DuplicatePlayerException(
                f"Two player game must have two different players: {player_1.name}"
            )

        new_game: Game = Game(
            player_1=player_1, player_2=player_2, game_mode=GameMode.TWO_PLAYER
        )
        self.games[new_game.id] = new_game
        self.games_by_player[player_1_id] = new_game
        self.games_by_player[player_2_id] = new_game
        player_1.status = PlayerStatus.IN_GAME
        player_2.status = PlayerStatus.IN_GAME

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

    def get_game_status_by_player_id(self, player_id: str) -> GameStatus:
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
        return game.status

    def get_game_status_by_game_id(self, game_id: str) -> GameStatus:
        try:
            game = self.games[game_id]
        except KeyError:
            raise UnknownGameException(f"Game with id:{game_id} does not exist")
        return game.status

    def get_game_id_by_player_id(self, player_id: str) -> str:
        raise NotImplementedError

    def abandon_game_by_player_id(self, player_id: str) -> None:
        raise NotImplementedError

    def abandon_game_by_game_id(self, game_id: str) -> None:
        raise NotImplementedError
