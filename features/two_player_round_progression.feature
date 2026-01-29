Feature: Two-Player Round Progression
  As a player in a two-player Battleships game
  I want rounds to progress correctly
  So that the game flows smoothly

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Round Progression ===

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