import pytest
from game.player import Player, PlayerStatus


class TestPlayerStatus:
    def test_player_status_available_exists(self):
        status: PlayerStatus = PlayerStatus.AVAILABLE
        assert status == "Available"


class TestPlayer:
    def test_player_creation(self):
        player: Player = Player("David", PlayerStatus.AVAILABLE)
        assert player

    def test_add_player_only_accepts_player_status_enum(self):
        with pytest.raises(TypeError):
            Player("David", "InvalidStatus")
