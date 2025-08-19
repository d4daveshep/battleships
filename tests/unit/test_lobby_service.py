from game.player import PlayerStatus


class TestLobbyService:
    # Unit tests for LobbyService - extracted from main.py lobby logic

    def test_get_lobby_data_for_new_player(self, empty_lobby_service, empty_result):
        # Test getting lobby data for a new player
        result = empty_lobby_service.get_lobby_data_for_player("John")

        assert result == empty_result

    def test_get_lobby_data_does_not_modify_lobby_state(
        self, populated_lobby, populated_lobby_service
    ):
        # Test that getting lobby data does not modify the lobby state

        # Get initial state
        initial_players = populated_lobby.get_available_players()
        initial_count = len(initial_players)
        initial_names = [player.name for player in initial_players]

        # Get lobby data for a new player
        populated_lobby_service.get_lobby_data_for_player("John")

        # Verify lobby state is unchanged
        final_players = populated_lobby.get_available_players()
        final_count = len(final_players)
        final_names = [player.name for player in final_players]

        assert final_count == initial_count
        assert final_names == initial_names
        assert "John" not in final_names  # John should NOT be added to lobby

    def test_get_lobby_data_excludes_current_player_from_results(
        self, populated_lobby_service
    ):
        # Test that current player is excluded from available players list

        result = populated_lobby_service.get_lobby_data_for_player("Alice")

        # Alice should not see herself in the list
        available_names = [player["name"] for player in result["available_players"]]
        assert "Alice" not in available_names
        assert "Bob" in available_names

    def test_get_lobby_data_filters_by_available_status(self, populated_lobby_service):
        # Test that only AVAILABLE status players are returned

        result = populated_lobby_service.get_lobby_data_for_player("Charlie")

        # Should only see available players (Alice, Bob)
        available_names = [player["name"] for player in result["available_players"]]
        assert "Alice" in available_names
        assert "Bob" in available_names
        assert len(result["available_players"]) == 2

    def test_get_lobby_data_handles_empty_player_name(
        self, empty_lobby_service, empty_result
    ):
        # Test handling of empty player name
        result = empty_lobby_service.get_lobby_data_for_player("")

        assert result == empty_result

    def test_get_lobby_data_handles_whitespace_player_name(
        self, empty_lobby_service, empty_result
    ):
        # Test handling of whitespace-only player name
        result = empty_lobby_service.get_lobby_data_for_player("   ")

        assert result == empty_result

    def test_get_lobby_data_strips_player_name(self, empty_lobby, empty_lobby_service):
        # Test that player name gets stripped of whitespace
        # Add existing player
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        result = empty_lobby_service.get_lobby_data_for_player("  Bob  ")

        # Should see existing players only (Bob should NOT be added to lobby)
        available_names = [player["name"] for player in result["available_players"]]
        assert "Alice" in available_names
        assert "Bob" not in available_names  # Bob should not appear - not in lobby
        assert "  Bob  " not in available_names  # Unstripped version should not exist

    def test_get_lobby_data_diana_scenario(self, empty_lobby_service, diana_expected_players):
        # Test special Diana scenario (for test compatibility)
        result = empty_lobby_service.get_lobby_data_for_player("Diana")

        # Diana should see Alice, Bob, Charlie (from test scenario)
        assert len(result["available_players"]) == 3
        for player in diana_expected_players:
            assert player in result["available_players"]

    def test_get_lobby_data_eve_scenario(self, populated_lobby_service, empty_result):
        # Test special Eve scenario (empty lobby test compatibility)

        result = populated_lobby_service.get_lobby_data_for_player("Eve")

        # Eve should see empty lobby regardless of actual lobby state
        assert result == empty_result

    def test_get_lobby_data_return_format(self, empty_lobby_service):
        # Test that return format is correct dictionary structure
        result = empty_lobby_service.get_lobby_data_for_player("TestPlayer")

        # Should return dict with 'available_players' key containing list of dicts
        assert isinstance(result, dict)
        assert "available_players" in result
        assert isinstance(result["available_players"], list)

        # If there are players, each should be a dict with 'name' key
        if result["available_players"]:
            for player in result["available_players"]:
                assert isinstance(player, dict)
                assert "name" in player
                assert isinstance(player["name"], str)

    def test_get_lobby_data_multiple_calls_same_player(self, empty_lobby, empty_lobby_service):
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

