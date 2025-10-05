# Game Rules

## Overview

The aim of the game is to sink all of your opponent's ships before they sink all of your ships.

## Players

The game is played by two players. Either two humans using their own computer or by one human playing against a computer.
Players take turns at starting the game if multiple games are being played. But there is no real advantage to starting first or second.

## Game board

The game board consists of two 10 by 10 grids representing a portion of ocean.
Each grid is labeled with ascending letters (A-J) along the vertical axis and with ascending numbers (1-10) along the horizontal axis.
The two grids can be arranged vertically or horizontally.
The bottom (or left hand) board is called the "My Ships and Shots Received" board and is where the player places their 5 ships and records the shots received from their opponent.
The top (or right hand) board is called the "Shots Fired" board and is where the player fires their shots at their opponent's ships and notes the possible positions of their opponent's ships
Next to the Shots Fired board is the Hits Made area lines of squares representing the length of each ship. The ship's names are labeled next to each line.

## Ships

Each player starts the game with 5 ships, each ship has a length and the number of shots it can fire as shown below:

1. Carrier: length 5, 2 shots
2. Battleship: length 4, 1 shot
3. Cruiser: length 3, 1 shot
4. Submarine: length 3, 1 shot
5. Destroyer: length 2, 1 shot

## Ship placement

A player's ships can be placed anywhere on the My Ships and Shots Received board according to the following rules:

1. Ships can be horizontal, vertical or diagonal
2. Ships can be touching the edge of the board grid but can not go outside the board grid or wrap around the board grid
3. Ships cannot overlap another ship or be touching another ship
4. There must be an empty space all around a ship (except where it touches the edge of the board)

When playing against a computer opponent, the computer will randomly place its ships on its bottom board.
A player can ask the game controller to randomly place their ships for them

## Game play

Players place their 5 ships on their My Ships and Shots Received board.
The game consists of a number of rounds until a player wins or the game is drawn
Rounds are numbered in ascending order starting at round 1.

- Also see [Game Play]("Game_Play.md")

### Each round

Both players decide where to fire their available shots and enter them on their Shots Fired grid with the round number E.g. for round 1 they enter the number 1 in each grid square for each fired shot.
Each player tells their opponent where they have fired their available shots using the alphanumeric grid reference for the shot E.g. A-4, C-5, D-8, F-1 etc. The player receiving the shots records the round number in their Ships and Shots Received grid.
Each player then tells their opponent which, if any, ships they have hit with their shots and if any of their ships have been sunk with this round of shots. The grid location of the hit is not revealed only that a hit was made on a particular ship in that round.
When a player firing shots hits their opponent's ships they record the round number in the appropriate ship in the Hits Made area.
The order of which player tell the other first does not matter in the round. What matters is that within the round, both players make their shots, tell their opponent their shots, learn which ships they hit with their shots, record the shots fired at them by their opponent and tell their opponent which of their own ships were hit with the opponent's shots

## Number of shot available

The number of shots available to a player in each round is the total number of shots for each unsunk ship.
E.g. at the start of the game no ships are sunk so each player has 5 shots available. If a player has its Battleship and Submarine sunk then they only have 3 shots available.
When a player has had all their ships sunk they have no shots available so have lost the game.

## Firing shots

In each round, each player will fire the number of shots they have available to them (they may fire less shots than they have available but there is normally no advantage in doing this)
All shots fired in a round by a player have the same round number label.

## Recording hits on ships

Each player needs to keep track of the hits they have made on their opponents ships, these are made in the Hits Made area.
This helps determine where the player should fire their next shots.
E.g. if they have hit their opponent's Battleship on round 1 and round 3, then they would be looking at their shots fired grid to find where they fired shots on rounds 1 and 3 to see where the opponent's Battleship could be placed, knowing it is 4 squares long.
It is possible to make multiple hits on the same ship in a round, in this case, each hit is recorded separately on the Hits Made area. E.g. if in round 3 two hits are made on the opponent's Carrier then the number 3 will be recorded twice on the Carrier line in the Hits Made area.

## Sinking ships

A ship is considered sunk when it has received the same number of hits as the length (in squares) of the ship. E.g. When a Battleship receives 4 hits, one on each of its grid positions, it is considered sunk.
A player must announce to their opponent when one of their ships has been sunk. The opponent may be able to determine the exact location ship from the sequence of shots fired in different rounds. Sinking a ship also reduces the owning player's available shots for the remainder of the game.

## Wining the game

The winner of the game is the player who sinks all their opponent's ships first.
A player can also win the game if their opponent surrenders by abandoning the game.

## Drawing the game

If both players sink the last of their opponent's ships in the same round then the game is considered a draw.
