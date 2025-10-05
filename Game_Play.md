# Game Play per Round

## Prerequisites for starting the game

- Each player has entered their name OR a single player has chosen to play against a computer opponent.
- Each player has placed their ships (according to the ship placement rules)

## Starting state for a Round

- Round numbers increment sequentially, starting from 1
- Player's game boards are in sync between the shots they have fired and the shots they have received, this means:
  - Each player knows the coordinates of each shot fired in each preceding round.
  - Each player knows which of the opponents ships they have hit in each preceding round but not the corresponding coordinates of each hit.
  - Each player knows the coordinates of the shots received from their opponent in preceding rounds, which round they were fired in and if they hit one of the players ships.
- Each player knows how many shots they have available to fire in the current round

## Steps in a Round

1. Each player aims their available shots for the round. This means they select the coordinates on their shots_fired board where they want to fire their available shots.
2. The coordinates of each player's aimed shots for the round are submitted (fired) to the game controller.
3. The game controller:
   - Validates the shots fired by each player.
     - The number of shots fired must be less or equal to the number of shots available to that player for the round.
     - The coordinates of the shots fired must be unique across the game (i.e. a player can't fire at a location they've already fired upon)
   - Enters the coordinates of each player's shots fired in the player's shots_fired board (storing the round number at the coordinates of each shot)
   - Enters the coordinates of each player's shots fired in their opponent's shots_received board (storing the round number at the coordinates of each shot received)
   - Enters the coordinates of any shots that hit a ship (storing the round number in the record for that ship)
   - Marks any ships as sunk if they have received a hit on each of their coordinates
   - Informs the player firing the shots how many (if any) shots were hits on their opponents ships
   - Updates the round results record with each player's shots fired, the hits made, ships sunk, and state of the game at the end of the round.
4. The player's displays are updated (if not done dynamically) and the round results are communicated to each player.
5. The next round starts (if the game hasn't ended)

## Ending the game

The game ends when one of the following events happens:

1. A player wins when they have sunk all their opponents ships (if both players sink the last of their opponents ships on the same round then the game is a draw)
2. A player withdraws from the game (their opponent wins by default)
3. Some abnormal error occurs in the game system
