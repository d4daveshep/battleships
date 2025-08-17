Feature: Player Login and Game Mode Selection
  As a game player
  I want to enter my name and select a game mode
  So that I can start playing the game with my preferred opponent type

  Background:
    Given I am on the login page
    And the login page is fully loaded

  Scenario: Successful login with computer opponent selection
    Given the player name field is empty
    When I enter "Alice" as my player name
    And I click the "Play against Computer" button
    Then I should be redirected to the game interface
    And the game should be configured for single player mode
    And my player name should be set to "Alice"

  Scenario: Successful login with human opponent selection
    Given the player name field is empty
    When I enter "Bob" as my player name
    And I click the "Play against Another Player" button
    Then I should be redirected to the multiplayer lobby
    And the game should be configured for two player mode
    And my player name should be set to "Bob"

  Scenario: Login attempt with empty player name
    Given the player name field is empty
    And I click the "Play against Computer" button
    Then I should see an error message "Player name is required"
    And I should remain on the login page

  Scenario Outline: Player name validation
    Given the player name field is empty
    When I enter "<player_name>" as my player name
    And I click the "Play against Computer" button
    Then <result>

    Examples:
      | player_name | result |
      | A | I should see an error message "Player name must be between 2 and 20 characters" |
      | AB | I should be redirected to the game interface |
      | ThisIsAVeryLongPlayerName | I should see an error message "Player name must be between 2 and 20 characters" |
      | Player123 | I should be redirected to the game interface |
      | Player With Spaces | I should be redirected to the game interface |
      | Player@#$ | I should see an error message "Player name can only contain letter, numbers and spaces" |


  # Scenario: Page refresh preserves no data
  #   Given I enter "Frank" as my player name
  #   And I click the "Play against Computer" button
  #   When I refresh the page
  #   Then the player name field should be empty
  #   And no error messages should be displayed
