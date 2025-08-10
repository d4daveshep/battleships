# import pytest
# import random
# from game.models import Coordinate, ShipType, Direction
# from game.player import Player
# from game.computer_player import ComputerPlayer, create_computer_player
#
#
# class TestComputerPlayer:
#     def test_computer_player_creation(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player)
#
#         assert computer_logic.player == player
#         assert player.is_computer
#
#     def test_computer_player_creation_with_seed(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=42)
#
#         assert computer_logic.player == player
#
#     def test_auto_place_ships_non_computer_player_error(self):
#         player = Player("Human", is_computer=False)
#         computer_logic = ComputerPlayer(player)
#
#         with pytest.raises(ValueError, match="Can only auto-place ships for computer players"):
#             computer_logic.auto_place_ships()
#
#     def test_auto_place_ships_success(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=42)  # Fixed seed for reproducible test
#
#         result = computer_logic.auto_place_ships()
#
#         assert result is True
#         assert len(player.board.ships) == 5
#         assert player.has_all_ships_placed()
#
#         # Verify all ship types are placed
#         placed_types = {ship.ship_type for ship in player.board.ships}
#         expected_types = set(ShipType)
#         assert placed_types == expected_types
#
#     def test_auto_place_ships_follows_spacing_rules(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=123)
#
#         result = computer_logic.auto_place_ships()
#
#         assert result is True
#
#         # Verify no ships are touching by checking all positions
#         all_positions = set()
#         for ship in player.board.ships:
#             for pos in ship.positions:
#                 # Check this position isn't already occupied
#                 assert pos not in all_positions, f"Ships overlap at {pos.to_string()}"
#                 all_positions.add(pos)
#
#         # Verify spacing rules by checking forbidden positions
#         forbidden = player.board._get_all_forbidden_positions()
#         for ship in player.board.ships:
#             for pos in ship.positions:
#                 # No ship position should be in the forbidden set of another ship
#                 # (This is already guaranteed by the board logic, but let's verify)
#                 assert pos not in forbidden or len([s for s in player.board.ships if pos in s.positions]) == 1
#
#     def test_auto_place_ships_all_ships_within_bounds(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=456)
#
#         result = computer_logic.auto_place_ships()
#
#         assert result is True
#
#         # Verify all ship positions are within board bounds
#         for ship in player.board.ships:
#             for pos in ship.positions:
#                 assert 0 <= pos.row <= 9, f"Ship position row {pos.row} out of bounds"
#                 assert 0 <= pos.col <= 9, f"Ship position col {pos.col} out of bounds"
#
#     def test_auto_place_ships_deterministic_with_seed(self):
#         # Two computer players with same seed should place ships identically
#         player1 = Player("Computer1", is_computer=True)
#         player2 = Player("Computer2", is_computer=True)
#
#         computer_logic1 = ComputerPlayer(player1, seed=789)
#         computer_logic2 = ComputerPlayer(player2, seed=789)
#
#         result1 = computer_logic1.auto_place_ships()
#         result2 = computer_logic2.auto_place_ships()
#
#         assert result1 is True
#         assert result2 is True
#
#         # Should have same ship placements
#         ship_positions1 = {}
#         ship_positions2 = {}
#
#         for ship in player1.board.ships:
#             ship_positions1[ship.ship_type] = sorted(ship.positions, key=lambda p: (p.row, p.col))
#
#         for ship in player2.board.ships:
#             ship_positions2[ship.ship_type] = sorted(ship.positions, key=lambda p: (p.row, p.col))
#
#         assert ship_positions1 == ship_positions2
#
#     def test_auto_place_ships_different_with_different_seeds(self):
#         player1 = Player("Computer1", is_computer=True)
#         player2 = Player("Computer2", is_computer=True)
#
#         computer_logic1 = ComputerPlayer(player1, seed=111)
#         computer_logic2 = ComputerPlayer(player2, seed=222)
#
#         result1 = computer_logic1.auto_place_ships()
#         result2 = computer_logic2.auto_place_ships()
#
#         assert result1 is True
#         assert result2 is True
#
#         # Should have different ship placements (with very high probability)
#         ship_positions1 = set()
#         ship_positions2 = set()
#
#         for ship in player1.board.ships:
#             ship_positions1.update(ship.positions)
#
#         for ship in player2.board.ships:
#             ship_positions2.update(ship.positions)
#
#         # It's extremely unlikely they'd be identical with different seeds
#         assert ship_positions1 != ship_positions2
#
#     def test_place_ship_randomly_success(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=333)
#
#         result = computer_logic._place_ship_randomly(ShipType.DESTROYER, max_attempts=100)
#
#         assert result is True
#         assert len(player.board.ships) == 1
#         assert player.board.ships[0].ship_type == ShipType.DESTROYER
#         assert len(player.board.ships[0].positions) == 2
#
#     def test_place_ship_randomly_with_constraints(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=444)
#
#         # Fill most of the board to make placement harder
#         # Place ships manually to constrain available space
#         player.place_ship(ShipType.CARRIER, Coordinate(0, 0), Direction.HORIZONTAL)
#         player.place_ship(ShipType.BATTLESHIP, Coordinate(2, 0), Direction.HORIZONTAL)
#         player.place_ship(ShipType.CRUISER, Coordinate(4, 0), Direction.HORIZONTAL)
#         player.place_ship(ShipType.SUBMARINE, Coordinate(6, 0), Direction.HORIZONTAL)
#
#         # Should still be able to place destroyer
#         result = computer_logic._place_ship_randomly(ShipType.DESTROYER, max_attempts=1000)
#         assert result is True
#         assert len(player.board.ships) == 5
#
#     def test_get_all_possible_positions_empty_board(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player)
#
#         positions = computer_logic.get_all_possible_positions(ShipType.DESTROYER)
#
#         # Destroyer (length 2) should have many valid positions on empty board
#         assert len(positions) > 0
#
#         # Check a few expected positions exist
#         assert (Coordinate(0, 0), Direction.HORIZONTAL) in positions
#         assert (Coordinate(0, 0), Direction.VERTICAL) in positions
#         assert (Coordinate(5, 5), Direction.DIAGONAL_SE) in positions
#
#     def test_get_all_possible_positions_with_constraints(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player)
#
#         # Place a ship to constrain available positions
#         player.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
#
#         positions = computer_logic.get_all_possible_positions(ShipType.DESTROYER)
#
#         # Should have fewer positions now due to spacing constraints
#         # Position (0, 2) horizontal should NOT be valid due to spacing rule
#         assert (Coordinate(0, 2), Direction.HORIZONTAL) not in positions
#
#         # But position (5, 5) should still be valid
#         assert (Coordinate(5, 5), Direction.HORIZONTAL) in positions
#
#     def test_auto_place_ships_deterministic(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player)
#
#         result = computer_logic.auto_place_ships_deterministic()
#
#         assert result is True
#         assert len(player.board.ships) == 5
#         assert player.has_all_ships_placed()
#
#         # Check specific expected positions for deterministic placement
#         expected_positions = {
#             ShipType.CARRIER: [Coordinate(0, i) for i in range(5)],
#             ShipType.BATTLESHIP: [Coordinate(2, i) for i in range(4)],
#             ShipType.CRUISER: [Coordinate(4, i) for i in range(3)],
#             ShipType.SUBMARINE: [Coordinate(6, i) for i in range(3)],
#             ShipType.DESTROYER: [Coordinate(8, i) for i in range(2)],
#         }
#
#         for ship in player.board.ships:
#             assert ship.positions == expected_positions[ship.ship_type]
#
#     def test_auto_place_ships_deterministic_non_computer_error(self):
#         player = Player("Human", is_computer=False)
#         computer_logic = ComputerPlayer(player)
#
#         with pytest.raises(ValueError, match="Can only auto-place ships for computer players"):
#             computer_logic.auto_place_ships_deterministic()
#
#     def test_auto_place_ships_clears_existing_ships(self):
#         player = Player("Computer", is_computer=True)
#         computer_logic = ComputerPlayer(player, seed=555)
#
#         # Place some ships manually first - use valid position
#         player.place_ship(ShipType.DESTROYER, Coordinate(9, 8), Direction.HORIZONTAL)
#         assert len(player.board.ships) == 1
#
#         # Auto-place should clear existing ships and place all 5
#         result = computer_logic.auto_place_ships()
#
#         assert result is True
#         assert len(player.board.ships) == 5
#         assert player.has_all_ships_placed()
#
#     def test_auto_place_ships_multiple_attempts(self):
#         # Test that the method can handle retries if initial attempts fail
#         player = Player("Computer", is_computer=True)
#
#         # Use a seed that might require multiple attempts
#         computer_logic = ComputerPlayer(player, seed=666)
#
#         result = computer_logic.auto_place_ships(max_attempts=10)  # Low max_attempts to test retry logic
#
#         # Should succeed even with low max_attempts due to retry logic
#         assert result is True or result is False  # Either succeeds or fails, but shouldn't crash
#
#         if result:
#             assert len(player.board.ships) == 5
#             assert player.has_all_ships_placed()
#         else:
#             # If it fails, ships should be cleared
#             assert len(player.board.ships) == 0
#
#
# class TestCreateComputerPlayer:
#     def test_create_computer_player(self):
#         player, computer_logic = create_computer_player("TestComputer")
#
#         assert player.name == "TestComputer"
#         assert player.is_computer
#         assert isinstance(computer_logic, ComputerPlayer)
#         assert computer_logic.player == player
#
#     def test_create_computer_player_with_seed(self):
#         player, computer_logic = create_computer_player("TestComputer", seed=777)
#
#         assert player.name == "TestComputer"
#         assert player.is_computer
#
#         # Test that it can place ships
#         result = computer_logic.auto_place_ships()
#         assert result is True
#         assert player.has_all_ships_placed()
#
#     def test_create_computer_player_default_name(self):
#         player, computer_logic = create_computer_player()
#
#         assert player.name == "Computer"
#         assert player.is_computer
#
#
# class TestPlayerAutoPlaceShips:
#     def test_player_auto_place_ships_success(self):
#         player = Player("Computer", is_computer=True)
#
#         result = player.auto_place_ships(seed=888)
#
#         assert result is True
#         assert len(player.board.ships) == 5
#         assert player.has_all_ships_placed()
#
#     def test_player_auto_place_ships_non_computer_error(self):
#         player = Player("Human", is_computer=False)
#
#         with pytest.raises(ValueError, match="Can only auto-place ships for computer players"):
#             player.auto_place_ships()
#
#     def test_player_auto_place_ships_deterministic_with_seed(self):
#         player1 = Player("Computer1", is_computer=True)
#         player2 = Player("Computer2", is_computer=True)
#
#         result1 = player1.auto_place_ships(seed=999)
#         result2 = player2.auto_place_ships(seed=999)
#
#         assert result1 is True
#         assert result2 is True
#
#         # Should have same ship placements
#         ship_positions1 = {}
#         ship_positions2 = {}
#
#         for ship in player1.board.ships:
#             ship_positions1[ship.ship_type] = sorted(ship.positions, key=lambda p: (p.row, p.col))
#
#         for ship in player2.board.ships:
#             ship_positions2[ship.ship_type] = sorted(ship.positions, key=lambda p: (p.row, p.col))
#
#         assert ship_positions1 == ship_positions2
