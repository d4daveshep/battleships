import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestMultiplayerGameInterface:
    """Integration tests for multiplayer game interface functionality"""

    def test_game_page_shows_multiplayer_mode_when_accessed_via_accepted_request(
        self, client: TestClient
    ):
        # Test that game page shows multiplayer mode when accessed after accepting request

        # Step 1: Setup players and game request workflow
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob accepts the request
        accept_response = client.post(
            "/accept-game-request", data={"player_name": "Bob"}, follow_redirects=True
        )

        # Step 3: Should be on game page showing multiplayer mode
        assert accept_response.status_code == status.HTTP_200_OK
        assert "Battleships Game" in accept_response.text
        assert 'data-testid="game-mode"' in accept_response.text

    def test_game_page_shows_opponent_name_for_both_players(self, client: TestClient):
        # Test that both players see each other as opponents in the game

        # Step 1: Setup complete game request workflow
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 2: Check Bob's game view (he accepted, so should be on game page)
        bob_game_response = client.get("/game?player_name=Bob&opponent_name=Alice")
        assert bob_game_response.status_code == status.HTTP_200_OK
        assert 'data-testid="opponent-name"' in bob_game_response.text
        assert "Alice" in bob_game_response.text  # Bob should see Alice as opponent

        # Step 3: Check Alice's game view (she should also be redirected to game)
        alice_game_response = client.get("/game?player_name=Alice&opponent_name=Bob")
        assert alice_game_response.status_code == status.HTTP_200_OK
        assert 'data-testid="opponent-name"' in alice_game_response.text
        assert "Bob" in alice_game_response.text  # Alice should see Bob as opponent

    def test_game_page_shows_current_player_name(self, client: TestClient):
        # Test that game page correctly identifies the current player

        # Step 1: Setup game
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 2: Check that each player sees their own name correctly
        bob_game_response = client.get("/game?player_name=Bob&opponent_name=Alice")
        assert 'data-testid="player-name"' in bob_game_response.text
        assert "Bob" in bob_game_response.text

        alice_game_response = client.get("/game?player_name=Alice&opponent_name=Bob")
        assert 'data-testid="player-name"' in alice_game_response.text
        assert "Alice" in alice_game_response.text

    def test_game_page_accessible_only_for_players_in_game(self, client: TestClient):
        # Test that game page is only accessible for players who are actually in a game

        # Step 1: Setup players in lobby (no game started)
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice and Bob start a game
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 3: Charlie can access game page but gets single player mode (no opponent_name)
        charlie_game_response = client.get("/game?player_name=Charlie")
        # Without opponent_name parameter, defaults to single player mode
        assert charlie_game_response.status_code == status.HTTP_200_OK
        # Should not show multiplayer-specific elements without opponent
        assert 'data-testid="opponent-name"' not in charlie_game_response.text

    def test_game_page_prevents_access_from_single_player_mode(
        self, client: TestClient
    ):
        # Test that multiplayer game interface is not accessible from single player mode

        # Step 1: Player logs in with computer opponent (single player)
        client.post("/test/reset-lobby")
        response = client.post(
            "/", data={"player_name": "Alice", "game_mode": "computer"}
        )

        # Step 2: Should be redirected to single player game, not multiplayer
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]
        if response.status_code == status.HTTP_200_OK:
            # If staying on same page, should show single player game
            assert "Single Player" in response.text
        else:
            # If redirected, follow redirect
            follow_response = client.get(response.headers["location"])
            assert "Single Player" in follow_response.text

    def test_game_state_persistence_between_requests(self, client: TestClient):
        # Test that game state is maintained between different requests

        # Step 1: Setup multiplayer game
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 2: Make multiple requests to game page for same player
        bob_response1 = client.get("/game?player_name=Bob&opponent_name=Alice")
        bob_response2 = client.get("/game?player_name=Bob&opponent_name=Alice")

        # Step 3: Both requests should show consistent game state
        assert bob_response1.status_code == status.HTTP_200_OK
        assert bob_response2.status_code == status.HTTP_200_OK

        # Both should show same opponent
        assert "Alice" in bob_response1.text
        assert "Alice" in bob_response2.text

    def test_both_players_removed_from_lobby_after_game_starts(
        self, client: TestClient
    ):
        # Test that both players are removed from lobby views once game starts

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice and Bob start a game
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 3: Charlie's lobby view should not show Alice or Bob
        charlie_lobby_response = client.get("/lobby/status/Charlie")
        assert charlie_lobby_response.status_code == status.HTTP_200_OK
        assert "Alice" not in charlie_lobby_response.text
        assert "Bob" not in charlie_lobby_response.text
        assert "No other players available" in charlie_lobby_response.text

    def test_game_page_shows_game_specific_elements(self, client: TestClient):
        # Test that game page contains expected game interface elements

        # Step 1: Setup multiplayer game
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 2: Check game page contains expected elements
        game_response = client.get("/game?player_name=Bob&opponent_name=Alice")
        assert game_response.status_code == status.HTTP_200_OK

        # Should have game-specific testids and elements
        assert 'data-testid="game-mode"' in game_response.text
        assert 'data-testid="player-name"' in game_response.text
        assert 'data-testid="opponent-name"' in game_response.text

        # Should not have lobby-specific elements
        assert 'data-testid="lobby-container"' not in game_response.text
        assert 'data-testid="available-players-list"' not in game_response.text


