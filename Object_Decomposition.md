# Object Decomposition from Game Play

## Player

- Players must have a name
- Players can be human or computer. Default is human
- Players have a GameBoard
- Players can place their Ships on their GameBoard
- Players can select where to aim their available Shots

## Round

- Rounds have sequentially incrementing numbers, starting from 1

## Game

All game state lives in the Game object (and sub-objects)

- Games have several Rounds
- Games have two Players
- Games have a GameState
- Games can have a GameResult when the GameState is FINISHED or ABANDONED

## GameResult

- GameResult can be PLAYER_1_WINS | PLAYER_2_WINS | DRAWN | ABANDONED

## GameState

- GameStates can be SETUP | PLAYING | FINISHED | ABANDONED

## GameController

GameController is stateless and operates on Game objects

- GameController creates and controls (updates) all the game model objects and controls the state of these model objects
- GameController is a singleton
- GameController can validate the ShotsAimed by each Player before they are fired. Validation includes:
  - Checking the number of ShotsAimed is less or equal to the Players shots available.
  - Checking the Coordinates of the ShotsAimed do not have ShotsFired at them already
- GameController can fire the aimed shots from a Player to their opponents ships
- GameController can record the HitsMade by each player from their ShotsFired in a Round
- GameController can determine if any Ships are sunk
- GameController can update the Round number
- GameController can determine and update the Game state
- GameController can produce RoundResults for each Round broken down into each Player

## GameBoard

- GameBoards store the Coordinates where the Players Ships are placed
- GameBoards store ShotsFired and ShotsReceived
- Opposing Players GameBoards are kept in sync between ShotsFired and ShotsReceived across opposing players.
- GameBoards store the Round number of the Hits made on the opponents Ships. (But not the Coordinates)
- GameBoards can calculate the number of Shots a player can make in a Round

## Shots (Aimed, Fired, Received)

- Shots have a Coordinate and a Round number

## Ships

- Ships have a ShipType
- Ships are placed on the GameBoard which gives them Coordinates
- Ships store which of their Coordinates
- Ships are either afloat or sunk

## ShipType

- ShipTypes have a name, a length and a number of guns
- ShipTypes are immutable

## Coordinate

- Coordinates have a row and column. Rows are A-J (1-10), columns are 1-10.
  range flexibin out in the driveway
  Add stuff already earmarked for bin (carpet, old rubbish bin, hose)
