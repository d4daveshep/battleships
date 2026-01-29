Feature: Two-Player Game State Persistence
  As a player in a two-player Battleships game
  I want my game state to be preserved
  So that I can continue playing after refreshing or reconnecting

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

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