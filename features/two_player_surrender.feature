Feature: Two-Player Surrender
  As a player in a two-player Battleships game
  I want to surrender the game if I cannot win
  So that I can end a hopeless game and return to the lobby

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Surrender Option ===

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