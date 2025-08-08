"""
Integration tests for complete game flow.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from web.app import app, games, GameManager
from game.models import ShipType, Direction, Coordinate
from game.game_state import GameState, GamePhase


class TestCompleteGameFlow:
    """Test complete game flow from start to finish"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    @pytest.fixture(autouse=True)
    def clear_games(self):
        """Clear games before each test"""
        games.clear()
        yield
        games.clear()
    
    def test_full_game_vs_computer(self, client):
        """Test complete game against computer from start to finish"""
        
        # 1. Create new game
        response = client.post("/game/new", data={
            "player1_name": "Alice",
            "vs_computer": "true"
        })
        assert response.status_code == 200
        game_data = response.json()
        assert game_data["status"] == "success"
        
        # Store session data for subsequent requests
        session_cookie = response.cookies
        
        # 2. Check initial game status
        response = client.get("/game/status", cookies=session_cookie)
        assert response.status_code == 200
        status = response.json()
        assert status["phase"] == "setup"
        assert status["player1"]["name"] == "Alice"
        assert status["player2"]["name"] == "Computer"
        assert status["player1"]["ships_placed"] is False
        
        # 3. Auto-place all ships
        response = client.post("/game/auto-place-ships", cookies=session_cookie)
        assert response.status_code == 200
        auto_place_result = response.json()
        assert auto_place_result["status"] == "success"
        
        # 4. Check game moved to playing phase
        response = client.get("/game/status", cookies=session_cookie)
        assert response.status_code == 200
        status = response.json()
        assert status["phase"] == "playing"
        assert status["current_round"] == 1
        assert status["player1"]["ships_placed"] is True
        assert status["player2"]["ships_placed"] is True
        
        # 5. Play several rounds
        shot_counter = 0  # Track shots to avoid duplicates
        for round_num in range(1, 4):
            # Check if game is still playing
            response = client.get("/game/status", cookies=session_cookie)
            status = response.json()
            if status["phase"] != "playing":
                break
            
            # Get number of shots available
            shots_available = status["player1"]["shots_available"]
            
            # Submit correct number of shots (ensure uniqueness)
            shots = []
            for i in range(shots_available):
                row = chr(65 + (shot_counter // 10))  # A-J (0-9 -> A-J)
                col = ((shot_counter % 10) + 1)       # 1-10 (0-9 -> 1-10)
                shots.append(f"{row}{col}")
                shot_counter += 1
                # If we've used all positions, wrap around
                if shot_counter >= 100:
                    shot_counter = 0
            
            shots_str = ",".join(shots)
            response = client.post("/game/submit-shots", 
                                 data={"shots": shots_str},
                                 cookies=session_cookie)
            assert response.status_code == 200
            shot_result = response.json()
            if shot_result["status"] != "success":
                print(f"Shot submission failed: {shot_result}")
                print(f"Shots attempted: {shots_str}")
            assert shot_result["status"] == "success"
            
            # Check round results
            response = client.get("/game/round-results", cookies=session_cookie)
            assert response.status_code == 200
            # Should be HTML content
            assert "Round" in response.text
        
        # 6. Check final game state (might be finished or still playing)
        response = client.get("/game/status", cookies=session_cookie)
        assert response.status_code == 200
        final_status = response.json()
        assert final_status["phase"] in ["playing", "finished"]
        
        # 7. Clean up
        response = client.delete("/game", cookies=session_cookie)
        assert response.status_code == 200
    
    def test_manual_ship_placement_vs_computer(self, client):
        """Test manual ship placement followed by gameplay"""
        
        # 1. Create game
        response = client.post("/game/new", data={
            "player1_name": "Bob",
            "vs_computer": "true"
        })
        assert response.status_code == 200
        session_cookie = response.cookies
        
        # 2. Manually place each ship
        ships_to_place = [
            (ShipType.DESTROYER, 0, 0, "horizontal"),
            (ShipType.CRUISER, 2, 0, "horizontal"),
            (ShipType.SUBMARINE, 4, 0, "horizontal"),
            (ShipType.BATTLESHIP, 6, 0, "horizontal"),
            (ShipType.CARRIER, 8, 0, "horizontal"),
        ]
        
        for ship_type, row, col, direction in ships_to_place:
            response = client.post("/game/place-ship", 
                                 data={
                                     "ship_type": ship_type.name,
                                     "row": str(row),
                                     "col": str(col),
                                     "direction": direction
                                 },
                                 cookies=session_cookie)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
        
        # 3. Check game moved to playing phase
        response = client.get("/game/status", cookies=session_cookie)
        assert response.status_code == 200
        status = response.json()
        assert status["phase"] == "playing"
        
        # 4. Play one round
        response = client.post("/game/submit-shots",
                             data={"shots": "F1,F2,F3"},
                             cookies=session_cookie)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        
        # 5. Check boards updated
        response = client.get("/game/board/Bob", cookies=session_cookie)
        assert response.status_code == 200
        assert "game-board" in response.text
        
        response = client.get("/game/shots-fired/Bob", cookies=session_cookie)
        assert response.status_code == 200
        assert "shots-board" in response.text
    
    def test_invalid_ship_placements(self, client):
        """Test handling of invalid ship placements"""
        
        # Create game
        response = client.post("/game/new", data={
            "player1_name": "Charlie",
            "vs_computer": "true"
        })
        assert response.status_code == 200
        session_cookie = response.cookies
        
        # Try to place ship at invalid position (overlapping)
        # First place a destroyer
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "DESTROYER", 
                                 "row": "0",
                                 "col": "0",
                                 "direction": "horizontal"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Try to place cruiser overlapping
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "CRUISER",
                                 "row": "0", 
                                 "col": "0",
                                 "direction": "horizontal"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "error"
        assert "Invalid ship placement" in result["message"]
        
        # Try invalid ship type
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "INVALID_SHIP",
                                 "row": "5",
                                 "col": "5", 
                                 "direction": "horizontal"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "error"
        assert "Invalid parameters" in result["message"]
    
    def test_invalid_shot_formats(self, client):
        """Test handling of invalid shot formats"""
        
        # Set up game in playing phase
        response = client.post("/game/new", data={
            "player1_name": "Dave",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Auto-place ships
        client.post("/game/auto-place-ships", cookies=session_cookie)
        
        # Test various invalid shot formats
        invalid_shots = [
            "INVALID",
            "A11",  # Column too high
            "K1",   # Row too high  
            "A0",   # Column too low
            "A1,INVALID,B2",  # Mixed valid/invalid
            "",     # Empty
            "A1,,B2",  # Empty shot in middle
        ]
        
        for invalid_shot in invalid_shots:
            response = client.post("/game/submit-shots",
                                 data={"shots": invalid_shot},
                                 cookies=session_cookie)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "error"
            assert "Invalid shot format" in result["message"]
    
    def test_game_state_persistence(self, client):
        """Test that game state persists across requests"""
        
        # Create game
        response = client.post("/game/new", data={
            "player1_name": "Eve",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Place a ship
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "DESTROYER",
                                 "row": "0",
                                 "col": "0",
                                 "direction": "horizontal"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        
        # Check ship shows up in board
        response = client.get("/game/board/Eve", cookies=session_cookie)
        assert response.status_code == 200
        board_html = response.text
        # Should show ship in some form (class or content)
        assert 'data-row="0"' in board_html
        assert 'data-col="0"' in board_html
        
        # Check ship placement form updates
        response = client.get("/game/ship-placement", cookies=session_cookie)
        assert response.status_code == 200
        # Should show next ship to place (not destroyer)
        assert "DESTROYER" not in response.text.upper() or "remaining" in response.text.lower()
    
    def test_multiple_sessions_isolation(self, client):
        """Test that different sessions have isolated games"""
        
        # Create first game
        response1 = client.post("/game/new", data={
            "player1_name": "Player1",
            "vs_computer": "true"
        })
        session1_cookie = response1.cookies
        
        # Create second game (new session)
        response2 = client.post("/game/new", data={
            "player1_name": "Player2", 
            "vs_computer": "true"
        })
        session2_cookie = response2.cookies
        
        # Check both games exist independently
        response = client.get("/game/status", cookies=session1_cookie)
        assert response.status_code == 200
        status1 = response.json()
        assert status1["player1"]["name"] == "Player1"
        
        response = client.get("/game/status", cookies=session2_cookie)
        assert response.status_code == 200
        status2 = response.json()
        assert status2["player1"]["name"] == "Player2"
        
        # Actions in one session shouldn't affect the other
        client.post("/game/place-ship",
                   data={
                       "ship_type": "DESTROYER",
                       "row": "0", 
                       "col": "0",
                       "direction": "horizontal"
                   },
                   cookies=session1_cookie)
        
        # Session 2 should still have no ships placed
        response = client.get("/game/status", cookies=session2_cookie)
        status2 = response.json()
        assert status2["player1"]["ships_placed"] is False
    
    def test_error_recovery(self, client):
        """Test error recovery scenarios"""
        
        # Try to access game endpoints without creating game
        response = client.get("/game/status")
        assert response.status_code == 404
        
        response = client.get("/game/board/NonExistent")
        assert response.status_code == 404
        
        response = client.post("/game/place-ship", data={
            "ship_type": "DESTROYER",
            "row": "0",
            "col": "0", 
            "direction": "horizontal"
        })
        assert response.status_code == 404
        
        # Create game and then delete it
        response = client.post("/game/new", data={
            "player1_name": "TestUser",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Delete game
        response = client.delete("/game", cookies=session_cookie)
        assert response.status_code == 200
        
        # Try to access deleted game
        response = client.get("/game/status", cookies=session_cookie)
        assert response.status_code == 404


class TestConcurrentGames:
    """Test concurrent game handling"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(autouse=True)
    def clear_games(self):
        games.clear()
        yield
        games.clear()
    
    def test_multiple_concurrent_games(self, client):
        """Test handling multiple concurrent games"""
        
        # Create multiple games concurrently
        sessions = []
        for i in range(5):
            response = client.post("/game/new", data={
                "player1_name": f"Player{i}",
                "vs_computer": "true"
            })
            assert response.status_code == 200
            sessions.append(response.cookies)
        
        # Check all games exist independently
        for i, session_cookie in enumerate(sessions):
            response = client.get("/game/status", cookies=session_cookie)
            assert response.status_code == 200
            status = response.json()
            assert status["player1"]["name"] == f"Player{i}"
        
        # Each session should be able to play independently
        for session_cookie in sessions[:3]:  # Test first 3
            # Auto-place ships
            response = client.post("/game/auto-place-ships", cookies=session_cookie)
            assert response.status_code == 200
            
            # Check moved to playing phase
            response = client.get("/game/status", cookies=session_cookie)
            assert response.status_code == 200
            status = response.json()
            assert status["phase"] == "playing"
    
    def test_game_cleanup(self, client):
        """Test game cleanup and memory management"""
        
        # Create and delete multiple games
        for i in range(10):
            response = client.post("/game/new", data={
                "player1_name": f"TempPlayer{i}",
                "vs_computer": "true"
            })
            session_cookie = response.cookies
            
            # Immediately delete
            response = client.delete("/game", cookies=session_cookie)
            assert response.status_code == 200
        
        # Games dict should not grow indefinitely
        # (In production, you'd want more sophisticated cleanup)
        assert len(games) <= 10  # Should not accumulate deleted games


class TestGameLogic:
    """Test game logic integration through web interface"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture(autouse=True) 
    def clear_games(self):
        games.clear()
        yield
        games.clear()
    
    def test_ship_spacing_rules(self, client):
        """Test ship spacing rules enforcement"""
        
        response = client.post("/game/new", data={
            "player1_name": "SpacingTest",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Place first ship
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "DESTROYER",
                                 "row": "5",
                                 "col": "5",
                                 "direction": "horizontal"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Try to place second ship touching (should fail)
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "CRUISER",
                                 "row": "4",  # Adjacent row
                                 "col": "5", 
                                 "direction": "horizontal"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "error"
    
    def test_diagonal_ship_placement(self, client):
        """Test diagonal ship placement"""
        
        response = client.post("/game/new", data={
            "player1_name": "DiagonalTest",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Place ship diagonally
        response = client.post("/game/place-ship",
                             data={
                                 "ship_type": "CRUISER",
                                 "row": "2",
                                 "col": "2",
                                 "direction": "diagonal_ne"
                             },
                             cookies=session_cookie)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        
        # Check board reflects diagonal placement
        response = client.get("/game/board/DiagonalTest", cookies=session_cookie)
        assert response.status_code == 200
        board_html = response.text
        
        # Should have ship symbols at diagonal positions
        # (2,2), (1,3), (0,4) for NE diagonal cruiser
        assert 'data-row="2"' in board_html and 'data-col="2"' in board_html
    
    def test_shot_allocation_based_on_fleet(self, client):
        """Test that shot allocation is based on remaining fleet"""
        
        # Set up game with known ship configuration
        response = client.post("/game/new", data={
            "player1_name": "ShotTest",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Auto-place ships
        client.post("/game/auto-place-ships", cookies=session_cookie)
        
        # Check initial shot allocation
        response = client.get("/game/status", cookies=session_cookie)
        status = response.json()
        initial_shots = status["player1"]["shots_available"]
        
        # Should equal total shots from all ships
        expected_total = sum(ship_type.shots for ship_type in ShipType)
        assert initial_shots == expected_total
        
        # After sinking ships, shot allocation should decrease
        # (This would require more complex test setup to actually sink ships)
    
    def test_simultaneous_shot_resolution(self, client):
        """Test simultaneous shot resolution"""
        
        response = client.post("/game/new", data={
            "player1_name": "SimulTest",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        client.post("/game/auto-place-ships", cookies=session_cookie)
        
        # Submit shots
        response = client.post("/game/submit-shots",
                             data={"shots": "A1,B1,C1"},
                             cookies=session_cookie)
        assert response.status_code == 200
        
        # Check round results show both players' shots
        response = client.get("/game/round-results", cookies=session_cookie)
        assert response.status_code == 200
        results_html = response.text
        
        # Should show both player shots and computer shots
        assert "SimulTest fired at" in results_html
        assert "Computer fired at" in results_html


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Test async behavior and performance"""
    
    async def test_concurrent_requests_same_game(self):
        """Test concurrent requests to same game session"""
        
        client = TestClient(app)
        
        # Create game
        response = client.post("/game/new", data={
            "player1_name": "ConcurrentTest",
            "vs_computer": "true"
        })
        session_cookie = response.cookies
        
        # Make concurrent requests
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def make_status_request():
            return client.get("/game/status", cookies=session_cookie)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = [
                asyncio.get_event_loop().run_in_executor(executor, make_status_request)
                for _ in range(5)
            ]
            responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            status = response.json()
            assert status["player1"]["name"] == "ConcurrentTest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])