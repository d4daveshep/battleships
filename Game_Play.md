# Game Play per Round

## Starting the game

- Each player enters their name OR a single player plays a computer opponent.
- Each player places their ships (according to the ship placement rules)

## Starting state for a Round

- Round numbers increment sequentially, starting from 1
- Game boards are in sync between shots fired and shots received, this means:
  - Each player knows where they have previously fired and which ships they have hit in which rounds, but not the exact coordinates of each hit.
  - Each player knows where they have received shots from their opponent and where each of their ships have been hit on what round.
- Each player knows how many shots they have available to fire in the round

## Steps in a Round

1. Each player aims their shots. This means they select the coordinates on their shots_fired board where they want to fire their available shots.
2. The coordinates of each player's aimed shots are submitted (fired) to the game controller.
3. The game controller:
   - Validates the shots fired by each player.
     - Number of shots fired must be less or equal to the number of shots available to that player.
     - Shots fired must be unique (i.e. can't fire at an already fired upon location)
   - Enters the shots fired in the players shots_fired board (store the round number at the coordinates of each shot)
   - Enters the shots fired in the opponents shots_received board (store the round number at the coordinates of each shot received)
   - Enters any shots that hit a ship (store the round number in the record for that ship)
   - Mark any ships as sunk if they have received a hit on each of their coordinates
   - Tells the player firing the shots how many (if any) shots were hits on their opponents ships
   - Updates the round results record with shots fired, hits made, ships sunk, game state at the end of the round.
4. Round results are communicated to each player.
5. Next round starts (if the game hasn't ended)

## Ending the game

The game ends when one of the following events happens:

1. A player wins when they have sunk all their opponents ships (if both players happen to sink the last of their opponents ships on the same round then the game is a draw)
2. A player withdraws from the game (their opponent wins by default)
3. Some abnormal error occurs in the game system
