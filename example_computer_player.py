#!/usr/bin/env python3
"""
Example demonstrating computer player functionality in Fox The Navy game.
"""

from game import Player, GameState, create_computer_player, ComputerPlayer

def main():
    print("Fox The Navy - Computer Player Example")
    print("=" * 40)
    
    # Create a human player and computer player
    print("\n1. Creating players...")
    human_player = Player("Alice")
    computer_player, computer_logic = create_computer_player("Computer Bot")
    
    print(f"Human player: {human_player.name} (Computer: {human_player.is_computer})")
    print(f"Computer player: {computer_player.name} (Computer: {computer_player.is_computer})")
    
    # Demonstrate computer auto-placement
    print("\n2. Auto-placing computer ships...")
    result = computer_logic.auto_place_ships()
    print(f"Auto-placement successful: {result}")
    print(f"Computer ships placed: {len(computer_player.board.ships)}")
    
    # Show computer ship positions
    print("\n3. Computer ship positions:")
    for ship in computer_player.board.ships:
        positions = [pos.to_string() for pos in ship.positions]
        print(f"  {ship.ship_type.ship_name} ({ship.ship_type.length}): {positions}")
    
    # Demonstrate deterministic placement
    print("\n4. Deterministic placement example:")
    computer_player2 = Player("Computer 2", is_computer=True)
    computer_logic2 = ComputerPlayer(computer_player2)
    
    result2 = computer_logic2.auto_place_ships_deterministic()
    print(f"Deterministic placement successful: {result2}")
    
    print("\nDeterministic ship positions:")
    for ship in computer_player2.board.ships:
        positions = [pos.to_string() for pos in ship.positions]
        print(f"  {ship.ship_type.ship_name} ({ship.ship_type.length}): {positions}")
    
    # Demonstrate game integration
    print("\n5. Game integration example:")
    game = GameState("Human", "Computer", player2_is_computer=True)
    
    # Place ships for human player manually (in real game, this would be via UI)
    from game import ShipType, Coordinate, Direction
    game.player1.place_ship(ShipType.CARRIER, Coordinate(0, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.BATTLESHIP, Coordinate(2, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.CRUISER, Coordinate(4, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.SUBMARINE, Coordinate(6, 0), Direction.HORIZONTAL)
    game.player1.place_ship(ShipType.DESTROYER, Coordinate(8, 0), Direction.HORIZONTAL)
    
    print("Human ships placed manually")
    print(f"Computer ships placed: {game.player2.has_all_ships_placed()}")
    
    # Start game - computer ships should be auto-placed
    game_started = game.start_game()
    print(f"Game started: {game_started}")
    print(f"Computer ships now placed: {game.player2.has_all_ships_placed()}")
    print(f"Game phase: {game.phase}")
    
    print("\nComputer player implementation complete!")


if __name__ == "__main__":
    main()