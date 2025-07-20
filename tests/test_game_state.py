import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
from game.models import Coordinate, ShipType, Direction
from game.game_state import GameState, GamePhase, GameResult, RoundResult
import json


class TestGameState:
    def test_game_state_creation(self):
        game = GameState("Alice", "Bob")
        
        assert game.player1.name == "Alice"
        assert game.player2.name == "Bob"
        assert not game.player1.is_computer
        assert not game.player2.is_computer
        assert game.current_round == 0
        assert game.phase == GamePhase.SETUP
        assert game.result is None
        assert game.winner is None
        assert len(game.round_history) == 0
    
    def test_game_state_with_computer(self):
        game = GameState("Human", "Computer", player2_is_computer=True)
        
        assert game.player2.is_computer
        assert not game.player1.is_computer
    
    def test_start_game_without_ships(self):
        game = GameState("Alice", "Bob")
        
        result = game.start_game()
        assert result is False
        assert game.phase == GamePhase.SETUP
    
    def test_start_game_with_ships(self):
        game = GameState("Alice", "Bob")
        
        # Place all ships for both players
        self._place_all_ships(game.player1)
        self._place_all_ships(game.player2)
        
        result = game.start_game()
        assert result is True
        assert game.phase == GamePhase.PLAYING
        assert game.current_round == 1
    
    def test_submit_shots_game_not_playing(self):
        game = GameState("Alice", "Bob")
        
        with pytest.raises(ValueError, match="not in playing phase"):
            game.submit_shots("Alice", [Coordinate(0, 0)])
    
    def test_submit_shots_invalid_player(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        with pytest.raises(ValueError, match="Player Charlie not found"):
            game.submit_shots("Charlie", [Coordinate(0, 0)])
    
    def test_submit_shots_wrong_count(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        # Alice has 6 shots available (2+1+1+1+1), but trying to fire 2
        with pytest.raises(ValueError, match="Must fire exactly 6 shots"):
            game.submit_shots("Alice", [Coordinate(0, 0), Coordinate(1, 1)])
    
    def test_submit_shots_duplicate_position(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        # Submit valid shots first - fire at empty areas to avoid hitting any ships
        alice_shots = [Coordinate(9, i) for i in range(6)]  # Row 9 should be empty
        game.submit_shots("Alice", alice_shots)
        
        # Start next round - fire at different empty areas
        bob_shots = [Coordinate(9, i) for i in range(4)] + [Coordinate(5, i) for i in range(2)]
        game.submit_shots("Bob", bob_shots)
        
        # Try to fire at same position again in next round (should still have 6 shots since no hits)
        alice_shots_round2 = [Coordinate(9, 0)] + [Coordinate(7, i) for i in range(5)]
        with pytest.raises(ValueError, match="Already fired at"):
            game.submit_shots("Alice", alice_shots_round2)
    
    def test_submit_shots_single_player(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        alice_shots = [Coordinate(5, i) for i in range(6)]
        result = game.submit_shots("Alice", alice_shots)
        
        assert result is True
        assert game.player1_shots_submitted
        assert not game.player2_shots_submitted
        assert game.current_round == 1  # Round not processed yet
    
    def test_submit_shots_both_players(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        alice_shots = [Coordinate(5, i) for i in range(6)]
        bob_shots = [Coordinate(6, i) for i in range(6)]
        
        game.submit_shots("Alice", alice_shots)
        game.submit_shots("Bob", bob_shots)
        
        # Round should be processed
        assert game.current_round == 2
        assert not game.player1_shots_submitted
        assert not game.player2_shots_submitted
        assert len(game.round_history) == 1
    
    def test_process_round_with_hits(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        # Alice fires at Bob's destroyer position (at 8,0 based on _setup_game placement)
        alice_shots = [Coordinate(8, 0)] + [Coordinate(5, i) for i in range(5)]
        # Bob fires away from Alice's ships
        bob_shots = [Coordinate(9, i) for i in range(6)]
        
        game.submit_shots("Alice", alice_shots)
        game.submit_shots("Bob", bob_shots)
        
        # Check round history
        assert len(game.round_history) == 1
        round_result = game.round_history[0]
        assert round_result.round_number == 1
        assert len(round_result.player1_shots) == 6
        assert len(round_result.player2_shots) == 6
        
        # Alice should have hit Bob's destroyer
        assert ShipType.DESTROYER in round_result.player1_hits
        assert round_result.player1_hits[ShipType.DESTROYER] == 1
    
    def test_game_end_player1_wins(self):
        game = GameState("Alice", "Bob")
        self._setup_minimal_game(game)  # Each player has only destroyer
        
        # Round 1: Alice hits, Bob misses
        alice_shots = [Coordinate(0, 0)]  # Hit Bob's destroyer
        bob_shots = [Coordinate(8, 8)]    # Miss Alice's destroyer
        
        game.submit_shots("Alice", alice_shots)
        game.submit_shots("Bob", bob_shots)
        
        # Round 2: Alice hits again to sink destroyer, Bob still misses
        alice_shots_round2 = [Coordinate(0, 1)]  # Sink Bob's destroyer
        bob_shots_round2 = [Coordinate(8, 9)]    # Miss Alice's destroyer
        
        game.submit_shots("Alice", alice_shots_round2)
        game.submit_shots("Bob", bob_shots_round2)
        
        assert game.phase == GamePhase.FINISHED
        assert game.result == GameResult.PLAYER1_WINS
        assert game.winner == game.player1
    
    def test_game_end_draw(self):
        game = GameState("Alice", "Bob")
        self._setup_minimal_game(game)  # Each player has only destroyer
        
        # Round 1: Both players hit each other
        alice_shots = [Coordinate(0, 0)]  # Hit Bob's destroyer
        bob_shots = [Coordinate(2, 0)]    # Hit Alice's destroyer
        
        game.submit_shots("Alice", alice_shots)
        game.submit_shots("Bob", bob_shots)
        
        # Round 2: Both players sink each other's destroyers in same round
        alice_shots_round2 = [Coordinate(0, 1)]  # Sink Bob's destroyer
        bob_shots_round2 = [Coordinate(2, 1)]    # Sink Alice's destroyer
        
        game.submit_shots("Alice", alice_shots_round2)
        game.submit_shots("Bob", bob_shots_round2)
        
        assert game.phase == GamePhase.FINISHED
        assert game.result == GameResult.DRAW
        assert game.winner is None
    
    def test_abandon_game(self):
        game = GameState("Alice", "Bob")
        
        game.abandon_game()
        
        assert game.phase == GamePhase.ABANDONED
        assert game.result == GameResult.ABANDONED
    
    def test_get_player_by_name(self):
        game = GameState("Alice", "Bob")
        
        alice = game.get_player_by_name("Alice")
        bob = game.get_player_by_name("Bob")
        nobody = game.get_player_by_name("Charlie")
        
        assert alice == game.player1
        assert bob == game.player2
        assert nobody is None
    
    def test_get_opponent(self):
        game = GameState("Alice", "Bob")
        
        alice_opponent = game.get_opponent(game.player1)
        bob_opponent = game.get_opponent(game.player2)
        
        assert alice_opponent == game.player2
        assert bob_opponent == game.player1
    
    def test_is_player_turn_complete(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        assert not game.is_player_turn_complete("Alice")
        assert not game.is_player_turn_complete("Bob")
        
        # Alice submits shots
        alice_shots = [Coordinate(5, i) for i in range(6)]
        game.submit_shots("Alice", alice_shots)
        
        assert game.is_player_turn_complete("Alice")
        assert not game.is_player_turn_complete("Bob")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    def test_save_game(self, mock_json_dump, mock_mkdir, mock_file):
        game = GameState("Alice", "Bob")
        
        game.save_game()
        
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
    
    def test_to_dict(self):
        game = GameState("Alice", "Bob")
        self._setup_minimal_game(game)
        
        # Add a round of gameplay (1 shot each since destroyers only)
        alice_shots = [Coordinate(5, 5)]
        bob_shots = [Coordinate(7, 7)]
        game.submit_shots("Alice", alice_shots)
        game.submit_shots("Bob", bob_shots)
        
        game_dict = game.to_dict()
        
        assert game_dict["player1_name"] == "Alice"
        assert game_dict["player2_name"] == "Bob"
        assert game_dict["current_round"] == 2
        assert game_dict["phase"] == GamePhase.PLAYING.value
        assert len(game_dict["round_history"]) == 1
    
    def test_double_shot_submission_error(self):
        game = GameState("Alice", "Bob")
        self._setup_game(game)
        
        alice_shots = [Coordinate(5, i) for i in range(6)]
        game.submit_shots("Alice", alice_shots)
        
        # Try to submit again
        with pytest.raises(ValueError, match="already submitted shots"):
            game.submit_shots("Alice", alice_shots)
    
    def test_ship_sinking_detection(self):
        game = GameState("Alice", "Bob")
        self._setup_minimal_game(game)
        
        # Hit destroyer once (only 1 shot available per player)
        alice_shots = [Coordinate(0, 0)]
        bob_shots = [Coordinate(7, 7)]
        game.submit_shots("Alice", alice_shots)
        game.submit_shots("Bob", bob_shots)
        
        # Destroyer should not be sunk yet
        assert ShipType.DESTROYER not in game.player1.opponent_ships_sunk
        
        # Hit destroyer second time to sink it
        alice_shots_round2 = [Coordinate(0, 1)]
        bob_shots_round2 = [Coordinate(7, 8)]
        game.submit_shots("Alice", alice_shots_round2)
        game.submit_shots("Bob", bob_shots_round2)
        
        # Now destroyer should be sunk
        assert ShipType.DESTROYER in game.player1.opponent_ships_sunk
        
        # Check round history records the sinking
        round2_result = game.round_history[1]
        assert len(round2_result.ships_sunk_this_round) == 1
        assert round2_result.ships_sunk_this_round[0] == ("Bob", ShipType.DESTROYER)
    
    def test_start_game_with_computer_player_auto_place(self):
        """Test that computer players automatically place ships when game starts"""
        game = GameState("Alice", "Computer", player2_is_computer=True)
        
        # Only place ships for human player
        self._place_all_ships(game.player1)
        
        # Computer player should not have ships placed yet
        assert not game.player2.has_all_ships_placed()
        
        # Starting game should auto-place computer ships
        result = game.start_game()
        
        assert result is True
        assert game.player2.has_all_ships_placed()
        assert len(game.player2.board.ships) == 5
        assert game.phase == GamePhase.PLAYING
    
    def test_start_game_computer_placement_failure_handling(self):
        """Test handling when computer ship placement fails"""
        from unittest.mock import patch
        
        game = GameState("Alice", "Computer", player2_is_computer=True)
        self._place_all_ships(game.player1)
        
        # Mock the auto_place_ships to return False (placement failure)
        with patch.object(game.player2, 'auto_place_ships', return_value=False):
            result = game.start_game()
            
            assert result is False
            assert game.phase == GamePhase.SETUP
    
    # Helper methods
    def _place_all_ships(self, player):
        """Place all 5 ships for a player"""
        player.place_ship(ShipType.CARRIER, Coordinate(0, 0), Direction.HORIZONTAL)
        player.place_ship(ShipType.BATTLESHIP, Coordinate(2, 0), Direction.HORIZONTAL)
        player.place_ship(ShipType.CRUISER, Coordinate(4, 0), Direction.HORIZONTAL)
        player.place_ship(ShipType.SUBMARINE, Coordinate(6, 0), Direction.HORIZONTAL)
        player.place_ship(ShipType.DESTROYER, Coordinate(8, 0), Direction.HORIZONTAL)
    
    def _setup_game(self, game):
        """Set up a complete game ready for play"""
        self._place_all_ships(game.player1)
        self._place_all_ships(game.player2)
        game.start_game()
    
    def _setup_minimal_game(self, game):
        """Set up game with minimal ships (just destroyers) - bypass normal start requirements for testing"""
        game.player1.place_ship(ShipType.DESTROYER, Coordinate(2, 0), Direction.HORIZONTAL)
        game.player2.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
        # Manually set game to playing state for testing
        game.phase = GamePhase.PLAYING
        game.current_round = 1


class TestRoundResult:
    def test_round_result_creation(self):
        round_result = RoundResult(
            round_number=1,
            player1_shots=[Coordinate(0, 0)],
            player2_shots=[Coordinate(1, 1)],
            player1_hits={ShipType.DESTROYER: 1},
            player2_hits={},
            ships_sunk_this_round=[("Player2", ShipType.DESTROYER)]
        )
        
        assert round_result.round_number == 1
        assert len(round_result.player1_shots) == 1
        assert len(round_result.player2_shots) == 1
        assert ShipType.DESTROYER in round_result.player1_hits
        assert len(round_result.ships_sunk_this_round) == 1