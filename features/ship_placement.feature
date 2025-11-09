Feature: Ship Placement
  As a player
  I want to place my ships on the board
  So that I can prepare for battle

  # Business Rules:
  # - Each player has 5 ships: Carrier (5), Battleship (4), Cruiser (3), Submarine (3), Destroyer (2)
  # - Ships can be horizontal, vertical or diagonal
  # - Ships can touch the edge of the board but cannot go outside or wrap around
  # - Ships cannot overlap another ship or be touching another ship
  # - There must be an empty space all around a ship (except where it touches the edge)
  # - Board is 10x10 grid (A-J rows, 1-10 columns)

  Background:
    Given I have logged in and selected a game mode
    And I am on the ship placement screen
    And the "My Ships and Shots Received" board is displayed
    And I have not placed any ships yet

  # === Horizontal Placement ===

  Scenario: Successfully place Destroyer horizontally
    Given I select the "Destroyer" ship to place
    When I place it horizontally starting at "A1"
    Then the Destroyer should be placed on the board
    And the Destroyer should occupy cells "A1" and "A2"
    And the Destroyer should be marked as placed

  Scenario: Successfully place Carrier horizontally
    Given I select the "Carrier" ship to place
    When I place it horizontally starting at "E3"
    Then the Carrier should be placed on the board
    And the Carrier should occupy cells "E3", "E4", "E5", "E6", and "E7"
    And the Carrier should be marked as placed

  # === Vertical Placement ===

  Scenario: Successfully place Battleship vertically
    Given I select the "Battleship" ship to place
    When I place it vertically starting at "B2"
    Then the Battleship should be placed on the board
    And the Battleship should occupy cells "B2", "C2", "D2", and "E2"
    And the Battleship should be marked as placed

  Scenario: Successfully place Submarine vertically
    Given I select the "Submarine" ship to place
    When I place it vertically starting at "F8"
    Then the Submarine should be placed on the board
    And the Submarine should occupy cells "F8", "G8", and "H8"
    And the Submarine should be marked as placed

  # === Diagonal Placement ===

  Scenario: Successfully place Cruiser diagonally (down-right)
    Given I select the "Cruiser" ship to place
    When I place it diagonally-down starting at "A1"
    Then the Cruiser should be placed on the board
    And the Cruiser should occupy cells "A1", "B2", and "C3"
    And the Cruiser should be marked as placed

  Scenario: Successfully place Destroyer diagonally (down-left)
    Given I select the "Destroyer" ship to place
    When I place it diagonally-down starting at "A10"
    Then the Destroyer should be placed on the board
    And the Destroyer should occupy cells "A10" and "B9"
    And the Destroyer should be marked as placed

  Scenario: Successfully place Submarine diagonally (up-right)
    Given I select the "Submarine" ship to place
    When I place it diagonally-up starting at "H3"
    Then the Submarine should be placed on the board
    And the Submarine should occupy cells "H3", "G4", and "F5"
    And the Submarine should be marked as placed

  # === Edge Placement (Valid) ===

  Scenario: Place ship touching top edge of board
    Given I select the "Destroyer" ship to place
    When I place it horizontally starting at "A1"
    Then the Destroyer should be placed on the board
    And no error message should be displayed

  Scenario: Place ship touching bottom edge of board
    Given I select the "Destroyer" ship to place
    When I place it horizontally starting at "J5"
    Then the Destroyer should be placed on the board
    And no error message should be displayed

  Scenario: Place ship touching left edge of board
    Given I select the "Cruiser" ship to place
    When I place it vertically starting at "D1"
    Then the Cruiser should be placed on the board
    And no error message should be displayed

  Scenario: Place ship touching right edge of board
    Given I select the "Cruiser" ship to place
    When I place it vertically starting at "D10"
    Then the Cruiser should be placed on the board
    And no error message should be displayed

  # === Invalid Placement - Outside Board ===

  Scenario: Attempt to place ship outside board (horizontal)
    Given I select the "Battleship" ship to place
    When I attempt to place it horizontally starting at "A9"
    Then the placement should be rejected
    And I should see an error message "Ship placement goes outside the board"
    And the Battleship should not be placed

  Scenario: Attempt to place ship outside board (vertical)
    Given I select the "Carrier" ship to place
    When I attempt to place it vertically starting at "H5"
    Then the placement should be rejected
    And I should see an error message "Ship placement goes outside the board"
    And the Carrier should not be placed

  Scenario: Attempt to place ship outside board (diagonal)
    Given I select the "Cruiser" ship to place
    When I attempt to place it diagonally-down starting at "J10"
    Then the placement should be rejected
    And I should see an error message "Ship placement goes outside the board"
    And the Cruiser should not be placed

  # === Invalid Placement - Ships Overlapping ===

  Scenario: Attempt to place ship overlapping another ship
    Given I have placed a "Destroyer" horizontally starting at "E5"
    And I select the "Cruiser" ship to place
    When I attempt to place it vertically starting at "D5"
    Then the placement should be rejected
    And I should see an error message "Ships cannot overlap"
    And the Cruiser should not be placed

  Scenario: Attempt to place ship with complete overlap
    Given I have placed a "Battleship" horizontally starting at "C3"
    And I select the "Submarine" ship to place
    When I attempt to place it horizontally starting at "C4"
    Then the placement should be rejected
    And I should see an error message "Ships cannot overlap"
    And the Submarine should not be placed

  # === Invalid Placement - Ships Touching (Adjacent) ===

  Scenario: Attempt to place ship directly adjacent horizontally
    Given I have placed a "Destroyer" horizontally starting at "E5"
    And I select the "Cruiser" ship to place
    When I attempt to place it horizontally starting at "E7"
    Then the placement should be rejected
    And I should see an error message "Ships must have empty space around them"
    And the Cruiser should not be placed

  Scenario: Attempt to place ship directly adjacent vertically
    Given I have placed a "Cruiser" vertically starting at "B3"
    And I select the "Destroyer" ship to place
    When I attempt to place it vertically starting at "B4"
    Then the placement should be rejected
    And I should see an error message "Ships must have empty space around them"
    And the Destroyer should not be placed

  Scenario: Attempt to place ship diagonally adjacent
    Given I have placed a "Destroyer" horizontally starting at "D4"
    And I select the "Submarine" ship to place
    When I attempt to place it diagonally-down starting at "E5"
    Then the placement should be rejected
    And I should see an error message "Ships must have empty space around them"
    And the Submarine should not be placed

  Scenario: Attempt to place ship adjacent at corners
    Given I have placed a "Destroyer" horizontally starting at "C3"
    And I select the "Destroyer" ship to place
    When I attempt to place it horizontally starting at "D4"
    Then the placement should be rejected
    And I should see an error message "Ships must have empty space around them"

  # === Valid Placement - Ships with Spacing ===

  Scenario: Place ships with proper spacing (horizontal)
    Given I have placed a "Destroyer" horizontally starting at "E5"
    And I select the "Cruiser" ship to place
    When I place it horizontally starting at "E8"
    Then the Cruiser should be placed on the board
    And no error message should be displayed

  Scenario: Place ships with proper spacing (vertical)
    Given I have placed a "Cruiser" vertically starting at "B3"
    And I select the "Destroyer" ship to place
    When I place it vertically starting at "B5"
    Then the Destroyer should be placed on the board
    And no error message should be displayed

  Scenario: Place ships with diagonal spacing
    Given I have placed a "Destroyer" horizontally starting at "C3"
    And I select the "Submarine" ship to place
    When I place it vertically starting at "E5"
    Then the Submarine should be placed on the board
    And no error message should be displayed

  # === Random Placement ===

  Scenario: Request random ship placement for player
    Given I have not placed any ships
    When I click the "Random Placement" button
    Then all 5 ships should be placed automatically
    And all ships should follow placement rules
    And no ships should overlap
    And no ships should be touching
    And all ships should be within the board boundaries

  Scenario: Reset and re-randomize ship placement
    Given I have placed some ships manually
    When I click the "Random Placement" button
    Then my manually placed ships should be removed
    And all 5 ships should be placed automatically following all rules

  # === Ship Placement Progress ===

  Scenario: Track ship placement progress
    Given I have not placed any ships
    Then I should see "0 of 5 ships placed"
    When I place the "Destroyer"
    Then I should see "1 of 5 ships placed"
    When I place the "Submarine"
    Then I should see "2 of 5 ships placed"

  Scenario: Cannot start game until all ships placed
    Given I have placed 4 out of 5 ships
    Then the "Start Game" button should be disabled
    When I place the 5th ship
    Then the "Start Game" button should be enabled

  # === Ship Removal/Reset ===

  Scenario: Remove a placed ship
    Given I have placed a "Carrier" horizontally starting at "A1"
    When I click on the "Carrier" to remove it
    Then the Carrier should be removed from the board
    And the Carrier should be available to place again
    And the ship count should show "0 of 5 ships placed"

  Scenario: Reset all ship placements
    Given I have placed 3 ships on the board
    When I click the "Reset All Ships" button
    Then all ships should be removed from the board
    And all ships should be available to place again
    And the ship count should show "0 of 5 ships placed"

  # === Computer Opponent Ship Placement ===

  Scenario: Computer opponent places ships automatically
    Given I am playing against a computer opponent
    And I have placed all my ships
    When I click the "Start Game" button
    Then the computer should automatically place all its ships
    And the computer's ship placement should follow all placement rules
    And the game should start immediately

  # === Multiplayer Ship Placement ===

  Scenario: Waiting for opponent to place ships
    Given I am playing against another human player
    And I have placed all my ships
    When I click the "Ready" button
    Then I should see a message "Waiting for opponent to place their ships..."
    And I should not be able to modify my ship placement

  Scenario: Both players ready - game starts
    Given I am playing against another human player
    And I have placed all my ships and clicked "Ready"
    And my opponent has placed all their ships and clicked "Ready"
    Then the game should start
    And both players should proceed to Round 1

  # === Invalid Ship Placement Patterns ===

  Scenario: Attempt to place ship with invalid direction
    Given I select the "Destroyer" ship to place
    When I attempt to place it with invalid direction starting at "A1"
    Then the placement should be rejected
    And I should see an error message "Invalid direction"
