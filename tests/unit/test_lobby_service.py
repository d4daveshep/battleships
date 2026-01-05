import pytest
from game import lobby
from game.player import GameRequest, Player, PlayerStatus
from services.lobby_service import LobbyService
from tests.unit.conftest import make_player


class TestLobbyService:
    # Unit tests for join_lobby method

    def test_join_lobby_adds_regular_player(self, empty_lobby_service: LobbyService):
        # Test that join_lobby adds a regular player to the lobby
        john = make_player("John")
        empty_lobby_service.join_lobby(john)

        # Verify John was added to the lobby
        players: list[Player] = empty_lobby_service.get_available_players()
        assert len(players) == 1
        john: Player = players[0]
        assert john.name == "John"
        assert john.status == PlayerStatus.AVAILABLE

    def test_join_lobby_with_existing_player(self, empty_lobby_service: LobbyService):
        # Test that same player joining multiple times raises ValueError
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby(alice)

        # Should still have only one Alice
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1

    # Unit tests for get_lobby_data_for_player method
    def test_get_lobby_data_expected_results(self, populated_lobby_service: dict):
        service = populated_lobby_service["service"]

        alice = populated_lobby_service["alice"]

        bob = populated_lobby_service["bob"]

        charlie = populated_lobby_service["charlie"]

        results: list[str] = service.get_lobby_data_for_player(alice.id)
        assert len(results) == 2
        assert results == ["Bob", "Charlie"]

    def test_get_lobby_data_for_new_player(self, empty_lobby_service: LobbyService):
        # Test getting lobby data for a new player
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        results: list[str] = empty_lobby_service.get_lobby_data_for_player(alice.id)

        assert results == []

    def test_get_lobby_data_fails_with_unknown_player_id(
        self, empty_lobby_service: LobbyService
    ):
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")  # Bob not in Lobby
        with pytest.raises(KeyError):
            empty_lobby_service.get_lobby_data_for_player(bob.id)

    def test_get_lobby_data_fails_with_unavailable_player_id(
        self, empty_lobby_service: LobbyService
    ):
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob", status=PlayerStatus.IN_GAME)  # Bob not available
        empty_lobby_service.join_lobby(bob)
        with pytest.raises(KeyError):
            empty_lobby_service.get_lobby_data_for_player(bob.id)

    def test_get_lobby_data_filters_out_in_game_status(
        self, empty_lobby_service: LobbyService
    ):
        lobby_service: LobbyService = empty_lobby_service
        # create some AVAILABLE players and add them to the lobby
        alice: Player = make_player("Alice")
        bob: Player = make_player("Bob")
        charlie: Player = make_player("Charlie")
        lobby_service.join_lobby(alice)
        lobby_service.join_lobby(bob)
        lobby_service.join_lobby(charlie)

        initial_player_count: int = len(
            lobby_service.get_lobby_players_for_player(alice.id)
        )

        # Add Diana to lobby and set status to IN_GAME
        diana = make_player("Diana")
        lobby_service.join_lobby(diana)
        lobby_service.update_player_status(diana.id, PlayerStatus.IN_GAME)

        lobby_data: list[str] = lobby_service.get_lobby_data_for_player(alice.id)
        assert len(lobby_data) == initial_player_count
        assert "Diana" not in lobby_data, (
            "IN_GAME player 'Diana' included in lobby data"
        )

    # Unit tests for new status management methods

    def test_update_player_status_existing_player(
        self, empty_lobby_service: LobbyService
    ):
        # Add a player first
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)

        # Update Alice's status
        empty_lobby_service.update_player_status(alice.id, PlayerStatus.REQUESTING_GAME)

        # Verify status was updated
        alice_status: PlayerStatus = empty_lobby_service.get_player_status(alice.id)
        assert alice_status == PlayerStatus.REQUESTING_GAME

    def test_update_player_status_nonexistent_player(
        self, empty_lobby_service: LobbyService
    ):
        # Try to update status of player that doesn't exist
        with pytest.raises(ValueError, match=r"Player with ID .*not found in lobby"):
            empty_lobby_service.update_player_status(
                "NonExistent", PlayerStatus.REQUESTING_GAME
            )

    def test_update_player_status_all_statuses(self, empty_lobby_service: LobbyService):
        # Add a player and test updating to all different statuses
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)

        # Test updating to REQUESTING_GAME
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)
        assert (
            empty_lobby_service.get_player_status(bob.id)
            == PlayerStatus.REQUESTING_GAME
        )

        # Test updating to IN_GAME
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.IN_GAME)
        assert empty_lobby_service.get_player_status(bob.id) == PlayerStatus.IN_GAME

        # Test updating back to AVAILABLE
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.AVAILABLE)
        assert empty_lobby_service.get_player_status(bob.id) == PlayerStatus.AVAILABLE

    def test_get_player_status_existing_player(self, empty_lobby_service: LobbyService):
        # Add players with different statuses
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)

        # Verify we can get each player's status
        assert empty_lobby_service.get_player_status(alice.id) == PlayerStatus.AVAILABLE
        assert (
            empty_lobby_service.get_player_status(bob.id)
            == PlayerStatus.REQUESTING_GAME
        )

    def test_get_player_status_nonexistent_player(
        self, empty_lobby_service: LobbyService
    ):
        # Try to get status of player that doesn't exist
        with pytest.raises(ValueError, match=r"Player with ID .*not found in lobby"):
            empty_lobby_service.get_player_status("NonExistent")

    # Unit tests for get_lobby_players_for_player method

    def test_get_lobby_players_for_player_returns_player_objects(
        self, empty_lobby_service: LobbyService
    ):
        # Add players with different statuses
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        charlie = make_player("Charlie")
        empty_lobby_service.join_lobby(charlie)
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)
        empty_lobby_service.update_player_status(charlie.id, PlayerStatus.IN_GAME)

        # Get lobby players for Alice
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            alice.id
        )

        # Should return Bob and Charlie (all other players regardless of status)
        assert len(players) == 2
        assert all(isinstance(player, Player) for player in players)

        player_names: list[str] = [player.name for player in players]
        assert "Bob" in player_names
        assert "Charlie" in player_names
        assert "Alice" not in player_names  # Should not include requesting player

    def test_get_lobby_players_for_player_excludes_requesting_player(
        self, empty_lobby_service: LobbyService
    ):
        # Add several players
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        charlie = make_player("Charlie")
        empty_lobby_service.join_lobby(charlie)

        # Get lobby players for Bob
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(bob.id)

        # Should return Alice and Charlie, but not Bob
        assert len(players) == 2
        player_names: list[str] = [player.name for player in players]
        assert "Alice" in player_names
        assert "Charlie" in player_names
        assert "Bob" not in player_names

    def test_get_lobby_players_for_player_includes_all_statuses(
        self, empty_lobby_service: LobbyService
    ):
        # Add players with different statuses
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        charlie = make_player("Charlie")
        empty_lobby_service.join_lobby(charlie)
        diana = make_player("Diana")
        empty_lobby_service.join_lobby(diana)

        # Update players to different statuses
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)
        empty_lobby_service.update_player_status(charlie.id, PlayerStatus.IN_GAME)
        # Alice and Diana remain AVAILABLE

        # Get lobby players for Diana
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            diana.id
        )

        # Should return all other players regardless of status
        assert len(players) == 3
        player_names_and_statuses: list[tuple[str, PlayerStatus]] = [
            (p.name, p.status) for p in players
        ]

        assert ("Alice", PlayerStatus.AVAILABLE) in player_names_and_statuses
        assert ("Bob", PlayerStatus.REQUESTING_GAME) in player_names_and_statuses
        assert ("Charlie", PlayerStatus.IN_GAME) in player_names_and_statuses
        assert all(name != "Diana" for name, _ in player_names_and_statuses)

    def test_get_lobby_players_for_player_empty_lobby(
        self, empty_lobby_service: LobbyService
    ):
        # Add only one player
        lonely = make_player("Lonely")
        empty_lobby_service.join_lobby(lonely)

        # Get lobby players for the only player
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            lonely.id
        )

        # Should return empty list (no other players)
        assert len(players) == 0
        assert players == []

    # Unit tests for leave_lobby method

    def test_leave_lobby_removes_existing_player(
        self, empty_lobby_service: LobbyService
    ):
        # Test that leave_lobby removes an existing player from the lobby
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)

        # Verify both players are in lobby
        players = empty_lobby_service.get_available_players()
        assert len(players) == 2

        # Alice leaves the lobby
        empty_lobby_service.leave_lobby(alice.id)

        # Verify Alice is no longer in lobby but Bob remains
        remaining_players = empty_lobby_service.get_available_players()
        assert len(remaining_players) == 1
        assert remaining_players[0].name == "Bob"

    def test_leave_lobby_with_nonexistent_player(
        self, empty_lobby_service: LobbyService
    ):
        # Test that leave_lobby with nonexistent player raises ValueError
        with pytest.raises(ValueError, match=r"Player with ID .*not found in lobby"):
            empty_lobby_service.leave_lobby("NonExistent")

    def test_leave_lobby_from_empty_lobby(self, empty_lobby_service: LobbyService):
        alice: Player = make_player("Alice")
        # Test that leave_lobby from empty lobby raises ValueError
        with pytest.raises(ValueError, match=r"Player with ID .*not found in lobby"):
            empty_lobby_service.leave_lobby(alice.id)

    def test_leave_lobby_updates_other_players_views(
        self, empty_lobby_service: LobbyService
    ):
        # Test that when a player leaves, it affects other players' lobby views
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        charlie = make_player("Charlie")
        empty_lobby_service.join_lobby(charlie)

        # Bob should see Alice and Charlie
        bob_view = empty_lobby_service.get_lobby_players_for_player(bob.id)
        bob_view_names = [p.name for p in bob_view]
        assert "Alice" in bob_view_names
        assert "Charlie" in bob_view_names

        # Alice leaves
        empty_lobby_service.leave_lobby(alice.id)

        # Bob should now only see Charlie
        updated_bob_view = empty_lobby_service.get_lobby_players_for_player(bob.id)
        updated_names = [p.name for p in updated_bob_view]
        assert "Alice" not in updated_names
        assert "Charlie" in updated_names
        assert len(updated_names) == 1

    def test_leave_lobby_with_different_player_statuses(
        self, empty_lobby_service: LobbyService
    ):
        # Test that players can leave regardless of their status
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        charlie = make_player("Charlie")
        empty_lobby_service.join_lobby(charlie)

        # Set different statuses
        empty_lobby_service.update_player_status(alice.id, PlayerStatus.REQUESTING_GAME)
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.IN_GAME)
        # Charlie remains AVAILABLE

        # All players should be able to leave regardless of status
        empty_lobby_service.leave_lobby(alice.id)  # REQUESTING_GAME status
        empty_lobby_service.leave_lobby(bob.id)  # IN_GAME status
        empty_lobby_service.leave_lobby(charlie.id)  # AVAILABLE status

        # Lobby should be empty
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0

    def test_leave_lobby_multiple_times_same_player(
        self, empty_lobby_service: LobbyService
    ):
        # Test that calling leave_lobby multiple times for same player raises ValueError
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)

        # First leave should succeed
        empty_lobby_service.leave_lobby(alice.id)

        # Second leave should fail
        with pytest.raises(ValueError, match=r"Player with ID .*not found in lobby"):
            empty_lobby_service.leave_lobby(alice.id)

    def test_leave_lobby_last_player(self, empty_lobby_service: LobbyService):
        # Test that the last player can leave, resulting in empty lobby
        lastplayer = make_player("LastPlayer")
        empty_lobby_service.join_lobby(lastplayer)

        # Verify player is in lobby
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1
        assert players[0].name == "LastPlayer"

        # Last player leaves
        empty_lobby_service.leave_lobby(lastplayer.id)

        # Lobby should be empty
        final_players = empty_lobby_service.get_available_players()
        assert len(final_players) == 0


