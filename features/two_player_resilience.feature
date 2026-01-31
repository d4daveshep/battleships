Feature: Two-Player Game Resilience
  As a player in a two-player Battleships game
  I want the game to handle edge cases, state persistence, and network issues
  So that gameplay is robust and reliable

  # This feature consolidates:
  # - Edge cases (first round, multiple hits, etc.)
  # - Game state persistence (refreshing, reconnecting)
  # - Network handling (disconnections, errors)
  # - Real-time updates (long polling)

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Edge Cases ===

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

  # === Game State Persistence ===

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

  # === Network and Error Handling ===

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

  # === Real-Time Updates (Long Polling) ===

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
