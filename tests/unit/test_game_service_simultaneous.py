import pytest
from game.game_service import GameService, ShotStatus
from game.model import Coord, Ship, ShipType, Orientation


class TestGameServiceSimultaneous:
    @pytest.fixture
    def setup(self, game_service, alice, bob):
        """Setup game service with 2-player game."""
        game_service.add_player(alice)
        game_service.add_player(bob)
        game_id = game_service.create_two_player_game(alice.id, bob.id)

        # Place ships to allow firing
        game = game_service.games[game_id]

        # Alice ships
        game.board[alice].place_ship(
            Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL
        )

        # Bob ships
        game.board[bob].place_ship(
            Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL
        )

        return game_service, game_id, alice, bob

    def test_process_shot_returns_waiting_or_result(self, setup):
        service, game_id, alice, bob = setup

        # 1. Alice fires (first player)
        service.toggle_aim(game_id, alice.id, "A1")
        result_alice = service.fire_shots(game_id, alice.id)

        # Expect WAITING status
        assert result_alice.status == ShotStatus.WAITING

        # 2. Bob fires (second player)
        service.toggle_aim(game_id, bob.id, "A1")
        result_bob = service.fire_shots(game_id, bob.id)

        # Expect COMPLETED status
        assert result_bob.status == ShotStatus.COMPLETED
