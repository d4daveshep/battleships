Feature: Two-Player Core Gameplay
  As a player in a two-player Battleships game
  I want to select shots, fire them, see results and progress through rounds
  So that I can play against my opponent


  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Start a round ===

  # Scenario: First round of the game
  #   Given the game just started
  #   And no shots have been fired yet
  #   And it is Round 1
  #   When I fire my 6 shots
  #   And my opponent fires their 6 shots
  #   Then the shots should be recorded
  #   And the round should resolve
  #   And Round 2 should begin

  # === Shot Selection ===

  Scenario: Game starts at Round 1 with 6 shots available
    Given the game just started
    Then I should see "Round 1" displayed
    And I should see "Shots Available: 6" displayed
    And I should be able to select up to 6 coordinates to fire at
    And I should see my board labeled "My Ships and Shots Received"
    And I should see the opponent's board labeled "Shots Fired"
    And I should see the "Hits Made" area showing all 5 opponent ships

  Scenario: Selecting multiple shot coordinates for aiming
    Given it is Round 1
    And I have 6 shots available
    When I select coordinate "A1" to aim at
    And I select coordinate "B3" to aim at
    And I select coordinate "E5" to aim at
    Then I should see 3 coordinates marked as aimed
    And I should see a list of the aimed coordinates 
    And I should see "Shots Aimed: 3/6" displayed
    And I should be able to select 3 more coordinates
    And the "Fire Shots" button should be enabled

  Scenario: Reselecting an aimed shot's coordinates un-aims the shot
    Given it is Round 1
    And I have only selected coordinate "A1" to aim at
    When I select coordinate "A1" again
    Then coordinate "A1" should be un-aimed
    And I should not see coordinate "A1" marked as aimed
    And the aimed coordinates list should not contain "A1"
    And I should still have 6 remaining shot selections available

  Scenario: Cannot select more shots than available
    Given it is Round 1
    And I have 6 shots available
    And I have selected 6 coordinates to aim at
    When I attempt to select another coordinate
    Then the coordinate should not be selectable
    And I should see a message "All available shots aimed"
    And I should see "Shots Aimed: 6/6" displayed

  Scenario: Can fire fewer shots than available
    Given it is Round 1
    And I have 6 shots available
    And I have selected 4 coordinates to aim at
    When I click the "Fire Shots" button
    Then my 4 shots should be submitted
    And I should see "Waiting for opponent to fire..." displayed
    And I should not be able to aim additional shots

  # === Round Resolution ===

  # Scenario: Both players fire shots simultaneously in the same round
  #   Given it is Round 1
  #   And I have selected 6 coordinates to aim at
  #   And I have clicked "Fire Shots"
  #   And I am waiting for my opponent
  #   When my opponent fires their shots
  #   Then both players' shots should be processed together
  #   And I should see the round results within 5 seconds
  #   And the round number should increment to Round 2
  #
  # Scenario: Waiting for opponent to fire their shots
  #   Given it is Round 1
  #   And I have fired my 6 shots
  #   When I am waiting for my opponent to fire
  #   Then I should see "Waiting for opponent to fire..." displayed
  #   And I should see a loading indicator
  #   And I should not be able to aim or fire additional shots
  #   And the page should update automatically when opponent fires
  #
  # Scenario: Opponent fires before me
  #   Given it is Round 1
  #   And my opponent has already fired their shots
  #   And I am still aiming my shots
  #   Then I should see "Opponent has fired - waiting for you" displayed
  #   And I should still be able to aim and fire my shots
  #   When I fire my shots
  #   Then the round should resolve immediately
  #   And I should see the round results within 2 seconds

  # === Round Progression ===

  # Scenario: Round number increments after both players fire
  #   Given it is Round 1
  #   And I have fired my shots
  #   And my opponent has fired their shots
  #   When the round resolves
  #   Then I should see "Round 2" displayed
  #   And I should be able to aim new shots for Round 2
  #
  # Scenario: Round doesn't advance while waiting
  #   Given it is Round 3
  #   And I have fired my shots
  #   But my opponent has not yet fired
  #   Then I should see "Round 3" displayed
  #   And I should see "Waiting for opponent to fire..." displayed
  #
  # Scenario: Round advances when both players have fired
  #   Given it is Round 3
  #   And I have already fired my shots
  #   When my opponent fires their shots
  #   Then I should see "Round 4" displayed 
