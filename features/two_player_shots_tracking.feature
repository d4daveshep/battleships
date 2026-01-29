Feature: Two-Player Shots Tracking
  As a player in a two-player Battleships game
  I want to see how many shots I can fire each round
  So that I can plan my targeting strategy

  # Business Rules:
  # - Each player fires multiple shots per round based on unsunk ships:
  #   * Carrier (length 5): 2 shots
  #   * Battleship (length 4): 1 shot
  #   * Cruiser (length 3): 1 shot
  #   * Submarine (length 3): 1 shot
  #   * Destroyer (length 2): 1 shot
  #   * Total at game start: 6 shots per round
  # - When a ship is sunk, available shots decrease for next round

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Shots Available Tracking ===

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
  # Scenario: Firing fewer shots than available
  #   Given it is Round 4
  #   And I have 5 shots available
  #   When I select only 3 coordinates to aim at
  #   And I click "Fire Shots"
  #   Then my 3 shots should be submitted
  #   And I should not be prevented from firing fewer shots than available
  #   And the round should resolve normally when opponent fires