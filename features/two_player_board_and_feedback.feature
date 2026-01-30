Feature: Two-Player Board Visibility and Hit Feedback
  As a player in a two-player Battleships game
  I want to see the appropriate game boards and receive hit feedback
  So that I can make informed targeting decisions

  # This feature consolidates:
  # - Board visibility (what players can/cannot see)
  # - Hit feedback (ship-based tracking, not coordinate-based)

  # Business Rules:
  # - Players learn WHICH SHIP was hit and HOW MANY TIMES, but NOT exact coordinates
  # - Hits Made area tracks cumulative hits across rounds
  # - Hits Received shows which of my ships were hit with exact coordinates

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Board Visibility ===

  Scenario: Player can see their own ships and received shots
    Given the game is in progress at Round 4
    And I have ships placed on my board
    And my opponent has fired shots at my board in previous rounds
    Then I should see all my ship positions on "My Ships and Shots Received" board
    And I should see all shots my opponent has fired at my board
    And I should see round numbers for each shot received
    And I should see which of my ships have been hit
    And I should see which of my ships have been sunk

  Scenario: Player sees shots fired but not opponent's ship positions
    Given the game is in progress at Round 4
    And my opponent has ships placed on their board
    And I have fired shots in previous rounds
    Then I should not see any of my opponent's ship positions
    And I should see all shots I have fired on the "Shots Fired" board
    And I should see round numbers for each shot fired
    And I should see the "Hits Made" area showing which ships I've hit with the round numbers

  Scenario: Hits Made area shows ship-level hit tracking
    Given the game is in progress at Round 5
    Then I should see the "Hits Made" area next to the Shots Fired board
    And I should see 5 ship rows labeled: Carrier, Battleship, Cruiser, Submarine, Destroyer
    And each ship row should show spaces for tracking hits
    And I should see round numbers marked in the spaces where I've hit each ship
    And sunk ships should be clearly marked as "SUNK"

  Scenario: Both boards are visible simultaneously
    Given the game is in progress
    Then I should see "My Ships and Shots Received" board
    And I should see "Shots Fired" board
    And I should see "Hits Made" area
    And both boards should show a 10x10 grid with coordinates A-J and 1-10
    And all three areas should be clearly distinguishable

  # === Hit Feedback ===

  Scenario: All shots miss in a round
    Given it is Round 1
    And I have fired 6 shots
    And my opponent has fired their shots
    And none of my shots hit any opponent ships
    When the round resolves
    Then I should see "Hits Made This Round: None" displayed
    And the Hits Made area should show no new shots marked
    And I should see all 6 of my shots marked as misses on the Shots Fired board

  Scenario: Hitting opponent's ship shows which ship was hit, not coordinates
    Given it is Round 1
    And I have fired 6 shots
    And my opponent has fired their shots
    And 2 of my shots hit my opponent's Carrier
    And 1 of my shots hit my opponent's Destroyer
    When the round resolves
    Then I should see "Hits Made This Round:" displayed
    And I should see "Carrier: 2 hits" in the hits summary
    And I should see "Destroyer: 1 hit" in the hits summary
    And I should NOT see the exact coordinates of the hits
    And the Hits Made area should show round number "1" marked twice on Carrier
    And the Hits Made area should show round number "1" marked once on Destroyer

  Scenario: Hits Made area tracks cumulative hits across rounds
    Given it is Round 3
    And in Round 1 I hit the opponent's Battleship 1 time
    And in Round 2 I hit the opponent's Battleship 1 time
    And in Round 3 I hit the opponent's Battleship 2 times
    When the round resolves
    Then the Hits Made area for Battleship should show:
      | Round | Hits |
      | 1     | 1    |
      | 2     | 1    |
      | 3     | 2    |
    And I should see "Battleship: 4 hits total" displayed

  Scenario: Receiving hits shows which of my ships were hit
    Given it is Round 1
    And I have fired my shots
    And my opponent has fired their shots
    And my opponent hit my Cruiser 2 times
    And my opponent hit my Submarine 1 time
    When the round resolves
    Then I should see "Hits Received This Round:" displayed
    And I should see "Your Cruiser was hit 2 times" in the hits received summary
    And I should see "Your Submarine was hit 1 time" in the hits received summary
    And I should see the exact coordinates of the hits on my board
    And coordinates should be marked with round number "1"

  Scenario: Multiple hits on same ship in one round
    Given it is Round 2
    And my opponent has a Carrier at "A1", "A2", "A3", "A4", "A5"
    And the Carrier has 1 hit from Round 1
    And I fire shots that hit "A2", "A3", "A4"
    When the round resolves
    Then I should see "Carrier: 3 hits" in the round results
    And the Hits Made area should show round number "2" marked three times on Carrier
    And the Carrier should have 4 total hits

  Scenario: Hitting multiple different ships in one round
    Given it is Round 3
    And I fire 6 shots
    And my shots hit Carrier (2 times), Battleship (1 time), and Destroyer (1 time)
    When the round resolves
    Then I should see "Carrier: 2 hits" in the round results
    And I should see "Battleship: 1 hit" in the round results
    And I should see "Destroyer: 1 hit" in the round results
    And the Hits Made area should be updated for all three ships
