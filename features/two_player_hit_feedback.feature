Feature: Two-Player Hit Feedback
  As a player in a two-player Battleships game
  I want to receive feedback about which of my shots hit opponent ships
  So that I can track my progress and target remaining ships

  # Business Rules:
  # - Players learn WHICH SHIP was hit and HOW MANY TIMES, but NOT exact coordinates
  # - Hits Made area tracks cumulative hits across rounds
  # - Hits Received shows which of my ships were hit

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Hit Feedback (Ship-Based, Not Coordinate-Based) ===

  # Scenario: Hitting opponent's ship shows which ship was hit, not coordinates
  #   Given it is Round 1
  #   And I have fired 6 shots
  #   And my opponent has fired their shots
  #   And 2 of my shots hit my opponent's Carrier
  #   And 1 of my shots hit my opponent's Destroyer
  #   When the round resolves
  #   Then I should see "Hits Made This Round:" displayed
  #   And I should see "Carrier: 2 hits" in the hits summary
  #   And I should see "Destroyer: 1 hit" in the hits summary
  #   And I should NOT see the exact coordinates of the hits
  #   And the Hits Made area should show round number "1" marked twice on Carrier
  #   And the Hits Made area should show round number "1" marked once on Destroyer
  #
  # Scenario: All shots miss in a round
  #   Given it is Round 1
  #   And I have fired 6 shots
  #   And my opponent has fired their shots
  #   And none of my shots hit any opponent ships
  #   When the round resolves
  #   Then I should see "Hits Made This Round: None" displayed
  #   And the Hits Made area should show no new shots marked
  #   And I should see all 6 of my shots marked as misses on the Shots Fired board
  #
  # Scenario: Hits Made area tracks cumulative hits across rounds
  #   Given it is Round 3
  #   And in Round 1 I hit the opponent's Battleship 1 time
  #   And in Round 2 I hit the opponent's Battleship 1 time
  #   And in Round 3 I hit the opponent's Battleship 2 times
  #   When the round resolves
  #   Then the Hits Made area for Battleship should show:
  #     | Round | Hits |
  #     | 1     | 1    |
  #     | 2     | 1    |
  #     | 3     | 2    |
  #   And I should see "Battleship: 4 hits total" displayed
  #
  # Scenario: Receiving hits shows which of my ships were hit
  #   Given it is Round 1
  #   And I have fired my shots
  #   And my opponent has fired their shots
  #   And my opponent hit my Cruiser 2 times
  #   And my opponent hit my Submarine 1 time
  #   When the round resolves
  #   Then I should see "Hits Received This Round:" displayed
  #   And I should see "Your Cruiser was hit 2 times" in the hits received summary
  #   And I should see "Your Submarine was hit 1 time" in the hits received summary
  #   And I should see the exact coordinates of the hits on my board
  #   And coordinates should be marked with round number "1"
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