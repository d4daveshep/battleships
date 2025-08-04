#!/usr/bin/env python3
"""
Test the grid changes: rectangular appearance and opponent reveal.
"""

from tui.display import GameDisplay
from game import Player, GameState, ShipType, Coordinate, Direction


def test_rectangular_grids():
    """Test the more rectangular grid appearance"""
    display = GameDisplay()
    
    # Create test player
    player = Player("Test Player")
    
    # Place some ships
    player.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
    player.place_ship(ShipType.CRUISER, Coordinate(2, 2), Direction.VERTICAL)
    
    # Simulate some shots
    player.board.shots_received[Coordinate(0, 0)] = 1
    player.board.shots_received[Coordinate(5, 5)] = 2
    player.board.shots_fired[Coordinate(7, 7)] = 1
    player.board.shots_fired[Coordinate(8, 8)] = 2
    
    # Hit the destroyer
    for ship in player.board.ships:
        if ship.ship_type == ShipType.DESTROYER:
            ship.hit(Coordinate(0, 0))
    
    print("Testing rectangular grid appearance...")
    display.display_dual_boards(player)
    
    # Test ship placement board too
    print("\nShip placement board:")
    placement_board = display.display_ship_placement_board(player)
    display.print(placement_board)


def test_opponent_reveal():
    """Test opponent ship position reveal at game end"""
    display = GameDisplay()
    
    # Create two players
    player1 = Player("Alice")
    player2 = Player("Bob")
    
    # Place ships for both players
    player1.place_ship(ShipType.DESTROYER, Coordinate(0, 0), Direction.HORIZONTAL)
    player1.place_ship(ShipType.CRUISER, Coordinate(2, 2), Direction.VERTICAL)
    
    player2.place_ship(ShipType.DESTROYER, Coordinate(1, 1), Direction.HORIZONTAL)
    player2.place_ship(ShipType.BATTLESHIP, Coordinate(5, 5), Direction.VERTICAL)
    
    # Simulate some battle damage
    player1.board.shots_received[Coordinate(0, 0)] = 1  # Hit destroyer
    player1.board.shots_received[Coordinate(3, 3)] = 2  # Miss
    
    player2.board.shots_received[Coordinate(1, 1)] = 1  # Hit destroyer  
    player2.board.shots_received[Coordinate(1, 2)] = 3  # Sink destroyer
    player2.board.shots_received[Coordinate(7, 7)] = 2  # Miss
    
    # Apply hits to ships
    for ship in player1.board.ships:
        if ship.ship_type == ShipType.DESTROYER:
            ship.hit(Coordinate(0, 0))
    
    for ship in player2.board.ships:
        if ship.ship_type == ShipType.DESTROYER:
            ship.hit(Coordinate(1, 1))
            ship.hit(Coordinate(1, 2))  # Sink it
    
    print("\n" + "="*80)
    print("Testing opponent ship position reveal...")
    
    # Show player 1's final board
    p1_final = display.display_opponent_final_board(player1, " (Your Ships)")
    display.print(p1_final)
    
    print()
    # Show player 2's final board (opponent)
    p2_final = display.display_opponent_final_board(player2, " (Opponent's Ships)")  
    display.print(p2_final)
    
    print("\n" + "="*80)
    print("Side-by-side comparison:")
    from rich.columns import Columns
    display.print(Columns([p1_final, p2_final], equal=True, expand=True))


if __name__ == "__main__":
    test_rectangular_grids()
    test_opponent_reveal()