# import pytest
# from tui.display import GameDisplay
# from tui.input_handler import InputHandler
# from game.models import Coordinate, ShipType, Direction
# from game.player import Player
#
#
# class TestGameDisplay:
#     def test_game_display_creation(self):
#         display = GameDisplay()
#         assert display.console is not None
#
#     def test_display_ship_placement_board(self):
#         display = GameDisplay()
#         player = Player("Test")
#
#         # Should not raise an exception
#         table = display.display_ship_placement_board(player)
#         assert table is not None
#
#     def test_display_ships_status(self):
#         display = GameDisplay()
#         player = Player("Test")
#         player.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
#
#         table = display.display_ships_status(player)
#         assert table is not None
#
#
# class TestInputHandler:
#     def test_parse_coordinate_valid(self):
#         test_cases = [
#             ("A1", Coordinate(0, 0)),
#             ("J10", Coordinate(9, 9)),
#             ("E5", Coordinate(4, 4)),
#             ("a1", Coordinate(0, 0)),  # Case insensitive
#         ]
#
#         for input_str, expected in test_cases:
#             result = InputHandler.parse_coordinate(input_str)
#             assert result == expected
#
#     def test_parse_coordinate_invalid(self):
#         invalid_cases = ["K1", "A11", "A0", "1A", "invalid", "", "A"]
#
#         for invalid_input in invalid_cases:
#             result = InputHandler.parse_coordinate(invalid_input)
#             assert result is None
#
#     def test_parse_coordinates_list(self):
#         # Test space-separated
#         coords = InputHandler.parse_coordinates_list("A1 B2 C3")
#         expected = [Coordinate(0, 0), Coordinate(1, 1), Coordinate(2, 2)]
#         assert coords == expected
#
#         # Test comma-separated
#         coords = InputHandler.parse_coordinates_list("A1,B2,C3")
#         assert coords == expected
#
#         # Test mixed separators
#         coords = InputHandler.parse_coordinates_list("A1, B2 C3")
#         assert coords == expected
#
#         # Test empty string
#         coords = InputHandler.parse_coordinates_list("")
#         assert coords == []
#
#     def test_parse_direction_valid(self):
#         test_cases = [
#             ("h", Direction.HORIZONTAL),
#             ("horizontal", Direction.HORIZONTAL),
#             ("v", Direction.VERTICAL),
#             ("vertical", Direction.VERTICAL),
#             ("ne", Direction.DIAGONAL_NE),
#             ("northeast", Direction.DIAGONAL_NE),
#             ("se", Direction.DIAGONAL_SE),
#             ("southeast", Direction.DIAGONAL_SE),
#         ]
#
#         for input_str, expected in test_cases:
#             result = InputHandler.parse_direction(input_str)
#             assert result == expected
#
#     def test_parse_direction_invalid(self):
#         invalid_cases = ["invalid", "n", "s", "e", "w", "", "diagonal"]
#
#         for invalid_input in invalid_cases:
#             result = InputHandler.parse_direction(invalid_input)
#             assert result is None
#
#     def test_validate_coordinate_format(self):
#         valid_cases = ["A1", "J10", "E5", "a1"]
#         invalid_cases = ["K1", "A11", "A0", "1A", "invalid"]
#
#         for valid in valid_cases:
#             assert InputHandler.validate_coordinate_format(valid)
#
#         for invalid in invalid_cases:
#             assert not InputHandler.validate_coordinate_format(invalid)
