import pytest
from game.player import Player, PlayerStatus


class TestPlayerStatus:
    def test_player_status_available_exists(self):
        status: PlayerStatus = PlayerStatus.AVAILABLE
        assert status == "Available"

    def test_player_status_requesting_game_exists(self):
        status: PlayerStatus = PlayerStatus.REQUESTING_GAME
        assert status == "Requesting Game"

    def test_player_status_in_game_exists(self):
        status: PlayerStatus = PlayerStatus.IN_GAME
        assert status == "In Game"

    def test_all_player_statuses_are_strings(self):
        # Verify all PlayerStatus enum values are strings
        assert isinstance(PlayerStatus.AVAILABLE, str)
        assert isinstance(PlayerStatus.REQUESTING_GAME, str)
        assert isinstance(PlayerStatus.IN_GAME, str)

    def test_player_status_values(self):
        # Test that we have all expected enum values
        expected_statuses = {
            PlayerStatus.AVAILABLE,
            PlayerStatus.REQUESTING_GAME,
            PlayerStatus.IN_GAME,
        }
        actual_statuses: set[PlayerStatus] = {status for status in PlayerStatus}
        assert expected_statuses == actual_statuses


class TestPlayer:
    def test_player_creation(self):
        player: Player = Player("David", PlayerStatus.AVAILABLE)
        assert player

    def test_add_player_only_accepts_player_status_enum(self):
        with pytest.raises(TypeError):
            Player("David", "InvalidStatus")  # type: ignore

    def test_player_creation_with_requesting_game_status(self):
        player: Player = Player("Alice", PlayerStatus.REQUESTING_GAME)
        assert player.name == "Alice"
        assert player.status == PlayerStatus.REQUESTING_GAME

    def test_player_creation_with_in_game_status(self):
        player: Player = Player("Bob", PlayerStatus.IN_GAME)
        assert player.name == "Bob"
        assert player.status == PlayerStatus.IN_GAME

    def test_player_status_can_be_updated(self):
        # Test that we can update player status after creation
        player: Player = Player("Charlie", PlayerStatus.AVAILABLE)

        # Update to REQUESTING_GAME
        player.status = PlayerStatus.REQUESTING_GAME
        assert player.status == PlayerStatus.REQUESTING_GAME

        # Update to IN_GAME
        player.status = PlayerStatus.IN_GAME
        assert player.status == PlayerStatus.IN_GAME

        # Update back to AVAILABLE
        player.status = PlayerStatus.AVAILABLE
        assert player.status == PlayerStatus.AVAILABLE
