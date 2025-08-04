#!/usr/bin/env python3
"""
Test script for TUI functionality
"""

from tui.display import GameDisplay
from tui.input_handler import InputHandler
from game import Player, GameState, ShipType, Coordinate, Direction


def test_display():
    """Test the display functionality"""
    display = GameDisplay()
    
    print("Testing display functionality...")
    
    # Create test player with some ships
    player = Player("Test Player")
    player.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
    player.place_ship(ShipType.CRUISER, Coordinate(2, 0), Direction.VERTICAL)
    
    # Test ship placement board
    board = display.display_ship_placement_board(player)
    display.print(board)
    
    # Test ships status
    ships_status = display.display_ships_status(player)
    display.print(ships_status)
    
    print("Display test completed!")


def test_input_handler():
    """Test input handler functionality"""
    print("Testing input handler...")
    
    # Test coordinate parsing
    test_coords = ["A1", "J10", "E5", "invalid", "K1"]
    
    for coord_str in test_coords:
        coord = InputHandler.parse_coordinate(coord_str)
        print(f"'{coord_str}' -> {coord}")
    
    # Test coordinates list parsing
    coords_list = InputHandler.parse_coordinates_list("A1 B2 C3")
    print(f"'A1 B2 C3' -> {coords_list}")
    
    # Test direction parsing
    directions = ["h", "vertical", "ne", "southeast", "invalid"]
    for dir_str in directions:
        direction = InputHandler.parse_direction(dir_str)
        print(f"'{dir_str}' -> {direction}")
    
    print("Input handler test completed!")


def test_game_setup():
    """Test basic game setup"""
    print("Testing game setup...")
    
    # Create a game
    game = GameState("Human", "Computer", player2_is_computer=True)
    
    # Place ships for human player
    game.player1.place_ship(ShipType.CARRIER, Coordinate(0, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.BATTLESHIP, Coordinate(2, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.CRUISER, Coordinate(4, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.SUBMARINE, Coordinate(6, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.DESTROYER, Coordinate(8, 0), Direction.HORIZONTAL)
    
    print(f"Human ships placed: {game.player1.has_all_ships_placed()}")
    print(f"Computer ships placed: {game.player2.has_all_ships_placed()}")
    
    # Start game (should auto-place computer ships)
    success = game.start_game()
    print(f"Game started: {success}")
    print(f"Computer ships now placed: {game.player2.has_all_ships_placed()}")
    
    display = GameDisplay()
    status = display.display_game_status(game)
    display.print(status)
    
    print("Game setup test completed!")


if __name__ == "__main__":
    test_display()
    print("\n" + "="*50 + "\n")
    test_input_handler()
    print("\n" + "="*50 + "\n")
    test_game_setup()