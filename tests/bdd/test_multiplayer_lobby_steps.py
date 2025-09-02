from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, Locator
from tests.bdd.conftest import login_and_select_multiplayer


scenarios("../../features/multiplayer_lobby.feature")


@given("the multiplayer lobby system is available")
def multiplayer_lobby_system_available(page: Page) -> None:
    # Verify the multiplayer lobby system is accessible
    # This step ensures the backend supports multiplayer functionality
    assert False, "this needs implementing"


@given("I have successfully logged in with multiplayer mode selected")
def logged_in_with_multiplayer_mode(page: Page) -> None:
    # Use shared login helper function
    login_and_select_multiplayer(page)


@given("there are other players in the lobby:")
def other_players_in_lobby(page: Page) -> None:
    # This step would normally set up pre-existing players in the lobby
    # For now we'll simulate having players Alice, Bob, Charlie available
    # This will drive proper implementation of lobby state management
    expected_players = [
        {"name": "Alice", "status": "Available"},
        {"name": "Bob", "status": "Available"},
        {"name": "Charlie", "status": "Available"},
    ]
    setattr(page, "expected_lobby_players", expected_players)
    # For now, this test will fail and drive the implementation

    assert False, "this needs implementing"


@when(parsers.parse('I enter the multiplayer lobby as "{player_name}"'))
def enter_multiplayer_lobby(page: Page, player_name: str) -> None:
    # Navigate to the lobby page - this will test the actual /lobby endpoint
    page.goto(f"http://localhost:8000/lobby?player_name={player_name}")
    # Store current player name for later verification
    setattr(page, "current_player_name", player_name)


@then("I should see the lobby interface")
def see_lobby_interface(page: Page) -> None:
    # Verify lobby interface elements are present
    lobby_title = page.locator("h1").text_content()
    assert lobby_title == "Multiplayer Lobby"
    assert page.locator('[data-testid="lobby-container"]').is_visible()


@then("I should see my name")
def see_my_name(page: Page) -> None:
    # Verify the current player's name is displayed in the lobby
    # Should show the player name that was used during login
    my_name_element: Locator = page.locator('[data-testid="my-player-name"]')
    assert my_name_element.is_visible()
    # The text should contain the actual player name
    current_player = getattr(page, "current_player_name", "TestPlayer")
    name_text = my_name_element.text_content()
    assert name_text is not None
    assert current_player in name_text


@then("I should see a list of available players:")
def see_available_players_list(page: Page) -> None:
    # Verify the player list shows expected players Alice, Bob, Charlie
    player_list: Locator = page.locator('[data-testid="available-players-list"]')
    assert player_list.is_visible()

    # Check for expected players from the feature scenario
    expected_players: list[str] = ["Alice", "Bob", "Charlie"]

    # Check for each expected player
    for player_name in expected_players:
        player_item: Locator = page.locator(f'[data-testid="player-{player_name}"]')
        assert player_item.is_visible()
        player_text = player_item.text_content()
        assert player_text is not None
        assert player_name in player_text


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
        button_text = button.text_content()
        assert button_text is not None
        assert "Select Opponent" in button_text


@then(parsers.parse('I should see my own status as "{status}"'))
def see_own_status(page: Page, status: str) -> None:
    # Verify our own player status is displayed correctly
    own_status: Locator = page.locator('[data-testid="own-player-status"]')
    assert own_status.is_visible()
    status_text = own_status.text_content()
    assert status_text is not None
    assert status in status_text


@given("there are no other players in the lobby")
def no_other_players_in_lobby(page: Page) -> None:
    # This step sets up the condition where the lobby is empty
    # Since we removed hardcoded players, the lobby should already be empty
    # This will test the UI behavior when no players are available
    assert False, "this needs implementing"


