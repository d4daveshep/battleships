#!/usr/bin/env python3
"""
Demo script showing the TUI game interface components.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from game import GameState, ShipType, Coordinate, Direction
from tui.display import GameDisplay


def demo_game_setup():
    """Demo the game setup and display"""
    console = Console()
    display = GameDisplay()
    
    console.clear()
    
    # Show title
    title = Text("🚢 Fox The Navy - TUI Demo 🚢", style="bold blue")
    console.print(Align.center(title))
    console.print()
    
    # Create a demo game
    game = GameState("Alice", "Computer Bot", player2_is_computer=True)
    
    # Place ships for human player
    game.player1.place_ship(ShipType.CARRIER, Coordinate(1, 1), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.BATTLESHIP, Coordinate(3, 2), Direction.VERTICAL)
    game.player1.place_ship(ShipType.CRUISER, Coordinate(0, 7), Direction.DIAGONAL_SE)
    game.player1.place_ship(ShipType.SUBMARINE, Coordinate(7, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.DESTROYER, Coordinate(9, 8), Direction.HORIZONTAL)
    
    # Start game (auto-places computer ships)
    game.start_game()
    
    # Simulate some shots
    game.player1.board.shots_fired[Coordinate(0, 0)] = 1
    game.player1.board.shots_fired[Coordinate(1, 0)] = 1
    game.player1.board.shots_fired[Coordinate(5, 5)] = 1
    
    # Simulate receiving some shots
    game.player1.board.shots_received[Coordinate(1, 1)] = 1  # Hit carrier
    game.player1.board.shots_received[Coordinate(8, 8)] = 1  # Miss
    game.player1.board.shots_received[Coordinate(3, 2)] = 1  # Hit battleship
    
    # Update ship hits
    for ship in game.player1.board.ships:
        if ship.ship_type == ShipType.CARRIER:
            ship.hit(Coordinate(1, 1))
        elif ship.ship_type == ShipType.BATTLESHIP:
            ship.hit(Coordinate(3, 2))
    
    # Show game status
    status = display.display_game_status(game)
    console.print(status)
    console.print()
    
    # Show dual boards
    console.print("[bold yellow]Player's View:[/bold yellow]")
    display.display_dual_boards(game.player1)
    console.print()
    
    # Show fleet status
    fleet_status = display.display_ships_status(game.player1)
    hits_made = display.display_hits_made(game.player1)
    
    from rich.columns import Columns
    console.print(Columns([fleet_status, hits_made], equal=True))
    
    console.print()
    console.print("\n[bold magenta]New Features Demonstrated:[/bold magenta]")
    console.print("1. [bold cyan]Shots Fired board[/bold cyan]: Shows round numbers when you fired")
    console.print("2. [bold yellow]Ships & Shots Received board[/bold yellow]: Shows colored round numbers")
    console.print("   • [bold red]Red numbers[/bold red] = Hits on sunk ships")
    console.print("   • [bold yellow]Yellow numbers[/bold yellow] = Hits on afloat ships") 
    console.print("   • [bold blue]Blue numbers[/bold blue] = Misses")
    console.print("   • [bold green]Letters (C/B/R/S/D)[/bold green] = Unhit ship positions")
    console.print("3. [bold green]Random ship placement[/bold green]: Option during setup for quick placement")
    
    console.print("\n[bold green]Demo completed! Run 'uv run python play.py' to play the actual game.[/bold green]")


if __name__ == "__main__":
    demo_game_setup()