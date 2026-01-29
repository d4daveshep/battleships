import asyncio
import random
from enum import StrEnum
from typing import TYPE_CHECKING

from game.exceptions import (
    DuplicatePlayerException,
    PlayerAlreadyInGameException,
    PlayerNotInGameException,
    UnknownGameException,
    UnknownPlayerException,
    ShotLimitExceededError,
)
from typing import NamedTuple

from game.model import (
    Coord,
    Game,
    GameBoard,
    GameMode,
    GameStatus,
    Orientation,
    Ship,
    ShipType,
)


class AimResult(NamedTuple):
    """Result of a toggle_aim operation."""

    is_aimed: bool
    aimed_count: int
    shots_available: int


class SelectShotResult(NamedTuple):
    """Result of a select_shot operation."""

    success: bool
    error: str | None = None


class ShotStatus(StrEnum):
    """Status of the shot processing."""

    WAITING = "waiting"
    COMPLETED = "completed"


class ShotResult(NamedTuple):
    """Result of a fire_shots operation."""

    status: ShotStatus
    game: Game


from game.player import Player, PlayerStatus

if TYPE_CHECKING:
    from services.lobby_service import LobbyService

# Re-export for backwards compatibility
__all__ = [
    "GameService",
    "Game",
    "GameMode",
    "GameStatus",
    "PlayerAlreadyInGameException",
    "UnknownPlayerException",
    "PlayerNotInGameException",
    "DuplicatePlayerException",
    "UnknownGameException",
    "AimResult",
    "SelectShotResult",
    "ShotStatus",
    "ShotResult",
]


