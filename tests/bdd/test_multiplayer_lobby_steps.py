from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, Locator
from tests.bdd.conftest import login_and_select_multiplayer


scenarios("../../features/multiplayer_lobby.feature")


@given("the multiplayer lobby system is available")
def multiplayer_lobby_system_available(page: Page) -> None:
    # Verify the multiplayer lobby system is accessible
    # This step ensures the backend supports multiplayer functionality
    pass  # Will implement when backend is ready


@given("I have successfully logged in with multiplayer mode selected")
def logged_in_with_multiplayer_mode(page: Page) -> None:
    # Use shared login helper function
    login_and_select_multiplayer(page)


@given("there are other players in the lobby:")
def other_players_in_lobby(page: Page) -> None:
    # This step would normally set up pre-existing players in the lobby
    # Since we removed hardcoded players, this will drive proper implementation
    # of dynamic lobby state management with a Lobby class
    # For now, this test will fail and drive the implementation
    pass


@when(parsers.parse('I enter the multiplayer lobby as "{player_name}"'))
def enter_multiplayer_lobby(page: Page, player_name: str) -> None:
    # Navigate to the lobby page - this will test the actual /lobby endpoint
    page.goto(f"http://localhost:8000/lobby?player_name={player_name}")


@then("I should see the lobby interface")
def see_lobby_interface(page: Page) -> None:
    # Verify lobby interface elements are present
    assert page.locator("h1").text_content() == "Multiplayer Lobby"
    assert page.locator('[data-testid="lobby-container"]').is_visible()


@then("I should see my name")
def see_my_name(page: Page) -> None:
    # Verify the current player's name is displayed in the lobby
    # Should show the player name that was used during login
    my_name_element: Locator = page.locator('[data-testid="my-player-name"]')
    assert my_name_element.is_visible()
    # The text should contain some player name (not empty)
    assert my_name_element.text_content()
    # Should contain "Welcome" text to confirm it's the right element
    assert "Welcome" in my_name_element.text_content()


@then("I should see a list of available players:")
def see_available_players_list(page: Page) -> None:
    # Verify the player list shows expected players
    # In real implementation, this would parse the table data from the feature file
    # For now, we'll check for the expected players: Alice, Bob, Charlie

    player_list: Locator = page.locator('[data-testid="available-players-list"]')
    assert player_list.is_visible()

    # Check for specific expected players (Alice, Bob, Charlie from feature)
    expected_players: list[str] = ["Alice", "Bob", "Charlie"]
    for player_name in expected_players:
        player_item: Locator = page.locator(f'[data-testid="player-{player_name}"]')
        assert player_item.is_visible()
        assert player_name in player_item.text_content()


@then('I should see a "Select Opponent" button for each available player')
def see_select_opponent_buttons(page: Page) -> None:
    # Verify each available player has a select button
    select_buttons: Locator = page.locator('[data-testid^="select-opponent-"]')
    assert select_buttons.count() > 0

    # Each button should be visible and enabled
    for i in range(select_buttons.count()):
        button: Locator = select_buttons.nth(i)
        assert button.is_visible()
        assert button.is_enabled()
        assert "Select Opponent" in button.text_content()


@then(parsers.parse('I should see my own status as "{status}"'))
def see_own_status(page: Page, status: str) -> None:
    # Verify our own player status is displayed correctly
    own_status: Locator = page.locator('[data-testid="own-player-status"]')
    assert own_status.is_visible()
    assert status in own_status.text_content()


@given("there are no other players in the lobby")
def no_other_players_in_lobby(page: Page) -> None:
    # This step sets up the condition where the lobby is empty
    # Since we removed hardcoded players, the lobby should already be empty
    # This will test the UI behavior when no players are available
    pass


@then('I should see a message "No other players available"')
def see_no_players_message(page: Page) -> None:
    # Verify that the empty lobby shows appropriate message
    no_players_message: Locator = page.locator('[data-testid="no-players-message"]')
    assert no_players_message.is_visible()
    assert "No other players available" in no_players_message.text_content()


@then('I should see a message "Waiting for other players to join..."')
def see_waiting_message(page: Page) -> None:
    # Verify that the lobby shows waiting message for empty state
    waiting_message: Locator = page.locator('[data-testid="waiting-message"]')
    assert waiting_message.is_visible()
    assert "Waiting for other players to join..." in waiting_message.text_content()


@then("I should not see any selectable players")
def no_selectable_players(page: Page) -> None:
    # Verify that no player selection buttons or player items are visible
    select_buttons: Locator = page.locator('[data-testid^="select-opponent-"]')
    
    # No select opponent buttons should be visible in empty lobby
    assert select_buttons.count() == 0


@then(parsers.parse('my status should be "{status}"'))
def my_status_should_be(page: Page, status: str) -> None:
    # Verify own player status - same as see_own_status but different wording
    own_status: Locator = page.locator('[data-testid="own-player-status"]')
    assert own_status.is_visible()
    assert status in own_status.text_content()
