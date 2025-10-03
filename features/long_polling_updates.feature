Feature: Long Polling Real-Time Updates
  As a player in the multiplayer lobby
  I want to receive real-time updates about lobby state changes
  So that I can see when other players join, leave, or send game requests without delay

  # Technical Implementation:
  # - Frontend uses long polling (/lobby/status/{player}/long-poll endpoint)
  # - Backend holds connection until state change or 30s timeout
  # - Event-based notifications trigger immediate response on state change
  # - HTMX automatically reconnects after each response

  Background:
    Given the multiplayer lobby system is available
    And long polling is enabled

  Scenario: Real-time update when another player joins
    Given I've logged in as "Alice" and selected human opponent
    And I see the message "Waiting for other players to join..."
    When another player "Bob" joins the lobby within 5 seconds
    Then I should see "Bob" appear in my lobby within 5 seconds
    And I should not have to wait for a polling interval

  Scenario: Real-time update when player leaves
    Given I've logged in as "Alice" and selected human opponent
    And another player "Bob" is already in the lobby
    And I can see "Bob" in my available players list
    When "Bob" leaves the lobby
    Then "Bob" should disappear from my lobby within 5 seconds
    And the "No other players available" message should appear

  Scenario: Real-time update when receiving game request
    Given I've logged in as "Alice" and selected human opponent
    And another player "Bob" is already in the lobby
    When "Bob" sends me a game request
    Then I should see the game request notification within 5 seconds
    And the notification should say "Game request from Bob"
    And I should see "Accept" and "Decline" buttons

  Scenario: Real-time update when game request is accepted
    Given I've logged in as "Alice" and selected human opponent
    And another player "Bob" is already in the lobby
    And I have sent a game request to "Bob"
    When "Bob" accepts my game request
    Then I should be redirected to the game page within 5 seconds
    And the game should be with opponent "Bob"

  Scenario: Real-time update when game request is declined
    Given I've logged in as "Alice" and selected human opponent
    And another player "Bob" is already in the lobby
    And I have sent a game request to "Bob"
    When "Bob" declines my game request
    Then I should see a message that the request was declined within 5 seconds
    And both "Alice" and "Bob" should return to "Available" status

  Scenario: Multiple rapid state changes all received
    Given I've logged in as "Alice" and selected human opponent
    And I see the message "Waiting for other players to join..."
    When the following players join in quick succession:
      | Player Name |
      | Bob         |
      | Charlie     |
      | Diana       |
    Then I should see all players appear in my lobby within 10 seconds
    And I should see "Bob" in the available players list
    And I should see "Charlie" in the available players list
    And I should see "Diana" in the available players list

  Scenario: Connection resilience after timeout
    Given I've logged in as "Alice" and selected human opponent
    And I see the message "Waiting for other players to join..."
    And I wait for 35 seconds
    When another player "Bob" joins the lobby
    Then I should see "Bob" appear in my lobby
    And the long polling connection should have automatically reconnected

  Scenario: Player status changes are immediately visible
    Given I've logged in as "Alice" and selected human opponent
    And another player "Bob" is already in the lobby
    And another player "Charlie" is already in the lobby
    When "Bob" sends a game request to "Charlie"
    Then I should see "Bob" status change to "Requesting Game" within 5 seconds
    And I should see "Charlie" status change to "Pending Response" within 5 seconds
    And I should not be able to select "Bob" as opponent
    And I should not be able to select "Charlie" as opponent

  Scenario: Long polling reduces unnecessary server requests
    Given I've logged in as "Alice" and selected human opponent
    And I see the message "Waiting for other players to join..."
    When I observe the network activity for 10 seconds
    Then there should be at most 1 request to the lobby status endpoint
    And the request should be a long-poll request
    And the request should not complete until timeout or state change

  Scenario: State changes wake up waiting long poll requests
    Given I've logged in as "Alice" and selected human opponent
    And I see the message "Waiting for other players to join..."
    And a long polling request is active and waiting
    When another player "Bob" joins the lobby
    Then the waiting long poll request should complete immediately
    And I should receive the updated lobby state showing "Bob"
    And a new long poll request should be initiated automatically
