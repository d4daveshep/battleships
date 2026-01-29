Feature: Two-Player Shot Selection
  As a player in a two-player Battleships game
  I want to select and aim multiple shot coordinates per round
  So that I can target enemy ships strategically

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

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
    And I should see "Shots Aimed: 3/6" displayed
    And I should be able to select 3 more coordinates
    And the "Fire Shots" button should be enabled

  Scenario: Reselecting an aimed shot's coordinates un-aims the shot
    Given it is Round 1
    And I have only selected coordinate "A1" to aim at
    When I select coordinate "A1" again
    Then coordinate "A1" should be un-aimed
    And I should not see coordinate "A1" marked as aimed
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