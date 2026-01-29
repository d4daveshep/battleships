Feature: Two-Player Board Visibility
  As a player in a two-player Battleships game
  I want to see the appropriate game boards
  So that I can make informed targeting decisions

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
