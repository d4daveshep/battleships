"""
Unit tests for FastAPI web interface.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from web.app import app, games, GameManager
from game.models import ShipType, Direction, Coordinate
from game.game_state import GameState, GamePhase


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Mock session data"""
    return {"game_id": "test-game-123"}


@pytest.fixture
def sample_game():
    """Sample game state for testing"""
    game = GameState("Alice", "Bob", player2_is_computer=True)
    return game


class TestIndexEndpoint:
    """Test the main index endpoint"""
    
    def test_index_no_game(self, client):
        """Test index page with no active game"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Start New Game" in response.text
    
    def test_index_with_game(self, client, sample_game):
        """Test index page with active game"""
        with client as test_client:
            # Mock session and game
            with patch.object(GameManager, 'get_game', return_value=sample_game):
                response = test_client.get("/")
                assert response.status_code == 200
                assert "Ship Placement" in response.text


class TestGameManagement:
    """Test game creation and management endpoints"""
    
    def test_create_new_game_vs_computer(self, client):
        """Test creating new game against computer"""
        response = client.post("/game/new", data={
            "player1_name": "Alice",
            "vs_computer": "true"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "game_id" in data
    
    def test_create_new_game_vs_human(self, client):
        """Test creating new game against human"""
        response = client.post("/game/new", data={
            "player1_name": "Alice",
            "player2_name": "Bob",
            "vs_computer": "false"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_game_status_no_game(self, client):
        """Test game status with no active game"""
        response = client.get("/game/status")
        assert response.status_code == 404
    
    def test_game_status_with_game(self, client, sample_game):
        """Test game status with active game"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/status")
            assert response.status_code == 200
            data = response.json()
            assert data["phase"] == "setup"
            assert data["current_round"] == 0
            assert data["player1"]["name"] == "Alice"
            assert data["player2"]["name"] == "Bob"
    
    def test_delete_game(self, client):
        """Test game deletion"""
        response = client.delete("/game")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestBoardEndpoints:
    """Test board-related endpoints"""
    
    def test_get_board_no_game(self, client):
        """Test getting board with no active game"""
        response = client.get("/game/board/Alice")
        assert response.status_code == 404
    
    def test_get_board_invalid_player(self, client, sample_game):
        """Test getting board for invalid player"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/board/Charlie")
            assert response.status_code == 404
    
    def test_get_board_valid_player(self, client, sample_game):
        """Test getting board for valid player"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/board/Alice")
            assert response.status_code == 200
            assert "game-board" in response.text
    
    def test_get_shots_fired_board(self, client, sample_game):
        """Test getting shots fired board"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/shots-fired/Alice")
            assert response.status_code == 200
            assert "shots-board" in response.text


class TestShipPlacement:
    """Test ship placement endpoints"""
    
    def test_place_ship_no_game(self, client):
        """Test placing ship with no active game"""
        response = client.post("/game/place-ship", data={
            "ship_type": "DESTROYER",
            "row": "0",
            "col": "0", 
            "direction": "HORIZONTAL"
        })
        assert response.status_code == 404
    
    def test_place_ship_valid(self, client, sample_game):
        """Test valid ship placement"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.post("/game/place-ship", data={
                "ship_type": "DESTROYER",
                "row": "0",
                "col": "0",
                "direction": "HORIZONTAL"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_place_ship_invalid_type(self, client, sample_game):
        """Test placing ship with invalid type"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.post("/game/place-ship", data={
                "ship_type": "INVALID",
                "row": "0",
                "col": "0",
                "direction": "HORIZONTAL"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Invalid parameters" in data["message"]
    
    def test_place_ship_invalid_position(self, client, sample_game):
        """Test placing ship at invalid position"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            # First place a ship
            sample_game.player1.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
            
            # Try to place another ship overlapping
            response = client.post("/game/place-ship", data={
                "ship_type": "CRUISER",
                "row": "0",
                "col": "0",
                "direction": "HORIZONTAL"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Invalid ship placement" in data["message"]
    
    def test_auto_place_ships(self, client, sample_game):
        """Test auto-placing ships"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            with patch('web.app.Player') as mock_player_class:
                # Mock the temporary player for auto-placement
                mock_temp_player = MagicMock()
                mock_temp_player.auto_place_ships.return_value = True
                mock_temp_player.board.ships = []
                mock_player_class.return_value = mock_temp_player
                
                response = client.post("/game/auto-place-ships")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
    
    def test_auto_place_ships_failure(self, client, sample_game):
        """Test auto-place ships failure"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            with patch('web.app.Player') as mock_player_class:
                # Mock failure
                mock_temp_player = MagicMock()
                mock_temp_player.auto_place_ships.return_value = False
                mock_player_class.return_value = mock_temp_player
                
                response = client.post("/game/auto-place-ships")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"


class TestShooting:
    """Test shooting phase endpoints"""
    
    def setup_playing_game(self, sample_game):
        """Helper to set up a game in playing phase"""
        # Place all ships for both players
        ships_and_positions = [
            (ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL),
            (ShipType.CRUISER, Coordinate(2, 0), Direction.HORIZONTAL),
            (ShipType.SUBMARINE, Coordinate(4, 0), Direction.HORIZONTAL),
            (ShipType.BATTLESHIP, Coordinate(6, 0), Direction.HORIZONTAL),
            (ShipType.CARRIER, Coordinate(8, 0), Direction.HORIZONTAL),
        ]
        
        for ship_type, coord, direction in ships_and_positions:
            sample_game.player1.place_ship(ship_type, coord, direction)
            sample_game.player2.place_ship(ship_type, Coordinate(coord.row, coord.col + 5), direction)
        
        sample_game.start_game()
        return sample_game
    
    def test_submit_shots_no_game(self, client):
        """Test submitting shots with no active game"""
        response = client.post("/game/submit-shots", data={
            "shots": "A1,B2"
        })
        assert response.status_code == 404
    
    def test_submit_shots_valid(self, client, sample_game):
        """Test valid shot submission"""
        game = self.setup_playing_game(sample_game)
        
        with patch.object(GameManager, 'get_game', return_value=game):
            # Submit correct number of shots (should be 6 total)
            expected_shots = game.player1.get_available_shots()
            shots = ",".join([f"{chr(65+i)}{i+6}" for i in range(expected_shots)])
            
            response = client.post("/game/submit-shots", data={
                "shots": shots
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_submit_shots_invalid_format(self, client, sample_game):
        """Test submitting shots with invalid format"""
        game = self.setup_playing_game(sample_game)
        
        with patch.object(GameManager, 'get_game', return_value=game):
            response = client.post("/game/submit-shots", data={
                "shots": "INVALID"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Invalid shot format" in data["message"]
    
    def test_submit_shots_with_computer_opponent(self, client, sample_game):
        """Test shot submission triggers computer response"""
        game = self.setup_playing_game(sample_game)
        
        with patch.object(GameManager, 'get_game', return_value=game):
            with patch('random.sample') as mock_random:
                # Mock computer shots (same number as player)
                expected_shots = game.player1.get_available_shots()
                computer_shots = [Coordinate(i, 0) for i in range(expected_shots)]
                mock_random.return_value = computer_shots
                
                # Submit correct number of player shots
                player_shots = ",".join([f"{chr(65+i)}{i+6}" for i in range(expected_shots)])
                
                response = client.post("/game/submit-shots", data={
                    "shots": player_shots
                })
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"


class TestRoundResults:
    """Test round results endpoint"""
    
    def test_round_results_no_game(self, client):
        """Test getting round results with no active game"""
        response = client.get("/game/round-results")
        assert response.status_code == 404
    
    def test_round_results_no_rounds(self, client, sample_game):
        """Test getting round results with no rounds played"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/round-results")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "no_rounds"
    
    def test_round_results_with_rounds(self, client, sample_game):
        """Test getting round results with played rounds"""
        # Set up game with some round history
        game = sample_game
        game.current_round = 1
        
        # Mock round history
        from game.game_state import RoundResult
        mock_round = RoundResult(
            round_number=1,
            player1_shots=[Coordinate(0, 0)],
            player2_shots=[Coordinate(1, 1)],
            player1_hits={},
            player2_hits={},
            ships_sunk_this_round=[]
        )
        game.round_history = [mock_round]
        
        with patch.object(GameManager, 'get_game', return_value=game):
            response = client.get("/game/round-results")
            assert response.status_code == 200
            assert "Round 1 Results" in response.text


class TestShipPlacementForm:
    """Test ship placement form endpoint"""
    
    def test_ship_placement_form_no_game(self, client):
        """Test getting ship placement form with no active game"""
        response = client.get("/game/ship-placement")
        assert response.status_code == 404
    
    def test_ship_placement_form_with_ships_to_place(self, client, sample_game):
        """Test getting ship placement form when ships remain"""
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/ship-placement")
            assert response.status_code == 200
            assert "Place" in response.text
            assert "ship-placement-form" in response.text
    
    def test_ship_placement_form_all_placed(self, client, sample_game):
        """Test getting ship placement form when all ships are placed"""
        # Place all ships
        ships_and_positions = [
            (ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL),
            (ShipType.CRUISER, Coordinate(2, 0), Direction.HORIZONTAL),
            (ShipType.SUBMARINE, Coordinate(4, 0), Direction.HORIZONTAL),
            (ShipType.BATTLESHIP, Coordinate(6, 0), Direction.HORIZONTAL),
            (ShipType.CARRIER, Coordinate(8, 0), Direction.HORIZONTAL),
        ]
        
        for ship_type, coord, direction in ships_and_positions:
            sample_game.player1.place_ship(ship_type, coord, direction)
        
        with patch.object(GameManager, 'get_game', return_value=sample_game):
            response = client.get("/game/ship-placement")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "all_placed"


class TestGameManager:
    """Test GameManager utility class"""
    
    def test_get_game_id_new_session(self):
        """Test getting game ID for new session"""
        mock_request = MagicMock()
        mock_request.session = {}
        
        game_id = GameManager.get_game_id(mock_request)
        assert game_id
        assert "game_id" in mock_request.session
        assert mock_request.session["game_id"] == game_id
    
    def test_get_game_id_existing_session(self):
        """Test getting game ID for existing session"""
        mock_request = MagicMock()
        mock_request.session = {"game_id": "existing-id"}
        
        game_id = GameManager.get_game_id(mock_request)
        assert game_id == "existing-id"
    
    def test_get_game_exists(self):
        """Test getting existing game"""
        mock_request = MagicMock()
        mock_request.session = {"game_id": "test-id"}
        
        test_game = GameState("Alice", "Bob")
        games["test-id"] = test_game
        
        game = GameManager.get_game(mock_request)
        assert game is test_game
        
        # Cleanup
        del games["test-id"]
    
    def test_get_game_not_exists(self):
        """Test getting non-existent game"""
        mock_request = MagicMock()
        mock_request.session = {"game_id": "nonexistent-id"}
        
        game = GameManager.get_game(mock_request)
        assert game is None
    
    def test_create_game(self):
        """Test creating new game"""
        mock_request = MagicMock()
        mock_request.session = {}
        
        game = GameManager.create_game(mock_request, "Alice", "Bob", True)
        
        assert game.player1.name == "Alice"
        assert game.player2.name == "Bob"
        assert game.player2.is_computer is True
        
        game_id = mock_request.session["game_id"]
        assert games[game_id] is game
        
        # Cleanup
        del games[game_id]
    
    def test_delete_game(self):
        """Test deleting game"""
        mock_request = MagicMock()
        mock_request.session = {"game_id": "test-delete-id"}
        
        test_game = GameState("Alice", "Bob")
        games["test-delete-id"] = test_game
        
        GameManager.delete_game(mock_request)
        
        assert "test-delete-id" not in games
        assert "game_id" not in mock_request.session
    
    def test_delete_game_not_exists(self):
        """Test deleting non-existent game"""
        mock_request = MagicMock()
        mock_request.session = {"game_id": "nonexistent-delete-id"}
        
        # Should not raise error
        GameManager.delete_game(mock_request)
        assert "game_id" not in mock_request.session


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async behavior of endpoints"""
    
    async def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import asyncio
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                asyncio.to_thread(
                    client.post, "/game/new", 
                    data={"player1_name": f"Player{i}", "vs_computer": "true"}
                )
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"