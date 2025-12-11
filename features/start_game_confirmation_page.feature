Feature: Start Game Confirmation
  As a game player
  After I've logged in and selected my opponent
  I want to confirm that game details before I place my ships and start the game

Background:
  Given I am on the start game confirmation page
  And the page is fully loaded

Scenario: Start game
  Given the game details are correct
  When I choose "Start Game"
  Then I should be redirected to the ship placement page

Scenario: Return to login page
  When I choose "Return to Login"
  Then I should be redirected to the login page

Scenario: Exit completely
  When I choose "Exit"
  Then I should be redirected to the goodbye page
