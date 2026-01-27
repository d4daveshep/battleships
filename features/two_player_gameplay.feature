Feature: Two-Player Simultaneous Multi-Shot Gameplay
  As a player in a two-player Battleships game
  I want to fire multiple shots simultaneously with my opponent each round
  So that I can try to sink all their ships and win the game

  # Business Rules:
  # - Both players fire shots SIMULTANEOUSLY in each round (no turns!)
  # - Each player fires multiple shots per round based on unsunk ships:
  #   * Carrier (length 5): 2 shots
  #   * Battleship (length 4): 1 shot
  #   * Cruiser (length 3): 1 shot
  #   * Submarine (length 3): 1 shot
  #   * Destroyer (length 2): 1 shot
  #   * Total at game start: 6 shots per round
  # - Rounds are numbered sequentially (1, 2, 3...)
  # - Players learn WHICH SHIP was hit and HOW MANY TIMES, but NOT exact coordinates
  # - When a ship is sunk, available shots decrease for next round
  # - Game ends when one player sinks all opponent ships (or both in same round = draw)
  # - Long polling keeps both players synchronized in real-time
  # - Coordinates are A1-J10 on a 10x10 grid

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Round Setup and Shot Availability ===

  Scenario: Game starts at Round 1 with 6 shots available
    Given the game just started
    Then I should see "Round 1" displayed
    And I should see "Shots Available: 6" displayed
    And I should be able to select up to 6 coordinates to fire at
    And I should see my board labeled "My Ships and Shots Received"
    And I should see the opponent's board labeled "Shots Fired"
    And I should see the "Hits Made" area showing all 5 opponent ships

  # Scenario: Selecting multiple shot coordinates for aiming
  #   Given it is Round 1
  #   And I have 6 shots available
  #   When I select coordinate "A1" to aim at
  #   And I select coordinate "B3" to aim at
  #   And I select coordinate "E5" to aim at
  #   Then I should see 3 coordinates marked as aimed
  #   And I should see "Shots Aimed: 3/6" displayed
  #   And I should be able to select 3 more coordinates
  #   And the "Fire Shots" button should be enabled
  #
  # Scenario: Cannot select the same coordinate twice in aiming phase
  #   Given it is Round 1
  #   And I have selected coordinate "A1" to aim at
  #   When I attempt to select coordinate "A1" again
  #   Then I should see an error message "Coordinate already selected for this round"
  #   And coordinate "A1" should remain selected once
  #   And I should still have 5 remaining shot selections available
  #
  # Scenario: Cannot select more shots than available
  #   Given it is Round 1
  #   And I have 6 shots available
  #   And I have selected 6 coordinates to aim at
  #   When I attempt to select a 7th coordinate
  #   Then the coordinate should not be selectable
  #   And I should see a message "All available shots aimed"
  #   And I should see "Shots Aimed: 6/6" displayed
  #
  # Scenario: Can fire fewer shots than available
  #   Given it is Round 1
  #   And I have 6 shots available
  #   And I have selected 4 coordinates to aim at
  #   When I click the "Fire Shots" button
  #   Then my 4 shots should be submitted
  #   And I should see "Waiting for opponent to fire..." displayed
  #   And I should not be able to aim additional shots
  #
  # # === Simultaneous Shot Submission ===
  #
  # Scenario: Both players fire shots simultaneously in the same round
  #   Given it is Round 1
  #   And I have selected 6 coordinates to aim at
  #   And I have clicked "Fire Shots"
  #   And I am waiting for my opponent
  #   When my opponent fires their shots
  #   Then both players' shots should be processed together
  #   And I should see the round results within 5 seconds
  #   And the round number should increment to Round 2
  #
  # Scenario: Waiting for opponent to fire their shots
  #   Given it is Round 1
  #   And I have fired my 6 shots
  #   When I am waiting for my opponent to fire
  #   Then I should see "Waiting for opponent to fire..." displayed
  #   And I should see a loading indicator
  #   And I should not be able to aim or fire additional shots
  #   And the page should update automatically when opponent fires
  #
  # Scenario: Opponent fires before me
  #   Given it is Round 1
  #   And my opponent has already fired their shots
  #   And I am still aiming my shots
  #   Then I should see "Opponent has fired - waiting for you" displayed
  #   And I should still be able to aim and fire my shots
  #   When I fire my shots
  #   Then the round should resolve immediately
  #   And I should see the round results within 2 seconds
  #
  # # === Hit Feedback (Ship-Based, Not Coordinate-Based) ===
  #
  # Scenario: Hitting opponent's ship shows which ship was hit, not coordinates
  #   Given it is Round 1
  #   And I have fired 6 shots
  #   And my opponent has fired their shots
  #   And 2 of my shots hit my opponent's Carrier
  #   And 1 of my shots hit my opponent's Destroyer
  #   When the round resolves
  #   Then I should see "Hits Made This Round:" displayed
  #   And I should see "Carrier: 2 hits" in the hits summary
  #   And I should see "Destroyer: 1 hit" in the hits summary
  #   And I should NOT see the exact coordinates of the hits
  #   And the Hits Made area should show round number "1" marked twice on Carrier
  #   And the Hits Made area should show round number "1" marked once on Destroyer
  #
  # Scenario: All shots miss in a round
  #   Given it is Round 1
  #   And I have fired 6 shots
  #   And my opponent has fired their shots
  #   And none of my shots hit any opponent ships
  #   When the round resolves
  #   Then I should see "Hits Made This Round: None" displayed
  #   And the Hits Made area should show no new shots marked
  #   And I should see all 6 of my shots marked as misses on the Shots Fired board
  #
  # Scenario: Hits Made area tracks cumulative hits across rounds
  #   Given it is Round 3
  #   And in Round 1 I hit the opponent's Battleship 1 time
  #   And in Round 2 I hit the opponent's Battleship 1 time
  #   And in Round 3 I hit the opponent's Battleship 2 times
  #   When the round resolves
  #   Then the Hits Made area for Battleship should show:
  #     | Round | Hits |
  #     | 1     | 1    |
  #     | 2     | 1    |
  #     | 3     | 2    |
  #   And I should see "Battleship: 4 hits total" displayed
  #
  # Scenario: Receiving hits shows which of my ships were hit
  #   Given it is Round 1
  #   And I have fired my shots
  #   And my opponent has fired their shots
  #   And my opponent hit my Cruiser 2 times
  #   And my opponent hit my Submarine 1 time
  #   When the round resolves
  #   Then I should see "Hits Received This Round:" displayed
  #   And I should see "Your Cruiser was hit 2 times" in the hits received summary
  #   And I should see "Your Submarine was hit 1 time" in the hits received summary
  #   And I should see the exact coordinates of the hits on my board
  #   And coordinates should be marked with round number "1"
  #
  # # === Shots Available Tracking ===
  #
  # Scenario: Shots available decreases when opponent ship is sunk
  #   Given it is Round 1
  #   And I have 6 shots available
  #   And my opponent has a Destroyer with 1 hit already
  #   And I fire shots that sink the opponent's Destroyer
  #   When Round 2 begins
  #   Then my opponent should see "Shots Available: 5" displayed
  #   And I should still see "Shots Available: 6" displayed
  #
  # Scenario: Shots available decreases when my ship is sunk
  #   Given it is Round 2
  #   And I have 6 shots available
  #   And my Battleship has 3 hits already
  #   And my opponent fires shots that sink my Battleship
  #   When Round 3 begins
  #   Then I should see "Shots Available: 5" displayed
  #   And the available shots should be 5
  #
  # Scenario: Multiple ships sunk reduces shots proportionally
  #   Given it is Round 5
  #   And my Destroyer is sunk
  #   And my Submarine is sunk
  #   And my Cruiser is sunk
  #   When Round 6 begins
  #   Then I should see "Shots Available: 3" displayed
  #   And the available shots should be 3
  #
  # Scenario: All ships sunk means zero shots available
  #   Given it is Round 8
  #   And all my ships are sunk
  #   Then I should see "Shots Available: 0" displayed
  #   And I should see "You Lose!" displayed
  #   And the game should be marked as finished
  #
  # # === Sinking Ships ===
  #
  # Scenario: Sinking an opponent's ship
  #   Given it is Round 3
  #   And my opponent has a Destroyer at "A1" and "A2"
  #   And I have hit "A1" in a previous round
  #   And I fire shots including "A2"
  #   And my opponent fires their shots
  #   When the round resolves
  #   Then I should see "You sunk their Destroyer!" displayed
  #   And the Destroyer should be marked as sunk in the Hits Made area
  #   And I should see "Ships Sunk: 1/5" displayed
  #   And my opponent should see "Your Destroyer was sunk!" displayed
  #   And my opponent should see "Ships Lost: 1/5" displayed
  #
  # Scenario: Having my ship sunk by opponent
  #   Given it is Round 4
  #   And I have a Cruiser at "C1", "C2", and "C3"
  #   And my opponent has hit "C1" and "C2" in previous rounds
  #   And my opponent fires shots including "C3"
  #   When the round resolves
  #   Then I should see "Your Cruiser was sunk!" displayed
  #   And coordinates "C1", "C2", and "C3" should be marked as sunk on my board
  #   And I should see "Ships Lost: 1/5" displayed
  #   And I should receive this update within 5 seconds
  #
  # Scenario: Multiple ships sunk in the same round
  #   Given it is Round 6
  #   And my opponent's Destroyer needs 1 more hit to sink
  #   And my opponent's Submarine needs 1 more hit to sink
  #   And I fire shots that hit both ships' final positions
  #   When the round resolves
  #   Then I should see "You sunk their Destroyer!" displayed
  #   And I should see "You sunk their Submarine!" displayed
  #   And I should see "Ships Sunk: 2/5" displayed (or higher if others already sunk)
  #
  # Scenario: Both players sink ships in the same round
  #   Given it is Round 5
  #   And my opponent's Battleship needs 1 more hit
  #   And my Carrier needs 1 more hit
  #   And I fire shots that sink the opponent's Battleship
  #   And my opponent fires shots that sink my Carrier
  #   When the round resolves
  #   Then I should see "You sunk their Battleship!" displayed
  #   And I should see "Your Carrier was sunk!" displayed
  #   And both ships should be marked as sunk
  #   And the game should continue to the next round
  #
  # # === Round-Based Shot Recording ===
  #
  # Scenario: Shots fired are marked with round numbers on Shots Fired board
  #   Given it is Round 1
  #   And I fire shots at "A1", "B2", "C3", "D4", "E5", "F6"
  #   When round 1 ends
  #   Then coordinates "A1", "B2", "C3", "D4", "E5", "F6" should be marked with "1" on my Shots Fired board
  #
  # Scenario: Shots fired in different rounds are shown on the Shots Fired board
  #   Given Round 1 has ended
  #   And my Round 1 shots were "A1", "B2", "C3", "D4", "E5", "F6"
  #   And my Round 1 shots are marked on my Shots Fired board with "1"
  #   When Round 2 starts
  #   And I fire shots at "A2", "B3", "C4", "D5", "E6", "F7"
  #   Then those coordinates should be marked with "2" on my Shots Fired board
  #   And I should be able to see both Round 1 and Round 2 shots on the board
  #
  # Scenario: Shots received are marked with round numbers on My Ships board
  #   Given it is Round 1
  #   And my opponent fires at "G1", "G2", "G3", "H1", "H2", "H3"
  #   When the round resolves
  #   Then coordinates "G1", "G2", "G3", "H1", "H2", "H3" should be marked with "1" on my Ships board
  #   And hits on my ships should be clearly marked
  #   And misses should be clearly marked differently
  #
  # # === Win/Loss/Draw Conditions ===
  #
  # Scenario: Winning the game by sinking all opponent ships
  #   Given it is Round 7
  #   And my opponent has only their Destroyer remaining
  #   And the Destroyer has 1 hit already
  #   And I fire shots that sink the Destroyer
  #   When the round ends
  #   Then I should see "All opponent ships destroyed!" displayed
  #   And the game should be marked as finished
  #   And I should see "You Win!" displayed
  #   And I should see an option to "Return to Lobby"
  #
  # Scenario: Losing the game when all my ships are sunk
  #   Given it is Round 8
  #   And I have only my Submarine remaining
  #   And my Submarine has 2 hits already
  #   And my opponent fires shots that sink my Submarine
  #   When the round resolves
  #   Then I should see "Your Submarine was sunk!" displayed
  #   And I should see "You Lose!" displayed
  #   And I should see "All your ships destroyed!" displayed
  #   And the game should be marked as finished
  #   And I should see an option to "Return to Lobby"
  #   And I should receive this update within 5 seconds
  #
  # Scenario: Draw when both players sink all ships in the same round
  #   Given it is Round 10
  #   And I have only my Destroyer remaining with 1 hit
  #   And my opponent has only their Destroyer remaining with 1 hit
  #   And I fire shots that sink the opponent's Destroyer
  #   And my opponent fires shots that sink my Destroyer
  #   When the round resolves
  #   Then I should see "Draw!" displayed
  #   And I should see "Both players sunk all ships in the same round" displayed
  #   And the game should be marked as finished
  #   And I should see an option to "Return to Lobby"
  #
  # # === Shot Validation ===
  #
  # Scenario: Cannot fire at coordinates already fired at in previous rounds
  #   Given it is Round 3
  #   And I fired at "E5" in Round 1
  #   When I attempt to select coordinate "E5" to aim at
  #   Then I should see an error message "You have already fired at this coordinate"
  #   And the coordinate should not be selectable
  #   And it should show as already fired with round number "1"
  #
  # Scenario: Cannot fire at invalid coordinates
  #   Given it is Round 1
  #   When I attempt to fire at coordinate "K11"
  #   Then I should see an error message "Invalid coordinate"
  #   And the shot should not be recorded
  #
  # Scenario: Must fire at unique coordinates within the same round
  #   Given it is Round 1
  #   And I have selected coordinates "A1", "B2", "C3"
  #   When I attempt to select "A1" again in the same round
  #   Then I should see an error message "Coordinate already selected for this round"
  #   And I should still have 3 shots aimed, not 4
  #
  # # === Board Visibility ===
  #
  # Scenario: Player can see their own ships and received shots
  #   Given the game is in progress at Round 4
  #   And I have ships placed on my board
  #   And my opponent has fired shots at my board in previous rounds
  #   Then I should see all my ship positions on "My Ships and Shots Received" board
  #   And I should see all shots my opponent has fired at my board
  #   And I should see round numbers for each shot received
  #   And I should see which of my ships have been hit
  #   And I should see which of my ships have been sunk
  #
  # Scenario: Player sees shots fired but not opponent's ship positions
  #   Given the game is in progress at Round 4
  #   And my opponent has ships placed on their board
  #   And I have fired shots in previous rounds
  #   Then I should not see any of my opponent's ship positions
  #   And I should see all shots I have fired on the "Shots Fired" board
  #   And I should see round numbers for each shot fired
  #   And I should see the "Hits Made" area showing which ships I've hit with the round numbers
  #
  # Scenario: Hits Made area shows ship-level hit tracking
  #   Given the game is in progress at Round 5
  #   Then I should see the "Hits Made" area next to the Shots Fired board
  #   And I should see 5 ship rows labeled: Carrier, Battleship, Cruiser, Submarine, Destroyer
  #   And each ship row should show spaces for tracking hits
  #   And I should see round numbers marked in the spaces where I've hit each ship
  #   And sunk ships should be clearly marked as "SUNK"
  #
  # Scenario: Both boards are visible simultaneously
  #   Given the game is in progress
  #   Then I should see "My Ships and Shots Received" board
  #   And I should see "Shots Fired" board
  #   And I should see "Hits Made" area
  #   And both boards should show a 10x10 grid with coordinates A-J and 1-10
  #   And all three areas should be clearly distinguishable
  #
  # # === Round Progression ===
  #
  # Scenario: Round number increments after both players fire
  #   Given it is Round 1
  #   And I have fired my shots
  #   And my opponent has fired their shots
  #   When the round resolves
  #   Then I should see "Round 2" displayed
  #   And I should be able to aim new shots for Round 2
  #
  # Scenario: Round number stays same while waiting for opponent
  #   Given it is Round 3
  #   And I have fired my shots
  #   And my opponent has not yet fired
  #   Then I should still see "Round 3" displayed
  #   And I should see "Waiting for opponent to fire..." displayed
  #   When my opponent fires their shots
  #   Then I should see "Round 4" displayed
  #
  # # === Real-Time Updates (Long Polling) ===
  #
  # Scenario: Real-time update when opponent fires
  #   Given it is Round 2
  #   And I have already fired my shots
  #   And I am waiting for my opponent to fire
  #   When my opponent fires their shots
  #   Then I should see the round results within 5 seconds
  #   And I should not have to manually refresh the page
  #   And I should see Round 3 begin automatically
  #
  # Scenario: Real-time update when both players fire simultaneously
  #   Given it is Round 1
  #   And I fire my shots at the same moment my opponent fires
  #   When both shots are submitted
  #   Then both players should see the round results within 5 seconds
  #   And the round should resolve correctly with all hits processed
  #
  # Scenario: Long polling connection resilience
  #   Given it is Round 3
  #   And I am waiting for my opponent to fire
  #   And the long polling connection times out after 30 seconds
  #   When the connection is re-established
  #   And my opponent fires their shots
  #   Then I should see the round results within 5 seconds
  #   And the game should continue normally
  #
  # # === Game State Persistence ===
  #
  # Scenario: Refreshing page maintains game state
  #   Given the game is in progress at Round 5
  #   And I have fired shots in Rounds 1-4
  #   And my opponent has fired shots in Rounds 1-4
  #   When I refresh the page
  #   Then I should see "Round 5" displayed
  #   And I should see all my previous shots on the Shots Fired board
  #   And I should see all opponent's previous shots on my Ships board
  #   And I should see the correct Hits Made tracking
  #   And I should see the correct shots available count
  #
  # Scenario: Reconnecting to an in-progress game
  #   Given I am in an active game at Round 6
  #   And I lose connection temporarily
  #   When I reconnect and navigate to the game page
  #   Then I should see the current game state at Round 6
  #   And all previous rounds' shots should be displayed correctly
  #   And the Hits Made area should show all previous hits
  #   And I should be able to continue playing
  #
  # # === Edge Cases ===
  #
  # Scenario: First round of the game
  #   Given the game just started
  #   And no shots have been fired yet
  #   And it is Round 1
  #   When I fire my 6 shots
  #   And my opponent fires their 6 shots
  #   Then the shots should be recorded
  #   And the round should resolve
  #   And Round 2 should begin
  #
  # Scenario: Multiple hits on same ship in one round
  #   Given it is Round 2
  #   And my opponent has a Carrier at "A1", "A2", "A3", "A4", "A5"
  #   And the Carrier has 1 hit from Round 1
  #   And I fire shots that hit "A2", "A3", "A4"
  #   When the round resolves
  #   Then I should see "Carrier: 3 hits" in the round results
  #   And the Hits Made area should show round number "2" marked three times on Carrier
  #   And the Carrier should have 4 total hits
  #
  # Scenario: Hitting multiple different ships in one round
  #   Given it is Round 3
  #   And I fire 6 shots
  #   And my shots hit Carrier (2 times), Battleship (1 time), and Destroyer (1 time)
  #   When the round resolves
  #   Then I should see "Carrier: 2 hits" in the round results
  #   And I should see "Battleship: 1 hit" in the round results
  #   And I should see "Destroyer: 1 hit" in the round results
  #   And the Hits Made area should be updated for all three ships
  #
  # Scenario: Firing fewer shots than available
  #   Given it is Round 4
  #   And I have 5 shots available
  #   When I select only 3 coordinates to aim at
  #   And I click "Fire Shots"
  #   Then my 3 shots should be submitted
  #   And I should not be prevented from firing fewer shots than available
  #   And the round should resolve normally when opponent fires
  #
  # # === Network and Error Handling ===
  #
  # Scenario: Handling network error during shot submission
  #   Given it is Round 2
  #   And I have selected 6 coordinates to aim at
  #   When I click "Fire Shots"
  #   And the network connection fails before submission completes
  #   Then I should see an error message "Connection lost - please try again"
  #   And the shots should not be recorded
  #   And I should still be in the aiming phase
  #   When the connection is restored
  #   Then I should be able to fire again with the same coordinates
  #
  # Scenario: Opponent disconnects during game
  #   Given the game is in progress at Round 5
  #   And I have fired my shots
  #   And I am waiting for my opponent
  #   When my opponent disconnects from the game
  #   Then I should see a message "Opponent has disconnected"
  #   And I should see an option to "Wait for Opponent" or "Abandon Game"
  #   And the game should be paused
  #
  # Scenario: Opponent reconnects after disconnection
  #   Given the game is in progress at Round 5
  #   And my opponent disconnected
  #   And I chose to "Wait for Opponent"
  #   When my opponent reconnects
  #   Then I should see a message "Opponent has reconnected"
  #   And the game should resume
  #   And my opponent should be able to fire their shots for Round 5
  #
  # # === Surrender Option ===
  #
  # Scenario: Player surrenders the game
  #   Given the game is in progress at Round 4
  #   When I click the "Surrender" button
  #   And I confirm the surrender
  #   Then I should see "You surrendered" displayed
  #   And I should see "You Lose!" displayed
  #   And my opponent should see "Opponent surrendered" displayed
  #   And my opponent should see "You Win!" displayed
  #   And the game should be marked as finished
  #   And I should see an option to return to the lobby
