Feature: Multiplayer Game Lobby
  As a player who wants to play against another human
  I want to join a lobby and select or wait for an opponent
  So that I can start a multiplayer game

  # Business Rules:
  # - Players enter lobby after selecting "Play against Another Player" 
  # - Players can select available opponents from the lobby
  # - If lobby is empty, players must wait for others to join
  # - Only players not currently in a game should be selectable

  Background:
    Given the multiplayer lobby system is available
    # And I have successfully logged in with multiplayer mode selected

  Scenario: Joining lobby with existing available players
    Given there are other players in the lobby:
      | Player Name | Status    |
      | Alice       | Available |
      | Bob         | Available |
      | Charlie     | Available |
    When I login as "Diana" and select human opponent
    Then I should see the lobby interface
    And I should see my name
    And I should see my own status as "Available"
    And I should see a list of available players:
      | Player Name |
      | Alice   |
      | Bob     |
      | Charlie |
    And I should see a "Select Opponent" button for each available player

  Scenario: Successfully selecting an opponent from the lobby
    Given I've logged in as "Diana" and selected human opponent
    And there are other players in the lobby:
      | Player Name | Status    |
      | Alice       | Available |
      | Bob         | Available |
      | Charlie     | Available |
    When I click "Select Opponent" next to "Alice"
    Then I should see a confirmation message "Game request sent to Alice"
    And Alice should receive a game invitation from "Diana"
    And my status should change to "Requesting Game"
    And I should not be able to select other players while waiting for my request to be completed

  Scenario: Joining an empty lobby
    Given there are no other players in the lobby
    When I login as "Eve" and select human opponent
    Then I should see the lobby interface
    And I should see a message "No other players available"
    And I should see a message "Waiting for other players to join..."
    And I should not see any selectable players
    And my status should be "Available"

  Scenario: Another player joins while I'm waiting in empty lobby
    Given I've logged in as "Frank" and selected human opponent
    And there are no other players in the lobby
    And I see the message "Waiting for other players to join..."
    When another player "Grace" logs in and selects human opponent
    Then I should see "Grace" in the available players list
    And I should see a "Select Opponent" button next to "Grace"
    And the "Waiting for other players" message should be hidden
    And I should be able to select "Grace" as my opponent

  # Scenario: Multiple players joining the lobby simultaneously
  #   Given I am in the lobby as "Henry"
  #   And there is one other player "Iris" in the lobby
  #   When two more players "Jack" and "Kelly" join the lobby
  #   Then I should see all available players:
  #     | Iris  |
  #     | Jack  |
  #     | Kelly |
  #   And each player should have a "Select Opponent" button
  #   And all players should show "Available" status
  #
  # Scenario: Player leaves the lobby while I'm viewing it
  #   Given I am in the lobby as "Liam"
  #   And there are other players in the lobby:
  #     | Player Name | Status    |
  #     | Maya        | Available |
  #     | Noah        | Available |
  #   When "Maya" leaves the lobby
  #   Then "Maya" should no longer appear in my available players list
  #   And I should still see "Noah" as available
  #   And the player count should update accordingly
  #
  # Scenario: Cannot select players who are already in a game
  #   Given I am in the lobby as "Olivia"
  #   And there are other players in the lobby:
  #     | Player Name | Status    |
  #     | Paul        | Available |
  #     | Quinn       | In Game   |
  #     | Rachel      | Requesting Game |
  #   Then I should only see selectable players:
  #     | Paul |
  #   And "Quinn" should be displayed but marked as "In Game"
  #   And "Rachel" should be displayed but marked as "Requesting Game"
  #   And I should not see "Select Opponent" buttons for "Quinn" or "Rachel"
  #
  # Scenario: Refreshing the lobby updates player list
  #   Given I am in the lobby as "Sam"
  #   And there are 2 other players in the lobby
  #   When I refresh the lobby view
  #   Then I should see the current list of available players
  #   And player statuses should be up to date
  #   And my own status should remain unchanged
  #
  # Scenario: Lobby shows real-time updates
  #   Given I am in the lobby as "Tina"
  #   And "Uma" is also in the lobby
  #   When "Uma" receives a game request from another player
  #   Then I should see "Uma's" status change from "Available" to "Requesting Game"
  #   And the "Select Opponent" button for "Uma" should be disabled
  #   And I should see a visual indicator that "Uma" is no longer available
  #
  # Scenario: Leaving the lobby
  #   Given I am in the lobby as "Victor"
  #   And there are other players in the lobby
  #   When I click the "Leave Lobby" button
  #   Then I should be returned to the main menu or login page
  #   And other players should no longer see me in their lobby view
  #   And my status should be removed from the lobby
  #
  # Scenario: Network connection issues in lobby
  #   Given I am in the lobby as "Wendy"
  #   And I can see other available players
  #   When my network connection is temporarily lost
  #   Then I should see a "Connection lost" message
  #   And player selection should be disabled
  #   When my connection is restored
  #   Then the lobby should automatically refresh
  #   And I should be able to select opponents again
  #
  # Scenario Outline: Lobby capacity and performance
  #   Given I am in the lobby as "Xavier"
  #   When there are <player_count> other players in the lobby
  #   Then the lobby should display all <player_count> players
  #   And the interface should remain responsive
  #   And I should be able to scroll through the player list if needed
  #
  #   Examples:
  #     | player_count |
  #     | 5           |
  #     | 15          |
  #     | 50          |
  #
  # Scenario: Player status indicators are clear and accurate
  #   Given I am in the lobby as "Yuki"
  #   And there are players with different statuses:
  #     | Player Name | Status          |
  #     | Zoe         | Available       |
  #     | Aaron       | In Game         |
  #     | Beth        | Requesting Game |
  #   Then each player should have a clear visual status indicator
  #   And "Available" players should have green indicators
  #   And "In Game" players should have red indicators  
  #   And "Requesting Game" players should have yellow indicators
  #   And status text should be clearly readable
