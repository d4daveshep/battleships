import asyncio
import random
import secrets
from enum import StrEnum

from game.model import Coord, GameBoard, Orientation, Ship, ShipType
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
        self.ship_placement_boards: dict[
            str, GameBoard
        ] = {}  # player_id->GameBoard for ship placement phase
        self.ready_players: set[str] = set()

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
        self._notify_placement_change()

        return new_game.id

    # TODO: Review this function and the commonality with get_or_create_ship_placement_board to see if we need both
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

    # TODO: Review this function and the commonality with get_game_board to see if we need both
    def get_or_create_ship_placement_board(self, player_id: str) -> GameBoard:
        """Get or create a game board for ship placement phase.

        This is used during ship placement before a game is officially created.
        Once the game starts, the board is transferred to the Game object.

        Args:
            player_id: The player ID

        Returns:
            GameBoard for the player to place ships on

        Raises:
            UnknownPlayerException: If player doesn't exist
        """
        try:
            player: Player = self.players[player_id]
        except KeyError:
            raise UnknownPlayerException(f"Player with id:{player_id} does not exist")

        # If player already has a ship placement board, return it
        if player_id in self.ship_placement_boards:
            return self.ship_placement_boards[player_id]

        # If player is already in a game, return their game board
        if player_id in self.games_by_player:
            game: Game = self.games_by_player[player_id]
            return game.board[player]

        # Create a new ship placement board
        new_board: GameBoard = GameBoard()
        self.ship_placement_boards[player_id] = new_board
        return new_board

    def place_ships_randomly(self, player_id: str) -> None:
        """Place all 5 ships randomly on the board following placement rules.

        Clears any existing ships and places all ships randomly.

        Args:
            player_id: The player ID

        Raises:
            UnknownPlayerException: If player doesn_t exist
        """

        # Get or create the board
        board = self.get_or_create_ship_placement_board(player_id)

        # Clear existing ships
        board.clear_all_ships()

        # All ship types to place
        ship_types = [
            ShipType.CARRIER,
            ShipType.BATTLESHIP,
            ShipType.CRUISER,
            ShipType.SUBMARINE,
            ShipType.DESTROYER,
        ]

        # All possible coordinates and orientations
        all_coords = list(Coord)
        all_orientations = list(Orientation)

        # Place each ship
        for ship_type in ship_types:
            ship = Ship(ship_type)
            placed = False
            max_attempts = 1000
            attempts = 0

            while not placed and attempts < max_attempts:
                attempts += 1
                # Pick random start position and orientation
                start = random.choice(all_coords)
                orientation = random.choice(all_orientations)

                try:
                    board.place_ship(ship, start, orientation)
                    placed = True
                except Exception:
                    # Try again with different position/orientation
                    continue

            if not placed:
                # Retry the whole process if we get stuck
                board.clear_all_ships()
                self.place_ships_randomly(player_id)
                return

    def set_player_ready(self, player_id: str) -> None:
        """Mark a player as ready for game."""
        self.ready_players.add(player_id)
        self._notify_placement_change()

    def is_player_ready(self, player_id: str) -> bool:
        """Check if a player is ready for game."""
        return player_id in self.ready_players

    def start_single_player_game(self, player_id: str) -> str:
        """Start a single player game against computer.

        Args:
            player_id: The player ID

        Returns:
            The game ID
        """

        # Create computer player
        computer = Player(name="Computer", status=PlayerStatus.AVAILABLE)
        self.add_player(computer)
        computer_id = computer.id

        # Create game (using TWO_PLAYER mode to support 2 boards)
        game_id = self.create_two_player_game(player_id, computer_id)
        game = self.games[game_id]
        player = self.players[player_id]

        # Transfer player_s board
        if player_id in self.ship_placement_boards:
            game.board[player] = self.ship_placement_boards[player_id]
            del self.ship_placement_boards[player_id]

        # Place computer ships randomly
        self.place_ships_randomly(computer_id)

        # Transfer computer_s board
        if computer_id in self.ship_placement_boards:
            game.board[computer] = self.ship_placement_boards[computer_id]
            del self.ship_placement_boards[computer_id]

        return game_id

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
        raise NotImplementedError("Complete unit tests first")

    def abandon_game_by_player_id(self, player_id: str) -> None:
        raise NotImplementedError("Complete unit tests first")

    def get_opponent_id(self, player_id: str) -> str | None:
        """Get the opponent's ID for a player in a game.

        Args:
            player_id: The player ID

        Returns:
            The opponent's player ID, or None if not in a game or no opponent
        """
        if player_id not in self.games_by_player:
            return None

        game = self.games_by_player[player_id]
        player = self.players.get(player_id)

        if game.player_1 == player:
            return game.player_2.id if game.player_2 else None
        elif game.player_2 == player:
            return game.player_1.id
        return None

    def is_opponent_ready(self, player_id: str) -> bool:
        """Check if the opponent is ready for game.

        Args:
            player_id: The player ID to check opponent for

        Returns:
            True if opponent is ready, False otherwise
        """
        opponent_id = self.get_opponent_id(player_id)
        if not opponent_id:
            return False
        return self.is_player_ready(opponent_id)

    def are_both_players_ready(self, game_id: str) -> bool:
        """Check if both players in a game are ready.

        Args:
            game_id: The game ID

        Returns:
            True if both players are ready, False otherwise
        """
        if game_id not in self.games:
            return False

        game = self.games[game_id]
        player_1_ready = self.is_player_ready(game.player_1.id)

        if not game.player_2:
            return player_1_ready

        player_2_ready = self.is_player_ready(game.player_2.id)
        return player_1_ready and player_2_ready

    def get_placement_version(self) -> int:
        """Get the current version of ship placement state.

        Returns:
            Current version number for change detection
        """
        if not hasattr(self, "_placement_version"):
            self._placement_version = 0
            self._placement_change_event = asyncio.Event()
        return self._placement_version

    def _notify_placement_change(self) -> None:
        """Increment version and notify waiters of placement state change."""
        if not hasattr(self, "_placement_version"):
            self._placement_version = 0
            self._placement_change_event = asyncio.Event()
        self._placement_version += 1
        self._placement_change_event.set()

    async def wait_for_placement_change(self, since_version: int) -> None:
        """Wait for placement state to change from the given version.

        Args:
            since_version: The version to wait for changes from

        Returns immediately if the current version is different from since_version.
        Otherwise, waits for the change_event to be set.
        """
        if not hasattr(self, "_placement_version"):
            self._placement_version = 0
            self._placement_change_event = asyncio.Event()

        # If version already changed, return immediately
        if self.get_placement_version() != since_version:
            return

        # Clear the event for this wait cycle
        self._placement_change_event.clear()

        # Check version again after clearing (in case it changed)
        if self.get_placement_version() != since_version:
            return

        # Wait for the event to be set
        await self._placement_change_event.wait()
