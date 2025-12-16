from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

import pytest

from game.game_service import GameService
from game.model import GameBoard


# FIXME: Move this model class to the game package


# FIXME: Move this model class to the game package


# FIXME: Move this model class to the game package
class GameStateManager:
    """Manages active game states for players"""

    def __init__(self):
        self.active_games: dict[str, GameState] = {}

    def start_single_player_game(self, player_name: str) -> GameState:
        """Start a single player game for the given player"""
        if player_name in self.active_games:
            raise ValueError(f"Player {player_name} is already in a game")

        game_state = GameState(
            player_name=player_name, game_mode=GameMode.SINGLE_PLAYER
        )
        self.active_games[player_name] = game_state
        return game_state

    def start_multiplayer_game(
        self, player1: str, player2: str
    ) -> tuple[GameState, GameState]:
        """Start a multiplayer game between two players"""
        if player1 in self.active_games:
            raise ValueError(f"Player {player1} is already in a game")
        if player2 in self.active_games:
            raise ValueError(f"Player {player2} is already in a game")

        game_state1 = GameState(
            player_name=player1, game_mode=GameMode.MULTIPLAYER, opponent_name=player2
        )
        game_state2 = GameState(
            player_name=player2, game_mode=GameMode.MULTIPLAYER, opponent_name=player1
        )

        self.active_games[player1] = game_state1
        self.active_games[player2] = game_state2

        return game_state1, game_state2

    def get_game_state(self, player_name: str) -> Optional[GameState]:
        """Get the current game state for a player"""
        return self.active_games.get(player_name)

    def is_player_in_game(self, player_name: str) -> bool:
        """Check if a player is currently in a game"""
        return player_name in self.active_games

    def end_game(self, player_name: str) -> Optional[str]:
        """End the game for a player and their opponent (if multiplayer)"""
        if player_name not in self.active_games:
            return None

        game_state = self.active_games[player_name]
        opponent_name = game_state.opponent_name

        # Remove the player's game
        del self.active_games[player_name]

        # If multiplayer, also remove opponent's game
        if opponent_name and opponent_name in self.active_games:
            del self.active_games[opponent_name]

        return opponent_name

    def clear_all_games(self) -> None:
        """Clear all active games"""
        self.active_games.clear()


class TestGameState:
    """Unit tests for GameState dataclass"""

    def test_single_player_game_state_creation(self):
        # Test creating a valid single player game state
        game_state = GameState(player_name="Alice", game_mode=GameMode.SINGLE_PLAYER)

        assert game_state.player_name == "Alice"
        assert game_state.game_mode == GameMode.SINGLE_PLAYER
        assert game_state.opponent_name is None

    def test_multiplayer_game_state_creation(self):
        # Test creating a valid multiplayer game state
        game_state = GameState(
            player_name="Alice", game_mode=GameMode.MULTIPLAYER, opponent_name="Bob"
        )

        assert game_state.player_name == "Alice"
        assert game_state.game_mode == GameMode.MULTIPLAYER
        assert game_state.opponent_name == "Bob"

    def test_multiplayer_game_state_without_opponent_fails(self):
        # Test that multiplayer game state requires an opponent
        with pytest.raises(ValueError, match="Multiplayer games must have an opponent"):
            GameState(player_name="Alice", game_mode=GameMode.MULTIPLAYER)

    def test_single_player_game_state_with_opponent_fails(self):
        # Test that single player game state cannot have an opponent
        with pytest.raises(
            ValueError, match="Single player games cannot have an opponent"
        ):
            GameState(
                player_name="Alice",
                game_mode=GameMode.SINGLE_PLAYER,
                opponent_name="Bob",
            )


class TestGameService:
    def test_create_game_service(self):
        service: GameService = GameService()
        assert service, "Can't create GameService"
        assert len(service.games) == 0

    def test_create_single_player_game(self):
        service: GameService = GameService()
        alice_id = "alice12345"
        game_id: str = service.create_single_player_game(
            player_id=alice_id, player_name="Alice"
        )
        assert len(game_id) == 24  # game_id should be a ?? length random string
        assert len(service.games) == 1

    def test_get_game_board_from_known_player_id(self):
        service: GameService = GameService()
        alice_id = "alice12345"
        service.create_single_player_game(player_id=alice_id, player_name="Alice")

        board: GameBoard = service.get_game_board(player_id=alice_id)
        assert board, "Didn't get GameBoard from GameService"

    # def test_get_game_from_player_id(self):
    #     player_id: str = "abcde12345"
    #     game_state: GameState = GameService.get_game(player_id)


