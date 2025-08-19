import pytest
from game.player import PlayerStatus


class TestPlayerStatus:
    def test_player_status_available_exists(self):
        status: PlayerStatus = PlayerStatus.AVAILABLE
        assert status == "Available"