@then('I should see a message "No other players available"')
def see_no_players_message(page: Page) -> None:
    # Verify that the empty lobby shows appropriate message
    no_players_message: Locator = page.locator('[data-testid="no-players-message"]')
    assert no_players_message.is_visible()
    message_text = no_players_message.text_content()
    assert message_text is not None
    assert "No other players available" in message_text


@then('I should see a message "Waiting for other players to join..."')
def see_waiting_message(page: Page) -> None:
    # Verify that the lobby shows waiting message for empty state
    waiting_message: Locator = page.locator('[data-testid="waiting-message"]')
    assert waiting_message.is_visible()
    waiting_text = waiting_message.text_content()
    assert waiting_text is not None
    assert "Waiting for other players to join..." in waiting_text


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
    status_text = own_status.text_content()
    assert status_text is not None
    assert status in status_text


# New step definitions for the "another player joins while waiting" scenario


@given(parsers.parse('I am waiting in an empty lobby as "{player_name}"'))
def waiting_in_empty_lobby(page: Page, player_name: str) -> None:
    # Set up the condition where player is already in an empty lobby
    # This combines entering the lobby and verifying it's empty
    page.goto(f"http://localhost:8000/lobby?player_name={player_name}")
    setattr(page, "current_player_name", player_name)

    # Verify we're in an empty lobby state
    waiting_message: Locator = page.locator('[data-testid="waiting-message"]')
    assert waiting_message.is_visible()


@given('I see the message "Waiting for other players to join..."')
def see_waiting_message_given(page: Page) -> None:
    # Verify the waiting message is displayed (given state)
    waiting_message: Locator = page.locator('[data-testid="waiting-message"]')
    assert waiting_message.is_visible()
    waiting_text = waiting_message.text_content()
    assert waiting_text is not None
    assert "Waiting for other players to join..." in waiting_text


@when(parsers.parse('another player "{player_name}" joins the lobby'))
def another_player_joins_lobby(page: Page, player_name: str) -> None:
    # Simulate another player joining the lobby by making an HTTP request
    # In a real application, this would involve WebSocket updates or polling
    # For BDD testing, simulate the player joining by visiting the lobby page

    # Store the expected new player for verification
    setattr(page, "expected_new_player", player_name)

    # Simulate the new player joining by making a request to the lobby
    # This will add the player to the lobby state via the normal flow
    import httpx

    # Make a request as the new player to register them in the lobby
    with httpx.Client() as client:
        response = client.get(f"http://localhost:8000/lobby?player_name={player_name}")

    # Refresh the current page to see the updated lobby state
    page.reload()


@then(parsers.parse('I should see "{player_name}" in the available players list'))
def see_new_player_in_list(page: Page, player_name: str) -> None:
    # Verify the new player appears in the available players list
    player_item: Locator = page.locator(f'[data-testid="player-{player_name}"]')
    assert player_item.is_visible()
    player_text = player_item.text_content()
    assert player_text is not None
    assert player_name in player_text


@then(parsers.parse('I should see a "Select Opponent" button next to "{player_name}"'))
def see_select_button_for_player(page: Page, player_name: str) -> None:
    # Verify there's a select opponent button for the specific player
    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{player_name}"]'
    )
    assert select_button.is_visible()
    assert select_button.is_enabled()
    button_text = select_button.text_content()
    assert button_text is not None
    assert "Select Opponent" in button_text


@then('the "Waiting for other players" message should be hidden')
def waiting_message_hidden(page: Page) -> None:
    # Verify the waiting message is no longer visible when players are available
    waiting_message: Locator = page.locator('[data-testid="waiting-message"]')
    assert not waiting_message.is_visible()


@then(parsers.parse('I should be able to select "{player_name}" as my opponent'))
def can_select_player_as_opponent(page: Page, player_name: str) -> None:
    # Verify the select button is functional for the new player
    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{player_name}"]'
    )
    assert select_button.is_visible()
    assert select_button.is_enabled()

    # Verify clicking the button would work (but don't actually click in this test)
    # The button should not be disabled and should be interactive
    assert not select_button.is_disabled()