class GameService:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}  # game_id->Game
        self.games_by_player: dict[str, Game] = {}  # player_id->Game
        self.players: dict[str, Player] = {}  # player_id->Player
        self.ship_placement_boards: dict[
            str, GameBoard
        ] = {}  # player_id->GameBoard for ship placement phase
        self.ready_players: set[str] = set()
        # Initialize placement version tracking
        self._placement_version: int = 0
        self._placement_change_event: "asyncio.Event" = asyncio.Event()

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

    def _get_player_or_raise(self, player_id: str) -> Player:
        """Get player by ID or raise UnknownPlayerException.

        Args:
            player_id: The player ID to look up

        Returns:
            Player object

        Raises:
            UnknownPlayerException: If player doesn't exist
        """
        try:
            return self.players[player_id]
        except KeyError:
            raise UnknownPlayerException(f"Player with id:{player_id} does not exist")

    def _get_game_or_raise(self, game_id: str) -> Game:
        """Get game by ID or raise UnknownGameException.

        Args:
            game_id: The game ID to look up

        Returns:
            Game object

        Raises:
            UnknownGameException: If game doesn't exist
        """
        try:
            return self.games[game_id]
        except KeyError:
            raise UnknownGameException(f"Game with id:{game_id} does not exist")

    def set_game_status(self, game_id: str, new_status: GameStatus) -> None:
        """Update the status of a game.

        Args:
            game_id: The game ID
            new_status: The new status to set

        Raises:
            UnknownGameException: If game doesn't exist
        """
        game = self._get_game_or_raise(game_id)
        game.status = new_status

    def start_game(self, game_id: str) -> None:
        """Transition game from SETUP to PLAYING.

        Args:
            game_id: The game ID

        Raises:
            UnknownGameException: If game doesn't exist
        """
        self.set_game_status(game_id, GameStatus.PLAYING)

    def create_game_from_accepted_request(
        self, sender_id: str, receiver_id: str
    ) -> str:
        """Create a two-player game when a game request is accepted.

        This method is idempotent - if a game already exists for either player,
        it returns the existing game ID without creating a new one.

        Args:
            sender_id: The ID of the player who sent the game request
            receiver_id: The ID of the player who accepted the request

        Returns:
            The game ID (new or existing)
        """
        # Check if game already exists (handles concurrent accepts)
        if sender_id in self.games_by_player:
            return self.games_by_player[sender_id].id
        if receiver_id in self.games_by_player:
            return self.games_by_player[receiver_id].id

        # Create new game
        game_id = self.create_two_player_game(sender_id, receiver_id)
        game = self.games[game_id]
        game.status = GameStatus.SETUP
        return game_id

    def create_single_player_game(self, player_id: str) -> str:
        player = self._get_player_or_raise(player_id)

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
        player_1: Player = self._get_player_or_raise(player_1_id)
        player_2: Player = self._get_player_or_raise(player_2_id)

        # Check if either player is already in a game
        if player_1_id in self.games_by_player:
            raise PlayerAlreadyInGameException(
                f"Player {player_1.name} with id: {player_1_id} is already in a game"
            )

        if player_2_id in self.games_by_player:
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

    # TODO: Review where this function gets called from to see if we actually need it,
    # Why can't we just put the board directly in the game?
    def transfer_ship_placement_board_to_game(
        self, game_id: str, player_id: str, player: Player
    ) -> None:
        """Transfer a player's ship placement board to a game.

        Args:
            game_id: The game ID
            player_id: The player ID
            player: The Player object

        Raises:
            UnknownGameException: If game doesn't exist
        """
        game = self._get_game_or_raise(game_id)
        if player_id in self.ship_placement_boards:
            game.board[player] = self.ship_placement_boards[player_id]
            del self.ship_placement_boards[player_id]

    # TODO: Review this function and the commonality with get_or_create_ship_placement_board to see if we need both
    def get_game_board(self, player_id: str) -> GameBoard:
        player: Player = self._get_player_or_raise(player_id)
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
        player: Player = self._get_player_or_raise(player_id)

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

    def notify_placement_change(self) -> None:
        """Notify that placement state has changed (e.g., player left)."""
        self._notify_placement_change()

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
        player = self._get_player_or_raise(player_id)
        try:
            game = self.games_by_player[player_id]
        except KeyError:
            raise PlayerNotInGameException(
                f"Player {player.name} with id:{player_id} exists but is not in a game"
            )
        return game.status

    def get_game_status_by_game_id(self, game_id: str) -> GameStatus:
        game = self._get_game_or_raise(game_id)
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

    def is_multiplayer(self, player_id: str) -> bool:
        """Check if a player is in a multiplayer (two-player) game.

        Args:
            player_id: The player ID to check

        Returns:
            True if player is in a two-player game, False otherwise
        """
        # Get opponent ID - returns None if no opponent
        opponent_id = self.get_opponent_id(player_id)
        if not opponent_id:
            return False

        # Player has an opponent - check game mode
        game = self.games_by_player[player_id]
        return game.game_mode == GameMode.TWO_PLAYER

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
        return self._placement_version

    def _notify_placement_change(self) -> None:
        """Increment version and notify waiters of placement state change."""
        self._placement_version += 1
        self._placement_change_event.set()

    async def wait_for_placement_change(self, since_version: int) -> None:
        """Wait for placement state to change from the given version.

        Args:
            since_version: The version to wait for changes from

        Returns immediately if the current version is different from since_version.
        Otherwise, waits for the change_event to be set.
        """
        # If version already changed, return immediately
        if self._placement_version != since_version:
            return

        # Clear the event for this wait cycle
        self._placement_change_event.clear()

        # Check version again after clearing (in case it changed)
        if self._placement_version != since_version:
            return

        # Wait for the event to be set
        await self._placement_change_event.wait()

    def toggle_aim(self, game_id: str, player_id: str, coord_str: str) -> AimResult:
        """Toggle aiming at a coordinate for a player.

        If the coordinate is not aimed, add it. If already aimed, remove it.

        Args:
            game_id: The game ID
            player_id: The player ID
            coord_str: The coordinate string (e.g., "A1", "J10")

        Returns:
            AimResult with is_aimed, aimed_count, and shots_available

        Raises:
            UnknownGameException: If game doesn't exist
        """
        game = self._get_game_or_raise(game_id)
        coord: Coord = Coord[coord_str]

        if coord in game.get_aimed_shots(player_id):
            game.unaim_at(player_id, coord)
            is_aimed = False
        else:
            game.aim_at(player_id, coord)
            is_aimed = True

        return AimResult(
            is_aimed=is_aimed,
            aimed_count=game.get_aimed_shots_count(player_id),
            shots_available=game.get_shots_available(player_id),
        )

    def select_shot(
        self, game_id: str, player_id: str, coord_str: str
    ) -> SelectShotResult:
        """Select a shot coordinate for a player.

        Args:
            game_id: The game ID
            player_id: The player ID
            coord_str: The coordinate string (e.g., "A1", "J10")

        Returns:
            SelectShotResult with success status and optional error message

        Raises:
            UnknownGameException: If game doesn't exist
        """
        game = self._get_game_or_raise(game_id)
        coord: Coord = Coord[coord_str]

        try:
            game.aim_at(player_id, coord)
            return SelectShotResult(success=True)
        except ShotLimitExceededError:
            return SelectShotResult(success=False, error="All available shots aimed")
        except Exception as e:
            return SelectShotResult(success=False, error=str(e))

    def fire_shots(self, game_id: str, player_id: str) -> ShotResult:
        """Submit the player's aimed shots and enter waiting state.

        Args:
            game_id: The game ID
            player_id: The player ID

        Returns:
            ShotResult with status and updated game

        Raises:
            UnknownGameException: If game doesn't exist
            UnknownPlayerException: If player doesn't exist
            NoShotsAimedError: If player has no shots aimed
            ActionAfterFireError: If player has already fired
        """
        game = self._get_game_or_raise(game_id)
        player = self._get_player_or_raise(player_id)

        # Delegate to Game model
        game.fire_shots(player_id)

        status = (
            ShotStatus.WAITING
            if game.is_waiting_for_opponent(player_id)
            else ShotStatus.COMPLETED
        )
        return ShotResult(status, game)
