import pytest
from game.models import Coordinate, ShipType, Direction, Ship
from game.player import Player


class TestPlayer:
    def test_player_creation(self):
        player: Player = Player("Test Player")
        assert player.name == "Test Player"

    #     assert not player.is_computer
    #     assert len(player.board.ships) == 0  # No ships placed
    #     assert len(player.hits_made) == 5  # All ship types initialized
    #     assert len(player.opponent_ships_sunk) == 0
    #
    # def test_computer_player_creation(self):
    #     player: Player = Player("Computer", is_computer=True)
    #     assert player.name == "Computer"
    #     assert player.is_computer
    #
    # def test_place_ship(self):
    #     player: Player = Player("Test Player")
    #
    #     ship_is_placed: bool = player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #     assert ship_is_placed
    #     assert len(player.board.ships) == 1
    #
    #     # Find the placed ship
    #     placed_ship: Ship | None = None
    #     for ship in player.board.ships:
    #         if ship.ship_type == ShipType.DESTROYER:
    #             placed_ship = ship
    #             break
    #
    #     assert placed_ship
    #     assert len(placed_ship.positions) == 2
    #
    # def test_place_ship_invalid(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place first ship
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #
    #     # Try to place overlapping ship
    #     ship_is_placed: bool = player.place_ship(
    #         ship_type=ShipType.CRUISER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.VERTICAL,
    #     )
    #     assert not ship_is_placed
    #     assert len(player.board.ships) == 1
    #
    # def test_fire_shots(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place a ship to have available shots
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #
    #     targets: list[Coordinate] = [Coordinate(5, 5)]
    #     valid_shots: list[Coordinate] = player.fire_shots(targets, 1)
    #
    #     assert len(valid_shots) == 1
    #     assert valid_shots[0] == Coordinate(5, 5)
    #     assert Coordinate(5, 5) in player.board.shots_fired
    #
    # def test_fire_shots_too_many(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place a destroyer (1 shot available)
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #     assert player.get_available_shots() == 1
    #
    #     # Try to fire 2 shots when only 1 available
    #     targets: list[Coordinate] = [Coordinate(5, 5), Coordinate(6, 6)]
    #
    #     with pytest.raises(ValueError, match="Cannot fire 2 shots"):
    #         player.fire_shots(targets=targets, round_number=1)
    #
    # def test_fire_shots_duplicate(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place a ship to have available shots
    #     player.place_ship(
    #         ship_type=ShipType.CARRIER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #     assert player.get_available_shots() == 2
    #
    #     # Fire first shot
    #     player.fire_shots(targets=[Coordinate(5, 5)], round_number=1)
    #
    #     # Try to fire at same position again
    #     valid_shots: list[Coordinate] = player.fire_shots(
    #         targets=[Coordinate(5, 5), Coordinate(6, 6)], round_number=2
    #     )
    #
    #     # Should only return the valid shot
    #     assert len(valid_shots) == 1
    #     assert Coordinate(6, 6) in valid_shots
    #     assert Coordinate(5, 5) not in valid_shots
    #
    # def test_receive_shots_hit(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place a ship
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #
    #     # Receive shots that hit the ship
    #     shots: list[Coordinate] = [Coordinate(0, 0), Coordinate(1, 1)]
    #     hit_ships: list[Ship] = player.receive_shots(shots=shots, round_number=1)
    #
    #     assert len(hit_ships) == 1
    #     assert hit_ships[0].ship_type == ShipType.DESTROYER
    #     assert Coordinate(0, 0) in player.board.shots_received
    #     assert Coordinate(1, 1) in player.board.shots_received
    #
    # def test_receive_shots_miss(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place a ship
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #
    #     # Receive shots that miss
    #     shots: list[Coordinate] = [Coordinate(5, 5)]
    #     hit_ships: list[Ship] = player.receive_shots(shots=shots, round_number=1)
    #
    #     assert len(hit_ships) == 0
    #     assert Coordinate(5, 5) in player.board.shots_received
    #
    # def test_record_hits_made(self):
    #     player: Player = Player("Test Player")
    #
    #     # create 1 hit on DESTROYER and 2 hits on CARRIER
    #     hits: dict[ShipType, int] = {ShipType.DESTROYER: 1, ShipType.CARRIER: 2}
    #     player.record_hits_made(ship_hits=hits, round_number=1)
    #
    #     # verify the hits made and round number they were made in
    #     assert player.hits_made[ShipType.DESTROYER] == [1]
    #     assert player.hits_made[ShipType.CARRIER] == [1, 1]  # Two hits recorded
    #     assert player.hits_made[ShipType.CRUISER] == []
    #
    # def test_record_opponent_ship_sunk(self):
    #     player: Player = Player("Test Player")
    #
    #     player.record_opponent_ship_sunk(ship_type=ShipType.DESTROYER)
    #
    #     assert ShipType.DESTROYER in player.opponent_ships_sunk
    #     assert ShipType.CARRIER not in player.opponent_ships_sunk
    #
    # def test_get_available_shots(self):
    #     player: Player = Player("Test Player")
    #
    #     # No ships placed
    #     assert player.get_available_shots() == 0
    #
    #     # Place some ships
    #     player.place_ship(
    #         ship_type=ShipType.CARRIER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )  # 2 shots
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(2, 0),
    #         direction=Direction.HORIZONTAL,
    #     )  # 1 shot
    #
    #     assert player.get_available_shots() == 3
    #
    #     # Sink destroyer
    #     destroyer: Ship = player.board.ships[1]
    #     assert destroyer.ship_type == ShipType.DESTROYER
    #     destroyer.incoming_shot(Coordinate(2, 0))
    #     destroyer.incoming_shot(Coordinate(2, 1))
    #
    #     assert player.get_available_shots() == 2  # Only carrier shots remain
    #
    # def test_is_defeated(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place a ship
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #
    #     assert not player.is_defeated()
    #
    #     # Sink the ship
    #     destroyer: Ship = player.board.ships[0]
    #     assert destroyer.ship_type == ShipType.DESTROYER
    #     destroyer.incoming_shot(Coordinate(0, 0))
    #     destroyer.incoming_shot(Coordinate(0, 1))
    #
    #     assert player.is_defeated()
    #
    # def test_get_fleet_status(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place ships
    #     player.place_ship(
    #         ship_type=ShipType.DESTROYER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #     player.place_ship(
    #         ship_type=ShipType.CRUISER,
    #         start=Coordinate(2, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #
    #     # FIXME: create a dataclass or enum to encapsulate the FleetStatus
    #     # e.g. dict[ShipType,ShipState] where ShipState is AFLOAT or SUNK
    #     status: dict[ShipType, bool] = player.get_fleet_status()
    #
    #     assert ShipType.DESTROYER in status
    #     assert ShipType.CRUISER in status
    #     assert status[ShipType.DESTROYER] is False  # Not sunk
    #     assert status[ShipType.CRUISER] is False  # Not sunk
    #
    #     # Sink destroyer
    #     destroyer: Ship = player.board.ships[0]
    #     assert destroyer.ship_type == ShipType.DESTROYER
    #     destroyer.incoming_shot(Coordinate(0, 0))
    #     destroyer.incoming_shot(Coordinate(0, 1))
    #
    #     status: dict[ShipType, bool] = player.get_fleet_status()
    #     assert status[ShipType.DESTROYER] is True  # Sunk
    #     assert status[ShipType.CRUISER] is False  # Still afloat
    #
    # # FIXME: this test and the model needs fixing as we shouldn't be able to record 3 hits against a ship that is only 2 spaces long
    # def test_get_hits_on_ship_type(self):
    #     player: Player = Player("Test Player")
    #
    #     # Record some hits
    #     player.record_hits_made(ship_hits={ShipType.DESTROYER: 2}, round_number=1)
    #     player.record_hits_made(ship_hits={ShipType.DESTROYER: 1}, round_number=3)
    #
    #     hits: list[int] = player.get_hits_on_ship_type(ShipType.DESTROYER)
    #     assert hits == [1, 1, 3]  # Two hits in round 1, one in round 3
    #
    #     hits = player.get_hits_on_ship_type(ShipType.CARRIER)
    #     assert hits == []  # No hits recorded
    #
    # def test_get_shots_fired_in_round(self):
    #     player: Player = Player("Test Player")
    #
    #     # Place ship and fire shots
    #     player.place_ship(
    #         ship_type=ShipType.CARRIER,
    #         start=Coordinate(0, 0),
    #         direction=Direction.HORIZONTAL,
    #     )
    #     player.fire_shots(targets=[Coordinate(5, 5), Coordinate(6, 6)], round_number=1)
    #     player.fire_shots(targets=[Coordinate(7, 7)], round_number=2)
    #
    #     round1_shots: list[Coordinate] = player.get_shots_fired_in_round(round_number=1)
    #     assert len(round1_shots) == 2
    #     assert Coordinate(5, 5) in round1_shots
    #     assert Coordinate(6, 6) in round1_shots
    #
    #     round2_shots: list[Coordinate] = player.get_shots_fired_in_round(round_number=2)
    #     assert len(round2_shots) == 1
    #     assert Coordinate(7, 7) in round2_shots
    #
    # def test_get_shots_received_in_round(self):
    #     player: Player = Player("Test Player")
    #
    #     # Receive shots in different rounds
    #     player.receive_shots(shots=[Coordinate(0, 0), Coordinate(1, 1)], round_number=1)
    #     player.receive_shots(shots=[Coordinate(2, 2)], round_number=2)
    #
    #     round1_shots: list[Coordinate] = player.get_shots_received_in_round(
    #         round_number=1
    #     )
    #     assert len(round1_shots) == 2
    #     assert Coordinate(0, 0) in round1_shots
    #     assert Coordinate(1, 1) in round1_shots
    #
    #     round2_shots: list[Coordinate] = player.get_shots_received_in_round(
    #         round_number=2
    #     )
    #     assert len(round2_shots) == 1
    #     assert Coordinate(2, 2) in round2_shots
    #
    # def test_has_all_ships_placed(self):
    #     player: Player = Player("Test Player")
    #
    #     assert not player.has_all_ships_placed()
    #
    #     # Place all required ships
    #     player.place_ship(ShipType.CARRIER, Coordinate(0, 0), Direction.HORIZONTAL)
    #     player.place_ship(ShipType.BATTLESHIP, Coordinate(2, 0), Direction.HORIZONTAL)
    #     player.place_ship(ShipType.CRUISER, Coordinate(4, 0), Direction.HORIZONTAL)
    #     player.place_ship(ShipType.SUBMARINE, Coordinate(6, 0), Direction.HORIZONTAL)
    #     player.place_ship(ShipType.DESTROYER, Coordinate(8, 0), Direction.HORIZONTAL)
    #
    #     assert player.has_all_ships_placed()
    #
    # def test_create_fleet(self):
    #     player: Player = Player("Test Player")
    #
    #     # setup_fleet just initializes tracking structures
    #     # Ships still need to be placed manually
    #     player.create_fleet()
    #
    #     # Should not change the board state
    #     assert len(player.board.ships) == 0
    #     assert not player.has_all_ships_placed()
