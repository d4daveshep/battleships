from game.player import Player, PlayerStatus


class TestLobby:
    def test_lobby_creation(self, empty_lobby):
        assert empty_lobby

    def test_add_player_to_empty_lobby(self, empty_lobby):
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        available_players: list[Player] = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert isinstance(available_players[0], Player)
        assert available_players[0].name == "Alice"
        assert available_players[0].status == PlayerStatus.AVAILABLE

    def test_add_multiple_players(self, empty_lobby):
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)

        available_players: list[Player] = empty_lobby.get_available_players()
        assert len(available_players) == 3
