from pytest_bdd import when
from game import player
import pytest
from game.player import Player, PlayerStatus
from services.lobby_service import LobbyService


class TestLobbyService:
    # Unit tests for join_lobby method

    def test_join_lobby_adds_regular_player(self, empty_lobby_service: LobbyService):
        # Test that join_lobby adds a regular player to the lobby
        empty_lobby_service.join_lobby("John")

        # Verify John was added to the lobby
        players: list[Player] = empty_lobby_service.get_available_players()
        assert len(players) == 1
        john: Player = players[0]
        assert john.name == "John"
        assert john.status == PlayerStatus.AVAILABLE

    def test_join_lobby_handles_empty_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test that empty player name raises ValueError
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby("")

        # Lobby should remain empty
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0

    def test_join_lobby_handles_whitespace_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test that whitespace-only player name raises ValueError
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby("   ")

        # Lobby should remain empty
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0

    def test_join_lobby_strips_player_name(self, empty_lobby_service: LobbyService):
        # Test that player name gets stripped of whitespace
        empty_lobby_service.join_lobby("  Alice  ")

        # Verify Alice was added with stripped name
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1
        alice: Player = players[0]
        assert alice.name == "Alice"  # Should be stripped

    def test_join_lobby_with_existing_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test that same player joining multiple times raises ValueError
        empty_lobby_service.join_lobby("Alice")
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby("Alice")

        # Should still have only one Alice
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1

    # Unit tests for get_lobby_data_for_player method
    def test_get_lobby_data_expected_results(
        self, populated_lobby_service: LobbyService
    ):
        results: list[str] = populated_lobby_service.get_lobby_data_for_player("Alice")
        assert len(results) == 2
        assert results == ["Bob", "Charlie"]

    def test_get_lobby_data_for_new_player(self, empty_lobby_service: LobbyService):
        # Test getting lobby data for a new player
        empty_lobby_service.join_lobby("Alice")
        results: list[str] = empty_lobby_service.get_lobby_data_for_player("Alice")

        assert results == []

    def test_get_lobby_data_does_not_modify_lobby_state(
        self, populated_lobby_service: LobbyService
    ):
        # Test that getting lobby data does not modify the lobby state
        # populated_lobby_service.get_lobby_data_for_player("Alice")

        # Get initial state
        initial_players: list[Player] = populated_lobby_service.get_available_players()
        initial_count: int = len(initial_players)
        initial_names: list[str] = [player.name for player in initial_players]

        # Get lobby data for a new player
        populated_lobby_service.get_lobby_data_for_player("Alice")

        # Verify lobby state is unchanged
        final_players: list[Player] = populated_lobby_service.get_available_players()
        final_count: int = len(final_players)
        final_names: list[str] = [player.name for player in final_players]

        assert final_count == initial_count
        assert final_names == initial_names

    def test_get_lobby_data_filters_by_available_status(self):
        # TODO: Implement when we have other PlayerStatus defined
        pass

    def test_get_lobby_data_handles_empty_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test handling of empty player name
        with pytest.raises(ValueError):
            empty_lobby_service.get_lobby_data_for_player("")

    def test_get_lobby_data_handles_whitespace_player_name(
        self, empty_lobby_service, empty_result
    ):
        # Test handling of whitespace-only player name
        with pytest.raises(ValueError):
            empty_lobby_service.get_lobby_data_for_player("   ")

    def test_get_lobby_data_strips_player_name(
        self, populated_lobby_service: LobbyService
    ):
        # Test that player name gets stripped of whitespace
        # Add existing player

        results: list[str] = populated_lobby_service.get_lobby_data_for_player(
            "  Bob  "
        )

        # Should see existing players only (Bob should NOT be added to lobby)
        assert "Alice" in results
        assert "Bob" not in results  # Bob should not appear - not in lobby
        assert "  Bob  " not in results  # Unstripped version should not exist

    def test_get_lobby_data_multiple_calls_same_player(
        self, empty_lobby, empty_lobby_service
    ):
        # Test multiple calls with same player name
        # First call
        result1 = empty_lobby_service.get_lobby_data_for_player("John")

        # Second call - should not duplicate player
        result2 = empty_lobby_service.get_lobby_data_for_player("John")

        # Results should be identical
        assert result1 == result2

        # Verify John wasn't added multiple times to lobby
        all_players = empty_lobby.get_available_players()
        john_count = sum(1 for player in all_players if player.name == "John")
        assert john_count == 0  # John should NOT be in lobby at all