class TestLobbyServiceGameRequests:
    """Tests for game request functionality in LobbyService"""

    def test_send_game_request_success(self, empty_lobby_service: LobbyService):
        # Setup: Add two available players
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)

        # Alice sends a game request to Bob
        empty_lobby_service.send_game_request(sender_id=alice.id, receiver_id=bob.id)

        # Verify: Both players have correct status
        assert (
            empty_lobby_service.get_player_status(alice.id)
            == PlayerStatus.REQUESTING_GAME
        )
        assert (
            empty_lobby_service.get_player_status(bob.id)
            == PlayerStatus.PENDING_RESPONSE
        )

        # Verify: Bob has a pending request from Alice
        pending_request = empty_lobby_service.get_pending_request_for_player(bob.id)
        assert pending_request is not None
        assert pending_request.sender_id == alice.id
        assert pending_request.receiver_id == bob.id

    def test_send_game_request_sender_not_available(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add players with Alice already requesting a game
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.update_player_status(alice.id, PlayerStatus.REQUESTING_GAME)

        # Test: Alice cannot send another request while already requesting
        with pytest.raises(ValueError, match=r"Sender with ID .*is not available"):
            empty_lobby_service.send_game_request(alice.id, bob.id)

    def test_send_game_request_receiver_not_available(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add players with Bob not available
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.update_player_status(bob.id, PlayerStatus.IN_GAME)

        # Test: Cannot send request to unavailable player
        with pytest.raises(ValueError, match="Receiver with ID .*is not available"):
            empty_lobby_service.send_game_request(alice.id, bob.id)

    def test_send_game_request_nonexistent_players(
        self, empty_lobby_service: LobbyService
    ):
        alice: Player = make_player("Alice")
        bob: Player = make_player("Bob")

        # Test: Should validate that both players exist
        with pytest.raises(ValueError, match="not found in lobby"):
            empty_lobby_service.send_game_request(alice.id, bob.id)

        # Add only Alice
        empty_lobby_service.join_lobby(alice)

        with pytest.raises(ValueError, match="not found in lobby"):
            empty_lobby_service.send_game_request(alice.id, bob.id)

    def test_get_pending_request_for_player_exists(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add players and send request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.send_game_request(alice.id, bob.id)

        # Test: Get pending request for receiver
        request = empty_lobby_service.get_pending_request_for_player(bob.id)

        assert request is not None
        assert request.sender_id == alice.id
        assert request.receiver_id == bob.id

    def test_get_pending_request_for_player_none_exists(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add player with no pending request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)

        # Test: Should return None when no request exists
        request = empty_lobby_service.get_pending_request_for_player(alice.id)
        assert request is None

    def test_get_pending_request_by_sender(self, empty_lobby_service: LobbyService):
        # Setup: Add players and send request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.send_game_request(alice.id, bob.id)

        game_request: GameRequest | None = (
            empty_lobby_service.get_pending_request_by_sender(alice.id)
        )
        assert game_request is not None
        assert game_request.sender_id == alice.id
        assert game_request.receiver_id == bob.id

    def test_accept_game_request_success(self, empty_lobby_service: LobbyService):
        # Setup: Add players and send request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.send_game_request(alice.id, bob.id)

        # Test: Bob accepts the request
        sender_id, receiver_id = empty_lobby_service.accept_game_request(bob.id)

        # Verify: Returns correct player names
        assert sender_id == alice.id
        assert receiver_id == bob.id

        # Verify: Both players are now IN_GAME
        assert empty_lobby_service.get_player_status(alice.id) == PlayerStatus.IN_GAME
        assert empty_lobby_service.get_player_status(bob.id) == PlayerStatus.IN_GAME

        # Verify: No pending request remains
        request = empty_lobby_service.get_pending_request_for_player(bob.id)
        assert request is None

    def test_accept_game_request_no_pending_request(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add player with no pending request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)

        # Test: Should raise error when no request to accept
        with pytest.raises(ValueError, match="No pending game request"):
            empty_lobby_service.accept_game_request(alice.id)

    def test_accept_game_request_empty_name(self, empty_lobby_service: LobbyService):
        # Test: Should validate player name
        with pytest.raises(ValueError):
            empty_lobby_service.accept_game_request("")

    def test_decline_game_request_success(self, empty_lobby_service: LobbyService):
        # Setup: Add players and send request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        empty_lobby_service.send_game_request(alice.id, bob.id)

        # Test: Bob declines the request
        sender_id = empty_lobby_service.decline_game_request(bob.id)

        # Verify: Returns sender name
        assert sender_id == alice.id

        # Verify: Both players are back to AVAILABLE
        assert empty_lobby_service.get_player_status(alice.id) == PlayerStatus.AVAILABLE
        assert empty_lobby_service.get_player_status(bob.id) == PlayerStatus.AVAILABLE

        # Verify: No pending request remains
        request = empty_lobby_service.get_pending_request_for_player(bob.id)
        assert request is None

    def test_decline_game_request_no_pending_request(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add player with no pending request
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)

        # Test: Should raise error when no request to decline
        with pytest.raises(ValueError, match="No pending game request"):
            empty_lobby_service.decline_game_request(alice.id)

    def test_decline_game_request_empty_name(self, empty_lobby_service: LobbyService):
        # Test: Should validate player name
        with pytest.raises(ValueError):
            empty_lobby_service.decline_game_request("")

    def test_multiple_game_requests_different_receivers(
        self, empty_lobby_service: LobbyService
    ):
        # Setup: Add multiple players
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)
        charlie = make_player("Charlie")
        empty_lobby_service.join_lobby(charlie)
        diana = make_player("Diana")
        empty_lobby_service.join_lobby(diana)

        # Test: Send requests from different senders to different receivers
        empty_lobby_service.send_game_request(alice.id, bob.id)
        empty_lobby_service.send_game_request(charlie.id, diana.id)

        # Verify: Both requests exist independently
        bob_request = empty_lobby_service.get_pending_request_for_player(bob.id)
        diana_request = empty_lobby_service.get_pending_request_for_player(diana.id)

        assert bob_request is not None
        assert diana_request is not None
        assert bob_request.sender_id == alice.id
        assert diana_request.sender_id == charlie.id

        # Verify: Players have correct statuses
        assert (
            empty_lobby_service.get_player_status(alice.id)
            == PlayerStatus.REQUESTING_GAME
        )
        assert (
            empty_lobby_service.get_player_status(bob.id)
            == PlayerStatus.PENDING_RESPONSE
        )
        assert (
            empty_lobby_service.get_player_status(charlie.id)
            == PlayerStatus.REQUESTING_GAME
        )
        assert (
            empty_lobby_service.get_player_status(diana.id)
            == PlayerStatus.PENDING_RESPONSE
        )

    def test_game_request_workflow_accept(self, empty_lobby_service: LobbyService):
        # Test: Complete workflow from request to acceptance
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)

        # Step 1: Alice sends request to Bob
        empty_lobby_service.send_game_request(alice.id, bob.id)
        assert (
            empty_lobby_service.get_player_status(alice.id)
            == PlayerStatus.REQUESTING_GAME
        )
        assert (
            empty_lobby_service.get_player_status(bob.id)
            == PlayerStatus.PENDING_RESPONSE
        )

        # Step 2: Bob accepts the request
        sender_id, receiver_id = empty_lobby_service.accept_game_request(bob.id)
        assert sender_id == alice.id
        assert receiver_id == bob.id
        assert empty_lobby_service.get_player_status(alice.id) == PlayerStatus.IN_GAME
        assert empty_lobby_service.get_player_status(bob.id) == PlayerStatus.IN_GAME

    def test_game_request_workflow_decline(self, empty_lobby_service: LobbyService):
        # Test: Complete workflow from request to decline
        alice = make_player("Alice")
        empty_lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        empty_lobby_service.join_lobby(bob)

        # Step 1: Alice sends request to Bob
        empty_lobby_service.send_game_request(alice.id, bob.id)
        assert (
            empty_lobby_service.get_player_status(alice.id)
            == PlayerStatus.REQUESTING_GAME
        )
        assert (
            empty_lobby_service.get_player_status(bob.id)
            == PlayerStatus.PENDING_RESPONSE
        )

        # Step 2: Bob declines the request
        sender_id = empty_lobby_service.decline_game_request(bob.id)
        assert sender_id == alice.id
        assert empty_lobby_service.get_player_status(alice.id) == PlayerStatus.AVAILABLE
        assert empty_lobby_service.get_player_status(bob.id) == PlayerStatus.AVAILABLE
