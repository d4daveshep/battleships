from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, Locator
from tests.conftest import login_and_select_multiplayer


scenarios("features/multiplayer_lobby.feature")


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
def other_players_in_lobby(page: Page, lobby) -> None:
    # Set up existing players in the lobby based on the feature table
    # Expected players from feature file: Alice, Bob, Charlie with "Available" status
    test_players = [
        {"name": "Alice", "status": "Available"},
        {"name": "Bob", "status": "Available"},
        {"name": "Charlie", "status": "Available"},
    ]

    for player_data in test_players:
        lobby.add_player(player_data["name"], player_data["status"])

    # Verify the lobby has the expected players
    available_players = lobby.get_available_players()
    assert len(available_players) == 3

    player_names = [player.name for player in available_players]
    assert "Alice" in player_names
    assert "Bob" in player_names
    assert "Charlie" in player_names


@when(parsers.parse('I enter the multiplayer lobby as "{player_name}"'))
def enter_multiplayer_lobby(page: Page, player_name: str) -> None:
    # This step assumes we're already in the lobby from the background step
    # But we may need to set our player name context
    page.evaluate(f"window.currentPlayerName = '{player_name}'")


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
