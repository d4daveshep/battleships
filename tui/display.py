"""
Display utilities for the TUI interface using Rich library.
"""

from typing import List, Set, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.layout import Layout
from rich.align import Align

from game.models import Coordinate, Ship, ShipType
from game.board import GameBoard
from game.player import Player
from game.game_state import GameState, GamePhase


class GameDisplay:
    """Handles all display logic for the TUI game"""
    
    def __init__(self):
        self.console = Console()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        self.console.clear()
    
    def display_title(self):
        """Display the game title"""
        title = Text("🚢 Fox The Navy 🚢", style="bold blue")
        self.console.print(Align.center(title))
        self.console.print()
    
    def display_game_board(self, player: Player, title: str, 
                          show_ships: bool = True, shots_fired: Optional[Dict[Coordinate, int]] = None,
                          hits_made: Optional[Dict[ShipType, List[int]]] = None, 
                          show_round_numbers: bool = False) -> Table:
        """Create a visual representation of a game board"""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        # Add column headers (A-J) - make columns narrower for more rectangular appearance
        table.add_column("", style="bold", width=1)
        for col in range(10):
            table.add_column(str(col + 1), justify="center", width=2)
        
        # Create the grid
        for row in range(10):
            row_data = [chr(ord('A') + row)]  # Row label (A-J)
            
            for col in range(10):
                coord = Coordinate(row, col)
                cell = self._get_cell_content(coord, player, show_ships, shots_fired, show_round_numbers)
                row_data.append(cell)
            
            table.add_row(*row_data)
        
        return table
    
    def _get_cell_content(self, coord: Coordinate, player: Player, 
                         show_ships: bool, shots_fired: Optional[Dict[Coordinate, int]], 
                         show_round_numbers: bool = False) -> str:
        """Get the content for a single cell in the grid"""
        # Check if there's a shot at this position
        shot_here = coord in player.board.shots_received
        
        # Check if there's a ship at this position
        ship_here = player.board.get_ship_at_position(coord)
        
        # Check if this position was fired at by player
        fired_here = shots_fired and coord in shots_fired
        
        # If we're showing round numbers (shots fired board), prioritize showing round numbers
        if show_round_numbers:
            if fired_here:
                round_num = shots_fired[coord]
                return f"[bold cyan]{round_num}[/bold cyan]"
            else:
                return "[cyan]~[/cyan]"  # Empty water
        else:
            # Normal display logic for ships & shots received board
            if shot_here and ship_here:
                # Hit on ship - show round number in red/yellow
                round_num = player.board.shots_received[coord]
                if ship_here.is_sunk:
                    return f"[bold red]{round_num}[/bold red]"  # Sunk ship hit
                else:
                    return f"[bold yellow]{round_num}[/bold yellow]"  # Hit ship
            elif shot_here:
                # Miss - show round number in blue
                round_num = player.board.shots_received[coord]
                return f"[bold blue]{round_num}[/bold blue]"
            elif fired_here:
                # Show where player has fired (when not showing round numbers)
                if ship_here and show_ships:
                    return f"[bold yellow]{shots_fired[coord]}[/bold yellow]"  # Hit
                else:
                    return f"[bold blue]{shots_fired[coord]}[/bold blue]"  # Miss
            elif ship_here and show_ships:
                # Show ship with letter designation
                ship_letter = self._get_ship_letter(ship_here.ship_type)
                if ship_here.is_sunk:
                    return f"[bold red]{ship_letter}[/bold red]"
                else:
                    return f"[bold green]{ship_letter}[/bold green]"
            else:
                # Empty water
                return "[dim cyan]~[/dim cyan]"
    
    def _get_ship_letter(self, ship_type: ShipType) -> str:
        """Get letter designation for ship types"""
        ship_letters = {
            ShipType.CARRIER: "C",
            ShipType.BATTLESHIP: "B", 
            ShipType.CRUISER: "R",
            ShipType.SUBMARINE: "S",
            ShipType.DESTROYER: "D"
        }
        return ship_letters[ship_type]
    
    def display_opponent_final_board(self, opponent: Player, title_suffix: str = "") -> Table:
        """Display opponent's final board showing all ships at game end"""
        title = f"{opponent.name}'s Final Ship Positions{title_suffix}"
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        # Add column headers - narrower for rectangular appearance
        table.add_column("", style="bold", width=1)
        for col in range(10):
            table.add_column(str(col + 1), justify="center", width=2)
        
        # Create the grid showing all ships and hits
        for row in range(10):
            row_data = [chr(ord('A') + row)]  # Row label (A-J)
            
            for col in range(10):
                coord = Coordinate(row, col)
                
                # Check if there's a shot received at this position
                shot_here = coord in opponent.board.shots_received
                
                # Check if there's a ship at this position
                ship_here = opponent.board.get_ship_at_position(coord)
                
                if shot_here and ship_here:
                    # Hit on ship - show round number in red/yellow
                    round_num = opponent.board.shots_received[coord]
                    if ship_here.is_sunk:
                        cell = f"[bold red]{round_num}[/bold red]"  # Sunk ship hit
                    else:
                        cell = f"[bold yellow]{round_num}[/bold yellow]"  # Hit ship
                elif shot_here:
                    # Miss - show round number in blue
                    round_num = opponent.board.shots_received[coord]
                    cell = f"[bold blue]{round_num}[/bold blue]"
                elif ship_here:
                    # Show ship with letter designation
                    ship_letter = self._get_ship_letter(ship_here.ship_type)
                    if ship_here.is_sunk:
                        cell = f"[bold red]{ship_letter}[/bold red]"
                    else:
                        cell = f"[bold green]{ship_letter}[/bold green]"
                else:
                    # Empty water
                    cell = "[dim cyan]~[/dim cyan]"
                
                row_data.append(cell)
            
            table.add_row(*row_data)
        
        return table
    
    def display_dual_boards(self, player: Player, opponent_shots: Optional[Dict[Coordinate, int]] = None):
        """Display both player boards side by side"""
        # Player's board (shows ships and shots received)
        player_board = self.display_game_board(
            player, 
            f"{player.name}'s Ships & Shots Received",
            show_ships=True
        )
        
        # Shots fired board (shows where player has fired with round numbers)
        shots_board = self.display_game_board(
            player, 
            f"{player.name}'s Shots Fired",
            show_ships=False,
            shots_fired=player.board.shots_fired,
            show_round_numbers=True
        )
        
        # Display side by side
        columns = Columns([player_board, shots_board], equal=True, expand=True)
        self.console.print(columns)
    
    def display_ship_placement_board(self, player: Player, highlight_positions: Optional[List[Coordinate]] = None) -> Table:
        """Display board for ship placement with optional position highlighting"""
        table = Table(title=f"{player.name}'s Ship Placement", show_header=True, header_style="bold magenta")
        
        # Add column headers - narrower for rectangular appearance
        table.add_column("", style="bold", width=1)
        for col in range(10):
            table.add_column(str(col + 1), justify="center", width=2)
        
        # Create the grid
        for row in range(10):
            row_data = [chr(ord('A') + row)]
            
            for col in range(10):
                coord = Coordinate(row, col)
                
                # Check if position should be highlighted
                if highlight_positions and coord in highlight_positions:
                    cell = "[yellow]⭐[/yellow]"
                else:
                    ship = player.board.get_ship_at_position(coord)
                    if ship:
                        cell = "[green]🚢[/green]"
                    else:
                        cell = "[cyan]~[/cyan]"
                
                row_data.append(cell)
            
            table.add_row(*row_data)
        
        return table
    
    def display_ships_status(self, player: Player) -> Table:
        """Display the status of all ships for a player"""
        table = Table(title=f"{player.name}'s Fleet Status", show_header=True)
        table.add_column("Ship", style="bold")
        table.add_column("Length", justify="center")
        table.add_column("Shots", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Hits", justify="center")
        
        for ship_type in ShipType:
            # Find the ship of this type
            ship = None
            for s in player.board.ships:
                if s.ship_type == ship_type:
                    ship = s
                    break
            
            if ship:
                status = "[red]SUNK[/red]" if ship.is_sunk else "[green]AFLOAT[/green]"
                hits = f"{len(ship.hits)}/{ship.length}"
            else:
                status = "[yellow]NOT PLACED[/yellow]"
                hits = "0/0"
            
            table.add_row(
                ship_type.ship_name,
                str(ship_type.length),
                str(ship_type.shots),
                status,
                hits
            )
        
        return table
    
    def display_hits_made(self, player: Player) -> Table:
        """Display hits made on opponent's ships"""
        table = Table(title=f"Hits Made on Opponent", show_header=True)
        table.add_column("Ship", style="bold")
        table.add_column("Hits", justify="center")
        table.add_column("Rounds", justify="left")
        table.add_column("Status", justify="center")
        
        for ship_type in ShipType:
            hits = player.hits_made.get(ship_type, [])
            is_sunk = ship_type in player.opponent_ships_sunk
            
            status = "[red]SUNK[/red]" if is_sunk else "[green]UNKNOWN[/green]"
            rounds = ", ".join(map(str, hits)) if hits else "None"
            
            table.add_row(
                ship_type.ship_name,
                str(len(hits)),
                rounds,
                status
            )
        
        return table
    
    def display_game_status(self, game: GameState) -> Panel:
        """Display current game status"""
        status_text = []
        status_text.append(f"Phase: {game.phase.value.title()}")
        status_text.append(f"Round: {game.current_round}")
        
        if game.phase == GamePhase.PLAYING:
            p1_shots = game.player1.get_available_shots()
            p2_shots = game.player2.get_available_shots()
            status_text.append(f"{game.player1.name} shots available: {p1_shots}")
            status_text.append(f"{game.player2.name} shots available: {p2_shots}")
        
        if game.result:
            if game.winner:
                status_text.append(f"🎉 Winner: {game.winner.name}!")
            else:
                status_text.append("🤝 Game ended in a draw!")
        
        content = "\n".join(status_text)
        return Panel(content, title="Game Status", style="bold blue")
    
    def display_instructions(self, instructions: List[str]) -> Panel:
        """Display instructions in a panel"""
        content = "\n".join(f"• {instruction}" for instruction in instructions)
        return Panel(content, title="Instructions", style="green")
    
    def print(self, *args, **kwargs):
        """Wrapper for console.print"""
        self.console.print(*args, **kwargs)
    
    def input(self, prompt: str) -> str:
        """Wrapper for console.input"""
        return self.console.input(f"[bold cyan]{prompt}[/bold cyan] ")
    
    def print_error(self, message: str):
        """Print an error message"""
        self.console.print(f"[bold red]❌ Error: {message}[/bold red]")
    
    def print_success(self, message: str):
        """Print a success message"""
        self.console.print(f"[bold green]✅ {message}[/bold green]")
    
    def print_info(self, message: str):
        """Print an info message"""
        self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")
    
    def wait_for_key(self, message: str = "Press Enter to continue..."):
        """Wait for user to press enter"""
        self.console.input(f"[dim]{message}[/dim]")