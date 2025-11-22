import pytest
from game.player import Player, PlayerStatus


class TestPlayerStatus:
    def test_player_status_values(self):
        # Test that we have all expected enum values
        expected_statuses = {
            PlayerStatus.AVAILABLE,
            PlayerStatus.REQUESTING_GAME,
            PlayerStatus.PENDING_RESPONSE,
            PlayerStatus.IN_GAME,
        }
        actual_statuses: set[PlayerStatus] = {status for status in PlayerStatus}
        assert expected_statuses == actual_statuses

    def test_all_player_statuses_are_strings(self):
        for status in PlayerStatus:
            assert isinstance(status, str)


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
