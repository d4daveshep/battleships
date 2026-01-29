Feature: Two-Player Win Conditions
  As a player in a two-player Battleships game
  I want to win, lose, or draw the game
  So that the game has a clear conclusion

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Win/Loss/Draw Conditions ===

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