class TestGameStateManager:
    """Unit tests for GameStateManager class"""

    def test_start_single_player_game_success(self):
        # Test starting a single player game
        manager = GameStateManager()

        game_state = manager.start_single_player_game("Alice")

        assert game_state.player_name == "Alice"
        assert game_state.game_mode == GameMode.SINGLE_PLAYER
        assert game_state.opponent_name is None
        assert manager.is_player_in_game("Alice")

    def test_start_multiplayer_game_success(self):
        # Test starting a multiplayer game
        manager = GameStateManager()

        game_state1, game_state2 = manager.start_multiplayer_game("Alice", "Bob")

        # Verify Alice's game state
        assert game_state1.player_name == "Alice"
        assert game_state1.game_mode == GameMode.MULTIPLAYER
        assert game_state1.opponent_name == "Bob"

        # Verify Bob's game state
        assert game_state2.player_name == "Bob"
        assert game_state2.game_mode == GameMode.MULTIPLAYER
        assert game_state2.opponent_name == "Alice"

        # Verify both are in game
        assert manager.is_player_in_game("Alice")
        assert manager.is_player_in_game("Bob")

    def test_start_single_player_game_player_already_in_game(self):
        # Test that starting single player game fails if player already in game
        manager = GameStateManager()
        manager.start_single_player_game("Alice")

        with pytest.raises(ValueError, match="Player Alice is already in a game"):
            manager.start_single_player_game("Alice")

    def test_start_multiplayer_game_player1_already_in_game(self):
        # Test that starting multiplayer game fails if player1 already in game
        manager = GameStateManager()
        manager.start_single_player_game("Alice")

        with pytest.raises(ValueError, match="Player Alice is already in a game"):
            manager.start_multiplayer_game("Alice", "Bob")

    def test_start_multiplayer_game_player2_already_in_game(self):
        # Test that starting multiplayer game fails if player2 already in game
        manager = GameStateManager()
        manager.start_single_player_game("Bob")

        with pytest.raises(ValueError, match="Player Bob is already in a game"):
            manager.start_multiplayer_game("Alice", "Bob")

    def test_get_game_state_existing_player(self):
        # Test getting game state for existing player
        manager = GameStateManager()
        original_state = manager.start_single_player_game("Alice")

        retrieved_state = manager.get_game_state("Alice")

        assert retrieved_state is not None
        assert retrieved_state == original_state

    def test_get_game_state_nonexistent_player(self):
        # Test getting game state for nonexistent player
        manager = GameStateManager()

        game_state = manager.get_game_state("NonExistent")

        assert game_state is None

    def test_is_player_in_game_true(self):
        # Test checking if player is in game (true case)
        manager = GameStateManager()
        manager.start_single_player_game("Alice")

        assert manager.is_player_in_game("Alice") is True

    def test_is_player_in_game_false(self):
        # Test checking if player is in game (false case)
        manager = GameStateManager()

        assert manager.is_player_in_game("Alice") is False

    def test_end_single_player_game(self):
        # Test ending a single player game
        manager = GameStateManager()
        manager.start_single_player_game("Alice")

        opponent = manager.end_game("Alice")

        assert opponent is None  # No opponent in single player
        assert not manager.is_player_in_game("Alice")
        assert manager.get_game_state("Alice") is None

    def test_end_multiplayer_game(self):
        # Test ending a multiplayer game
        manager = GameStateManager()
        manager.start_multiplayer_game("Alice", "Bob")

        opponent = manager.end_game("Alice")

        assert opponent == "Bob"
        assert not manager.is_player_in_game("Alice")
        assert not manager.is_player_in_game("Bob")
        assert manager.get_game_state("Alice") is None
        assert manager.get_game_state("Bob") is None

    def test_end_game_nonexistent_player(self):
        # Test ending game for nonexistent player
        manager = GameStateManager()

        opponent = manager.end_game("NonExistent")

        assert opponent is None

    def test_clear_all_games(self):
        # Test clearing all games
        manager = GameStateManager()
        manager.start_single_player_game("Alice")
        manager.start_multiplayer_game("Bob", "Charlie")

        # Verify games exist
        assert manager.is_player_in_game("Alice")
        assert manager.is_player_in_game("Bob")
        assert manager.is_player_in_game("Charlie")

        manager.clear_all_games()

        # Verify all games cleared
        assert not manager.is_player_in_game("Alice")
        assert not manager.is_player_in_game("Bob")
        assert not manager.is_player_in_game("Charlie")

    def test_multiple_single_player_games(self):
        # Test managing multiple single player games
        manager = GameStateManager()

        manager.start_single_player_game("Alice")
        manager.start_single_player_game("Bob")
        manager.start_single_player_game("Charlie")

        assert manager.is_player_in_game("Alice")
        assert manager.is_player_in_game("Bob")
        assert manager.is_player_in_game("Charlie")

        # Verify each has correct game state
        alice_state = manager.get_game_state("Alice")
        bob_state = manager.get_game_state("Bob")
        charlie_state = manager.get_game_state("Charlie")

        assert alice_state is not None
        assert bob_state is not None
        assert charlie_state is not None
        assert alice_state.game_mode == GameMode.SINGLE_PLAYER
        assert bob_state.game_mode == GameMode.SINGLE_PLAYER
        assert charlie_state.game_mode == GameMode.SINGLE_PLAYER

    def test_multiple_multiplayer_games(self):
        # Test managing multiple multiplayer games
        manager = GameStateManager()

        manager.start_multiplayer_game("Alice", "Bob")
        manager.start_multiplayer_game("Charlie", "Diana")

        # Verify all players are in games
        assert manager.is_player_in_game("Alice")
        assert manager.is_player_in_game("Bob")
        assert manager.is_player_in_game("Charlie")
        assert manager.is_player_in_game("Diana")

        # Verify correct opponent mappings
        alice_state = manager.get_game_state("Alice")
        bob_state = manager.get_game_state("Bob")
        charlie_state = manager.get_game_state("Charlie")
        diana_state = manager.get_game_state("Diana")

        assert alice_state is not None
        assert bob_state is not None
        assert charlie_state is not None
        assert diana_state is not None
        assert alice_state.opponent_name == "Bob"
        assert bob_state.opponent_name == "Alice"
        assert charlie_state.opponent_name == "Diana"
        assert diana_state.opponent_name == "Charlie"

    def test_mixed_single_and_multiplayer_games(self):
        # Test managing mix of single and multiplayer games
        manager = GameStateManager()

        manager.start_single_player_game("Solo")
        manager.start_multiplayer_game("Alice", "Bob")

        # Verify correct game modes
        solo_state = manager.get_game_state("Solo")
        alice_state = manager.get_game_state("Alice")
        bob_state = manager.get_game_state("Bob")

        assert solo_state is not None
        assert alice_state is not None
        assert bob_state is not None
        assert solo_state.game_mode == GameMode.SINGLE_PLAYER
        assert alice_state.game_mode == GameMode.MULTIPLAYER
        assert bob_state.game_mode == GameMode.MULTIPLAYER

        assert solo_state.opponent_name is None
        assert alice_state.opponent_name == "Bob"
        assert bob_state.opponent_name == "Alice"


