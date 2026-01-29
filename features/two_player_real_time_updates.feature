Feature: Two-Player Real-Time Updates
  As a player in a two-player Battleships game
  I want real-time updates without page refreshes
  So that I always see the current game state

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

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