Feature: Two-Player Edge Cases
  As a player in a two-player Battleships game
  I want edge cases to be handled gracefully
  So that the game remains stable in unusual situations

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Edge Cases ===

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