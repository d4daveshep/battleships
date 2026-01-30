Feature: Two-Player Game Outcomes
  As a player in a two-player Battleships game
  I want to sink ships, win, lose, draw, or surrender
  So that games have clear conclusions

  # This feature consolidates:
  # - Ship sinking mechanics
  # - Win conditions (all opponent ships sunk)
  # - Loss conditions (all my ships sunk)
  # - Draw conditions (mutual destruction in same round)
  # - Surrender option

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Sinking Ships ===

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
