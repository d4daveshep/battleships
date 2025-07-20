"""
Game controller for the TUI interface - handles game flow and player interactions.
"""

from typing import List, Optional
from game.models import Coordinate, ShipType, Direction
from game.player import Player
from game.game_state import GameState, GamePhase, GameResult
from game.computer_player import create_computer_player
from .display import GameDisplay
from .input_handler import InputHandler


class TUIGameController:
    """Controls the game flow for the TUI interface"""
    
    def __init__(self):
        self.display = GameDisplay()
        self.input_handler = InputHandler()
        self.game: Optional[GameState] = None
    
    def start_new_game(self):
        """Start a new game"""
        self.display.clear_screen()
        self.display.display_title()
        
        # Get player names
        human_name = self.display.input("Enter your name") or "Player"
        
        # Ask if playing against computer
        vs_computer = self.input_handler.get_yes_no(
            self.display, 
            "Play against computer?", 
            default=True
        )
        
        if vs_computer:
            self.game = GameState(human_name, "Computer", player2_is_computer=True)
        else:
            opponent_name = self.display.input("Enter opponent's name") or "Opponent"
            self.game = GameState(human_name, opponent_name)
        
        self.display.print_success(f"Game created: {self.game.player1.name} vs {self.game.player2.name}")
        
        # Setup phase
        self.setup_phase()
        
        # Play the game
        if self.game.phase == GamePhase.PLAYING:
            self.play_game()
    
    def setup_phase(self):
        """Handle ship placement for human players"""
        self.display.print_info("Ship placement phase")
        
        # Place ships for Player 1 (always human)
        self.place_ships_for_player(self.game.player1)
        
        # Place ships for Player 2 if human
        if not self.game.player2.is_computer:
            self.display.wait_for_key("Pass the computer to the next player...")
            self.display.clear_screen()
            self.place_ships_for_player(self.game.player2)
        
        # Start the game (computer ships auto-placed if needed)
        success = self.game.start_game()
        if success:
            self.display.print_success("All ships placed! Game starting...")
        else:
            self.display.print_error("Failed to start game. Please try again.")
    
    def place_ships_for_player(self, player: Player):
        """Handle ship placement for a specific player"""
        self.display.print_info(f"\n{player.name}, place your ships!")
        
        ships_to_place = list(ShipType)
        
        for ship_type in ships_to_place:
            placed = False
            while not placed:
                self.display.clear_screen()
                self.display.display_title()
                
                # Show current board
                board = self.display.display_ship_placement_board(player)
                self.display.print(board)
                
                # Show ships status
                ships_status = self.display.display_ships_status(player)
                self.display.print(ships_status)
                
                try:
                    # Get ship placement from user
                    coord, direction = self.input_handler.get_ship_placement(self.display, ship_type)
                    
                    # Try to place the ship
                    success = player.place_ship(ship_type, coord, direction)
                    
                    if success:
                        self.display.print_success(f"{ship_type.ship_name} placed successfully!")
                        placed = True
                        self.display.wait_for_key()
                    else:
                        self.display.print_error("Cannot place ship there. Check spacing rules and boundaries.")
                        self.display.wait_for_key()
                        
                except KeyboardInterrupt:
                    self.display.print_info("Game cancelled.")
                    return
        
        self.display.print_success(f"All ships placed for {player.name}!")
        self.display.wait_for_key()
    
    def play_game(self):
        """Main game loop"""
        while self.game.phase == GamePhase.PLAYING:
            # Player 1's turn (always human)
            if not self.game.is_player_turn_complete(self.game.player1.name):
                self.human_turn(self.game.player1)
            
            # Player 2's turn
            if not self.game.is_player_turn_complete(self.game.player2.name):
                if self.game.player2.is_computer:
                    self.computer_turn(self.game.player2)
                else:
                    self.display.wait_for_key("Pass the computer to the next player...")
                    self.human_turn(self.game.player2)
            
            # Check if round is complete
            if (self.game.player1_shots_submitted and self.game.player2_shots_submitted):
                self.display_round_results()
        
        # Game finished
        self.display_game_end()
    
    def human_turn(self, player: Player):
        """Handle a human player's turn"""
        self.display.clear_screen()
        self.display.display_title()
        
        # Show game status
        status = self.display.display_game_status(self.game)
        self.display.print(status)
        
        # Show dual boards
        self.display.display_dual_boards(player)
        
        # Show fleet status and hits made
        fleet_status = self.display.display_ships_status(player)
        hits_made = self.display.display_hits_made(player)
        
        from rich.columns import Columns
        self.display.print(Columns([fleet_status, hits_made], equal=True))
        
        # Get shots from player
        shots_needed = player.get_available_shots()
        
        if shots_needed == 0:
            self.display.print_info("You have no ships left - no shots available!")
            return
        
        self.display.print_info(f"You have {shots_needed} shots this round.")
        
        shots = self.input_handler.get_valid_coordinates_list(
            self.display,
            f"Enter {shots_needed} target coordinates (e.g., 'A1 B2 C3')",
            shots_needed
        )
        
        # Validate shots haven't been fired before
        valid_shots = []
        for shot in shots:
            if shot not in player.board.shots_fired:
                valid_shots.append(shot)
            else:
                self.display.print_error(f"Already fired at {shot.to_string()}")
        
        if len(valid_shots) != shots_needed:
            self.display.print_error("Some shots were invalid. Please try again.")
            self.display.wait_for_key()
            return self.human_turn(player)  # Retry
        
        # Submit shots
        try:
            success = self.game.submit_shots(player.name, valid_shots)
            if success:
                self.display.print_success("Shots submitted!")
                self.display.wait_for_key()
            else:
                self.display.print_error("Failed to submit shots.")
        except ValueError as e:
            self.display.print_error(str(e))
            self.display.wait_for_key()
    
    def computer_turn(self, player: Player):
        """Handle a computer player's turn"""
        from game.computer_player import ComputerPlayer
        
        shots_needed = player.get_available_shots()
        
        if shots_needed == 0:
            return
        
        # Simple random shot selection for computer
        available_positions = []
        for row in range(10):
            for col in range(10):
                coord = Coordinate(row, col)
                if coord not in player.board.shots_fired:
                    available_positions.append(coord)
        
        # Select random shots
        import random
        computer_shots = random.sample(available_positions, min(shots_needed, len(available_positions)))
        
        # Submit shots
        try:
            self.game.submit_shots(player.name, computer_shots)
            shot_strs = [shot.to_string() for shot in computer_shots]
            self.display.print_info(f"Computer fires at: {', '.join(shot_strs)}")
        except ValueError as e:
            self.display.print_error(f"Computer shot error: {e}")
    
    def display_round_results(self):
        """Display results after both players have fired"""
        if not self.game.round_history:
            return
        
        round_result = self.game.round_history[-1]
        
        self.display.clear_screen()
        self.display.display_title()
        
        self.display.print(f"[bold yellow]Round {round_result.round_number} Results[/bold yellow]")
        self.display.print()
        
        # Show shots fired
        p1_shots = [shot.to_string() for shot in round_result.player1_shots]
        p2_shots = [shot.to_string() for shot in round_result.player2_shots]
        
        self.display.print(f"[blue]{self.game.player1.name} fired at:[/blue] {', '.join(p1_shots)}")
        self.display.print(f"[blue]{self.game.player2.name} fired at:[/blue] {', '.join(p2_shots)}")
        self.display.print()
        
        # Show hits
        if round_result.player1_hits:
            for ship_type, hits in round_result.player1_hits.items():
                self.display.print(f"[green]{self.game.player1.name} hit {ship_type.ship_name} {hits} times![/green]")
        
        if round_result.player2_hits:
            for ship_type, hits in round_result.player2_hits.items():
                self.display.print(f"[green]{self.game.player2.name} hit {ship_type.ship_name} {hits} times![/green]")
        
        # Show sunk ships
        if round_result.ships_sunk_this_round:
            for player_name, ship_type in round_result.ships_sunk_this_round:
                self.display.print(f"[red]💥 {player_name}'s {ship_type.ship_name} was SUNK![/red]")
        
        if not round_result.player1_hits and not round_result.player2_hits:
            self.display.print("[yellow]Both players missed all their shots this round.[/yellow]")
        
        self.display.wait_for_key("Press Enter to continue...")
    
    def display_game_end(self):
        """Display game end screen"""
        self.display.clear_screen()
        self.display.display_title()
        
        # Show final status
        status = self.display.display_game_status(self.game)
        self.display.print(status)
        
        # Show final boards
        self.display.print("\n[bold]Final Game State[/bold]")
        self.display.display_dual_boards(self.game.player1)
        
        # Show final fleet status for both players
        p1_fleet = self.display.display_ships_status(self.game.player1)
        p2_fleet = self.display.display_ships_status(self.game.player2)
        
        from rich.columns import Columns
        self.display.print(Columns([p1_fleet, p2_fleet], equal=True))
        
        self.display.wait_for_key("Press Enter to return to menu...")
    
    def run(self):
        """Main entry point"""
        try:
            while True:
                self.display.clear_screen()
                self.display.display_title()
                
                options = [
                    "Start New Game",
                    "Exit"
                ]
                
                choice = self.input_handler.get_menu_choice(self.display, options, "Select an option")
                
                if choice == 0:  # Start New Game
                    self.start_new_game()
                elif choice == 1:  # Exit
                    self.display.print_info("Thanks for playing Fox The Navy!")
                    break
                    
        except KeyboardInterrupt:
            self.display.print_info("\nGame terminated by user. Goodbye!")
        except Exception as e:
            self.display.print_error(f"An unexpected error occurred: {e}")
            self.display.wait_for_key()


if __name__ == "__main__":
    controller = TUIGameController()
    controller.run()