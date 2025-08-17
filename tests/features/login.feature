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
    Then I should <result>

    Examples:
      | player_name | result |
      | "A" | see an error message "Player name must be at least 2 characters long" |
      | "AB" | be redirected to the game interface |
      | "ThisIsAVeryLongPlayerName" | an error message "Player name must be 20 characters or less" |
      | "Player123" | be redirected to the game interface |
      | "Player With Spaces" | be redirected to the game interface |

  # Scenario: Player name with special characters
  #   Given the player name field is empty
  #   And I select "Play against Computer" as the game mode
  #   When I enter "Player@#$" as my player name
  #   And I click the "Start Game" button
  #   Then I should see an error message "Player name can only contain letters, numbers, and spaces"
  #   And I should remain on the login page
  #
  # Scenario: Game mode selection persistence
  #   Given I enter "Diana" as my player name
  #   When I select "Play against Computer" as the game mode
  #   And I change my selection to "Play against Another Player"
  #   Then "Play against Another Player" should be selected
  #   And "Play against Computer" should not be selected
  #
  # Scenario: Form reset functionality
  #   Given I enter "Eve" as my player name
  #   And I select "Play against Computer" as the game mode
  #   When I click the "Reset" button
  #   Then the player name field should be empty
  #   And no game mode should be selected
  #   And all error messages should be cleared
  #
  # Scenario: Keyboard navigation and accessibility
  #   Given I am using keyboard navigation
  #   When I press Tab to navigate through the form
  #   Then I should be able to reach the player name field
  #   And I should be able to reach both game mode options
  #   And I should be able to reach the "Start Game" button
  #   And I should be able to reach the "Reset" button
  #   When I press Enter on the "Start Game" button
  #   Then it should behave the same as clicking the button
  #
  # Scenario: Page refresh preserves no data
  #   Given I enter "Frank" as my player name
  #   And I select "Play against Another Player" as the game mode
  #   When I refresh the page
  #   Then the player name field should be empty
  #   And no game mode should be selected
  #   And no error messages should be displayed
  #
  # Scenario: Multiple error correction workflow
  #   Given the player name field is empty
  #   And no game mode is selected
  #   When I click the "Start Game" button
  #   Then I should see validation errors
  #   When I enter "Grace" as my player name
  #   Then the player name error should be cleared
  #   But the game mode error should still be visible
  #   When I select "Play against Computer" as the game mode
  #   Then all error messages should be cleared
  #   And the "Start Game" button should be ready to submit
