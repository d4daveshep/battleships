Feature: Two-Player Network Handling
  As a player in a two-player Battleships game
  I want network issues to be handled gracefully
  So that I can recover from connection problems

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

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