Feature: Two-Player Shot Validation
  As a player in a two-player Battleships game
  I want validation when selecting shot coordinates
  So that invalid shots are prevented

  Background:
    Given both players have completed ship placement
    And both players are ready
    And the game has started
    And I am on the gameplay page

  # === Shot Validation ===

  # Scenario: Cannot fire at coordinates already fired at in previous rounds
  #   Given it is Round 3
  #   And I fired at "E5" in Round 1
  #   When I attempt to select coordinate "E5" to aim at
  #   Then I should see an error message "You have already fired at this coordinate"
  #   And the coordinate should not be selectable
  #   And it should show as already fired with round number "1"
  #
  # Scenario: Cannot fire at invalid coordinates
  #   Given it is Round 1
  #   When I attempt to fire at coordinate "K11"
  #   Then I should see an error message "Invalid coordinate"
  #   And the shot should not be recorded
  #
  # Scenario: Must fire at unique coordinates within the same round
  #   Given it is Round 1
  #   And I have selected coordinates "A1", "B2", "C3"
  #   When I attempt to select "A1" again in the same round
  #   Then I should see an error message "Coordinate already selected for this round"
  #   And I should still have 3 shots aimed, not 4