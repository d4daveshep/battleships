Feature: Multiplayer Ship Placement
  As a player in a multiplayer game
  I want to place my ships while my opponent places theirs
  So that we can both prepare for battle and start the game together

  # Business Rules:
  # - Both players must place all 5 ships before the game can start
  # - Players place ships simultaneously (not turn-based)
  # - Players cannot see their opponent's ship positions
  # - Players can see their opponent's placement status (ready/not ready)
  # - Once a player clicks "Ready", they cannot modify their ship placement
  # - The game starts automatically when both players are ready
  # - Real-time updates show opponent's readiness status via long polling

  Background:
    Given I am playing a multiplayer game against another human player
    And both players have been matched and redirected to ship placement
    And I am on the ship placement screen
    And the "My Ships and Shots Received" board is displayed

  # === Multiplayer Placement Status ===

  Scenario: Initial multiplayer ship placement screen shows opponent status
    Given I have just entered the ship placement screen
    Then I should see my own placement area
    And I should see an opponent status indicator
    And the opponent status should show "Opponent is placing ships..."
    And I should not see my opponent's ship positions

  Scenario: Opponent status updates in real-time
    Given I am placing my ships
    And my opponent has not finished placing their ships
    When my opponent finishes placing all their ships
    Then the opponent status should update to "Opponent is ready"
    And I should receive this update within 5 seconds

  # === Ready State Management ===

  Scenario: Cannot click Ready until all ships are placed
    Given I have placed 4 out of 5 ships
    Then the "Ready" button should be disabled
    And I should see a message "Place all ships to continue"

  Scenario: Ready button becomes available when all ships placed
    Given I have placed 4 out of 5 ships
    When I place the 5th ship
    Then the "Ready" button should be enabled
    And I should see a message "All ships placed - click Ready when done"

  Scenario: Clicking Ready locks ship placement
    Given I have placed all 5 ships
    When I click the "Ready" button
    Then I should see a message "Waiting for opponent..."
    And I should not be able to remove any ships
    And I should not be able to place new ships
    And I should not be able to use the "Random Placement" button
    And I should not be able to use the "Reset All Ships" button

  Scenario: Ready status is communicated to opponent
    Given I have placed all 5 ships
    When I click the "Ready" button
    Then my opponent should see my status change to "Opponent is ready"
    And my opponent should receive this update within 5 seconds

  # === Game Start Conditions ===

  Scenario: Game starts when both players are ready
    Given I have placed all my ships and clicked "Ready"
    And I am waiting for my opponent
    When my opponent finishes placing ships and clicks "Ready"
    Then the game should start automatically
    And I should be redirected to the gameplay screen
    And I should see "Round 1" displayed

  Scenario: I am the second player to become ready
    Given my opponent has already clicked "Ready"
    And I have placed all 5 ships
    When I click the "Ready" button
    Then the game should start automatically
    And I should be redirected to the gameplay screen
    And I should see "Round 1" displayed

  Scenario: Both players become ready simultaneously
    Given I have placed all 5 ships
    And my opponent has placed all their ships
    When both players click "Ready" at approximately the same time
    Then the game should start for both players
    And both players should be redirected to the gameplay screen

  # === Waiting State ===

  Scenario: Waiting screen shows helpful information
    Given I have placed all my ships and clicked "Ready"
    Then I should see my ship placement displayed
    And I should see a message "Waiting for opponent to finish placing ships..."
    And I should see an animated waiting indicator
    And I should not see a "Cancel" button

  Scenario: Long wait for opponent
    Given I have placed all my ships and clicked "Ready"
    And I have been waiting for more than 30 seconds
    Then I should still see the waiting message
    And the connection should remain active via long polling

  # === Opponent Disconnection ===

  Scenario: Opponent leaves during ship placement
    Given I am placing my ships
    When my opponent leaves the game
    Then I should see a message "Opponent has left the game"
    And I should see an option to "Return to Lobby"

  Scenario: Opponent leaves while I am waiting
    Given I have placed all my ships and clicked "Ready"
    And I am waiting for my opponent
    When my opponent leaves the game
    Then I should see a message "Opponent has left the game"
    And I should see an option to "Return to Lobby"

  # === Ship Placement Privacy ===

  Scenario: Opponent cannot see my ship positions
    Given I have placed a "Carrier" horizontally starting at "A1"
    Then my opponent should not be able to see that I placed a ship at "A1"
    And my opponent should only see my placement status

  Scenario: I cannot see opponent's ship positions
    Given my opponent has placed all their ships
    Then I should not see any indication of where their ships are placed
    And I should only see that they are ready or not ready

  # === Placement Modifications Before Ready ===

  Scenario: Can modify ships while opponent is placing
    Given I have placed a "Destroyer" horizontally starting at "A1"
    And my opponent is still placing their ships
    When I click on the "Destroyer" to remove it
    Then the Destroyer should be removed from the board
    And I should be able to place it in a new location

  Scenario: Can use random placement while opponent is placing
    Given I have placed 2 ships manually
    And my opponent is still placing their ships
    When I click the "Random Placement" button
    Then all 5 ships should be placed automatically
    And my previous manual placements should be replaced

  Scenario: Can reset all ships while opponent is placing
    Given I have placed 3 ships on the board
    And my opponent is still placing their ships
    When I click the "Reset All Ships" button
    Then all ships should be removed from the board
    And I should be able to start placing ships again

  # === Edge Cases ===

  Scenario: Rapid ready/unready toggling is not allowed
    Given I have placed all 5 ships
    When I click the "Ready" button
    Then I should not see an "Unready" or "Cancel Ready" button
    And my ready status should be permanent until the game starts

  Scenario: Ship placement rules still apply in multiplayer
    Given I have placed a "Destroyer" horizontally starting at "E5"
    And I select the "Cruiser" ship to place
    When I attempt to place it horizontally starting at "E7"
    Then the placement should be rejected
    And I should see an error message "Ships must have empty space around them"
    And the Cruiser should not be placed

  Scenario: All ship types must be placed in multiplayer
    Given I have placed the following ships:
      | Ship       | Position | Orientation |
      | Carrier    | A1       | horizontal  |
      | Battleship | C1       | horizontal  |
      | Cruiser    | E1       | horizontal  |
      | Submarine  | G1       | horizontal  |
    Then the "Ready" button should be disabled
    And I should see "4 of 5 ships placed"
    When I place the "Destroyer" horizontally starting at "I1"
    Then the "Ready" button should be enabled
    And I should see "5 of 5 ships placed"

  # === Real-Time Updates ===

  Scenario: Placement status updates use long polling
    Given I am on the ship placement screen
    And my opponent is placing their ships
    When I observe the network activity
    Then there should be an active long-poll connection for opponent status
    And updates should arrive without page refresh

  Scenario: Connection resilience during ship placement
    Given I am placing my ships
    And the long-poll connection times out after 30 seconds
    When the connection is re-established
    Then I should see the current opponent status
    And I should be able to continue placing ships normally
