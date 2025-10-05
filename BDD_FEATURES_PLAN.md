# BDD Features Implementation Plan

## Overview
This document outlines the feature files needed to implement the Battleships game following strict BDD/TDD principles.

## Existing Features
✓ `login.feature` - Player authentication and game mode selection
✓ `multiplayer_lobby.feature` - Matchmaking and opponent selection
✓ `long_polling_updates.feature` - Real-time lobby updates

## Proposed New Features

### 1. **ship_placement.feature**
**As a player, I want to place my ships on the board, so I can prepare for battle**

**Scenarios:**
- Manual ship placement (horizontal orientation)
- Manual ship placement (vertical orientation)
- Manual ship placement (diagonal orientation)
- Invalid placement - ship outside board boundaries
- Invalid placement - ships overlapping
- Invalid placement - ships touching (no spacing)
- Invalid placement - ship touching board edge (valid)
- Random ship placement for player
- Computer opponent random ship placement
- Viewing placed ships on "My Ships and Shots Received" board
- All 5 ships must be placed before game starts
- Ship placement cancellation/reset

### 2. **game_initialization.feature**
**As a player, I want the game to be properly set up, so both players can begin playing**

**Scenarios:**
- Game starts after both players place ships
- Initial game state (Round 1, all ships afloat)
- Board display shows correct grids and labels (A-J, 1-10)
- Hits Made area initialized with ship names and slots
- Available shots calculated correctly (6 total initially)
- Computer opponent places ships automatically
- Multiplayer: waiting for opponent to place ships

### 3. **firing_shots.feature**
**As a player, I want to fire shots at my opponent, so I can sink their ships**

**Scenarios:**
- Aiming shots on the Shots Fired board
- Firing available number of shots (based on unsunk ships)
- Cannot fire at same location twice across the game
- Firing fewer shots than available (valid but suboptimal)
- Firing exactly the available number of shots
- Shot validation - must be unique coordinates
- Shot validation - must be within board bounds
- Submitting shots for the round
- Computer opponent fires shots automatically

### 4. **round_processing.feature**
**As a player, I want each round to be processed correctly, so hits are recorded accurately**

**Scenarios:**
- Round 1 complete processing (both players fire, results calculated)
- Shots recorded on both players' boards with round numbers
- Hit detection - shot hits opponent's ship
- Miss detection - shot hits empty square
- Multiple hits on different ships in one round
- Multiple hits on same ship in one round
- Round results displayed to both players
- Round number increments after processing
- Simultaneous round processing (both players fire)

### 5. **hit_tracking.feature**
**As a player, I want to track my hits, so I can identify where opponent's ships are located**

**Scenarios:**
- Recording hit on opponent's Carrier in Hits Made area
- Recording hit on opponent's Battleship in Hits Made area
- Recording hit on opponent's Cruiser in Hits Made area
- Recording hit on opponent's Submarine in Hits Made area
- Recording hit on opponent's Destroyer in Hits Made area
- Multiple hits on same ship show multiple round numbers
- Viewing which ships have been hit and in which rounds
- Correlating hits with shots fired to deduce ship locations
- Recording shots received on own ships

### 6. **ship_sinking.feature**
**As a player, I want ships to sink when fully hit, so the game progresses**

**Scenarios:**
- Destroyer sinks after 2 hits
- Submarine sinks after 3 hits
- Cruiser sinks after 3 hits
- Battleship sinks after 4 hits
- Carrier sinks after 5 hits
- Player notified when they sink opponent's ship
- Player notified when their own ship is sunk
- Sunk ship reduces available shots
- Multiple ships sunk in same round
- Available shots recalculated after ship sinks

### 7. **game_progression.feature**
**As a player, I want the game to progress smoothly through rounds, so I can play until completion**

**Scenarios:**
- Progressing from Round 1 to Round 2
- Round history maintained (all previous shots visible)
- Both players synchronized on round number
- Turn structure (both players act simultaneously in each round)
- Game state persisted between rounds
- Player can review previous rounds' results
- Shot count decreases as ships are sunk

### 8. **game_completion.feature**
**As a player, I want to know when the game ends, so I can see the outcome**

**Scenarios:**
- Player wins by sinking all opponent's ships first
- Game drawn when both sink last ships in same round
- Player wins when opponent surrenders/abandons
- Win notification displayed
- Draw notification displayed
- Game statistics shown (rounds played, shots fired, accuracy)
- Option to play again
- Return to lobby/login after game ends

### 9. **computer_opponent_strategy.feature**
**As a player facing a computer, I want the AI to play intelligently, so the game is challenging**

**Scenarios:**
- Computer places ships randomly following all rules
- Computer fires random shots when hunting
- Computer fires adjacent shots after scoring a hit
- Computer fires along ship axis after second hit
- Computer doesn't repeat shots
- Computer responds within reasonable time
- Computer follows all game rules

### 10. **game_board_ui.feature**
**As a player, I want a clear visual interface, so I can understand the game state**

**Scenarios:**
- "My Ships and Shots Received" board displays correctly
- "Shots Fired" board displays correctly
- Grid labels (A-J vertically, 1-10 horizontally) visible
- Round numbers shown in fired shot locations
- Round numbers shown in received shot locations
- Ship positions marked on own board
- Hits indicated differently from misses
- Sunk ships visually distinguished
- Hits Made area shows all 5 ships with tracking slots
- Current round number displayed
- Available shots count displayed
- Responsive layout for different screen sizes

---

## Implementation Order Recommendation

1. **ship_placement.feature** - Core setup
2. **game_initialization.feature** - Game start
3. **firing_shots.feature** - Basic gameplay mechanic
4. **round_processing.feature** - Core game loop
5. **hit_tracking.feature** - Feedback mechanism
6. **ship_sinking.feature** - Game progression
7. **game_progression.feature** - Multi-round flow
8. **game_completion.feature** - Win/loss conditions
9. **computer_opponent_strategy.feature** - AI behavior
10. **game_board_ui.feature** - Visual polish (can be developed in parallel)

---

## Notes

- Each feature focuses on user-facing behavior
- Implementation will follow RED-GREEN-REFACTOR TDD cycle
- Features build upon each other in the recommended order
- All scenarios align with Game_Rules.md and Game_Play.md specifications