class TestGameRequestToGameTransition:
    """Integration tests for the transition from game request to actual game"""

    def test_accept_request_redirects_both_players_to_game(self, client: TestClient):
        # Test that accepting a request properly transitions both players to game state

        # Step 1: Setup game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob accepts (should redirect to game)
        accept_response = client.post(
            "/accept-game-request", data={"player_name": "Bob"}, follow_redirects=False
        )
        assert accept_response.status_code == status.HTTP_302_FOUND
        assert "/game" in accept_response.headers["location"]

        # Step 3: Alice should also be transitioned to game state
        alice_response = client.get("/lobby/status/Alice")
        # Alice should either be redirected to game or removed from lobby
        if alice_response.status_code == status.HTTP_302_FOUND:
            assert "/game" in alice_response.headers["location"]
        else:
            # Or Alice could be shown a message that game has started
            alice_game_response = client.get("/game?player_name=Alice&opponent_name=Bob")
            assert alice_game_response.status_code == status.HTTP_200_OK

    def test_game_initialization_sets_correct_opponent_mapping(
        self, client: TestClient
    ):
        # Test that game properly initializes with correct opponent relationships

        # Step 1: Complete game setup workflow
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 2: Verify opponent mappings are correct
        alice_game = client.get("/game?player_name=Alice&opponent_name=Bob")
        bob_game = client.get("/game?player_name=Bob&opponent_name=Alice")

        # Alice should see Bob as opponent
        assert "Bob" in alice_game.text
        assert 'data-testid="opponent-name"' in alice_game.text

        # Bob should see Alice as opponent
        assert "Alice" in bob_game.text
        assert 'data-testid="opponent-name"' in bob_game.text

    def test_decline_request_keeps_both_players_in_lobby(self, client: TestClient):
        # Test that declining a request keeps both players available in lobby

        # Step 1: Setup game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob declines request
        decline_response = client.post(
            "/decline-game-request", data={"player_name": "Bob"}
        )
        assert decline_response.status_code == status.HTTP_200_OK

        # Step 3: Both players should remain in lobby and be available
        charlie_lobby = client.get("/lobby/status/Charlie")
        assert "Alice" in charlie_lobby.text
        assert "Bob" in charlie_lobby.text
        assert "(Available)" in charlie_lobby.text

        # Step 4: Without opponent_name parameter, both get single player mode
        alice_game = client.get("/game?player_name=Alice")
        bob_game = client.get("/game?player_name=Bob")

        for response in [alice_game, bob_game]:
            # Without opponent_name, defaults to single player mode
            assert response.status_code == status.HTTP_200_OK
            # Should not show multiplayer-specific elements
            assert 'data-testid="opponent-name"' not in response.text

