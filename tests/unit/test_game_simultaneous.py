import pytest
from game.model import Game, GameMode, Ship, ShipType, Orientation, Coord


class TestGameSimultaneous:
    @pytest.fixture
    def game(self, alice, bob):
        """Create a standard 2-player game with ships placed."""
        g = Game(player_1=alice, player_2=bob, game_mode=GameMode.TWO_PLAYER)

        # Place ships for Alice
        board1 = g.board[alice]
        board1.place_ship(Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL)

        # Place ships for Bob
        board2 = g.board[bob]
        board2.place_ship(Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL)

        return g

    def test_fire_first_shot_stores_pending(self, game, alice, bob):
        """
        When the first player fires:
        1. Shots are stored in a pending state (fired_shots).
        2. Shots are NOT yet applied to the opponent's board.
        3. Player is marked as waiting.
        """
        # Alice aims and fires at Bob's ship
        game.aim_at(alice.id, Coord.A1)
        game.fire_shots(alice.id)

        # Check Alice's state
        assert game.is_waiting_for_opponent(alice.id) is True
        assert Coord.A1 in game.get_fired_shots(alice.id)

        # Check Bob's board - should NOT have received the shot yet
        # checking the internal shots_received dict or a public method if available
        # GameBoard.shots_received is a dict
        assert len(game.board[bob].shots_received) == 0

        # Check Bob's state
        assert game.is_waiting_for_opponent(bob.id) is False

    def test_fire_second_shot_resolves_round(self, game, alice, bob):
        """
        When the second player fires:
        1. Both players' shots are applied to opponents' boards.
        2. fired_shots is cleared.
        3. Round number increments.
        4. Both players are no longer waiting.
        """
        # Alice aims and fires at Bob's ship (A1)
        game.aim_at(alice.id, Coord.A1)
        game.fire_shots(alice.id)

        # Bob aims and fires at Alice's ship (A1)
        game.aim_at(bob.id, Coord.A1)
        game.fire_shots(bob.id)

        # 1. Check shots applied
        # Alice fired at Bob, so Bob received A1
        assert Coord.A1 in game.board[bob].shots_received
        # Bob fired at Alice, so Alice received A1
        assert Coord.A1 in game.board[alice].shots_received

        # 2. Check fired_shots cleared (for next round)
        assert len(game.get_fired_shots(alice.id)) == 0
        assert len(game.get_fired_shots(bob.id)) == 0

        # 3. Check round incremented
        assert game.round == 2

        # 4. Check waiting status
        assert game.is_waiting_for_opponent(alice.id) is False
        assert game.is_waiting_for_opponent(bob.id) is False