class TestGameModeEnum:
    """Unit tests for GameMode enumeration"""

    def test_game_mode_values(self):
        # Test that GameMode has expected values
        assert GameMode.SINGLE_PLAYER == "Single Player"
        assert GameMode.MULTIPLAYER == "Multiplayer"

    def test_game_mode_enum_members(self):
        # Test that GameMode has expected members
        expected_modes = {GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER}
        actual_modes = {mode for mode in GameMode}
        assert expected_modes == actual_modes

    def test_game_mode_string_comparison(self):
        # Test that GameMode can be compared to strings
        assert GameMode.SINGLE_PLAYER == "Single Player"
        assert GameMode.MULTIPLAYER == "Multiplayer"
        assert GameMode.SINGLE_PLAYER != "Multiplayer"
        assert GameMode.MULTIPLAYER != "Single Player"


class TestGameStateIntegration:
    """Integration tests between GameState and GameStateManager"""

    def test_game_state_manager_produces_valid_game_states(self):
        # Test that GameStateManager always produces valid GameState objects
        manager = GameStateManager()

        # Test single player
        single_state = manager.start_single_player_game("Alice")
        assert isinstance(single_state, GameState)
        # Should not raise validation errors

        # Test multiplayer
        multi_state1, multi_state2 = manager.start_multiplayer_game("Bob", "Charlie")
        assert isinstance(multi_state1, GameState)
        assert isinstance(multi_state2, GameState)
        # Should not raise validation errors

    def test_game_state_manager_consistency_with_game_state_validation(self):
        # Test that GameStateManager respects GameState validation rules
        manager = GameStateManager()

        # Single player game should have no opponent
        single_state = manager.start_single_player_game("Alice")
        assert single_state.opponent_name is None

        # Multiplayer game should have opponents
        multi_state1, multi_state2 = manager.start_multiplayer_game("Bob", "Charlie")
        assert multi_state1.opponent_name is not None
        assert multi_state2.opponent_name is not None
        assert multi_state1.opponent_name == "Charlie"
        assert multi_state2.opponent_name == "Bob"
