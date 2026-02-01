# Object Oriented Programming Notes

## Objects (Nouns)

### Game

#### Constructor

- Requires a GameType enum, and 1 or 2 GamePlayers depending on type
- Creates a ShotsFiredBoard and a ShotsReceivedBoard
- Creates an empty list of Rounds
- Creates a GameState and sets it to CREATED

#### Actions, Questions (Verbs)

- mode -> GameMode
- state -> GameState
- player_1 -> GamePlayer (HumanPlayer)
- player_2 -> GamePlayer (HumanPlayer|ComputerPlayer)
- place_ships(GamePlayer, ValidShipLayout)
- current_round -> Round (raises StateException if not collecting shots or displaying round results)
- fire_shots(GamePlayer, Round, AimedShots) -> FiredShotResults
- result(GamePlayer)-> GamePlayerResult

### GameType Enum

#### Types

- SINGLE_PLAYER
- TWO_PLAYER

### GameState

#### States

1. CREATED
2. PLACING_SHIPS
3. COLLECTING_SHOTS_FOR_ROUND
4. DISPLAYING_ROUND_RESULTS (during game play will cycle back to 3.)
5. DISPLAYING_GAME_RESULT
6. ENDED
7. SURRENDERED

### GamePlayerResult

- WON
- LOST
- DRAWN
- SURRENDERED

### GamePlayer (HumanPlayer, ComputerPlayer)

- name
- type : PlayerType

### ValidShipLayout

### Board (ShotsFiredBoard, ShotsReceivedBoard)

### Ship

### Round

### FiredShotResults
