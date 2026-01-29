Feature: Two-Player Round Resolution
  As a player in a two-player Battleships game
  I want both players to fire shots simultaneously each round
  So that gameplay is fair and synchronized

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  Scenario: Both players fire shots simultaneously in the same round
    Given it is Round 1
    And I have selected 6 coordinates to aim at
    And I have clicked "Fire Shots"
    And I am waiting for my opponent
    When my opponent fires their shots
    Then both players' shots should be processed together
    And I should see the round results within 5 seconds
    And the round number should increment to Round 2

  Scenario: Waiting for opponent to fire their shots
    Given it is Round 1
    And I have fired my 6 shots
    When I am waiting for my opponent to fire
    Then I should see "Waiting for opponent to fire..." displayed
    And I should see a loading indicator
    And I should not be able to aim or fire additional shots
    And the page should update automatically when opponent fires

  Scenario: Opponent fires before me
    Given it is Round 1
    And my opponent has already fired their shots
    And I am still aiming my shots
    Then I should see "Opponent has fired - waiting for you" displayed
    And I should still be able to aim and fire my shots
    When I fire my shots
    Then the round should resolve immediately
    And I should see the round results within 2 seconds