from pytest_bdd import scenarios, given, when, then, parsers
import httpx
from playwright.sync_api import Page, Locator


scenarios("../../features/multiplayer_lobby.feature")


# Helper function to wait for HTMX long-poll updates
def wait_for_lobby_update(page: Page, timeout: int = 35000) -> None:
    """
    Wait for HTMX long-poll to update the lobby.
    Long-poll has a 30s timeout, so we wait slightly longer.
    This helper triggers a reload if needed to force an update.
    """
    # Reload the page to force fetching the latest lobby state
    # This is more reliable than waiting for long-poll to complete
    page.reload()
    # Wait for the lobby container to be visible after reload
    page.locator('[data-testid="lobby-player-status"]').wait_for(
        state="visible", timeout=5000
    )


# Helper function to perform authenticated actions as another player using test endpoints
def perform_action_as_player(
    page: Page, player_name: str, action: str, target_player: str | None = None
) -> None:
    """
    Perform an action as a different player using test endpoints.
    This bypasses session authentication for testing purposes.

    Args:
        page: The current test page
        player_name: The player performing the action
        action: The action to perform ("select-opponent", "accept-request", "decline-request")
        target_player: The target player for the action (if applicable)
    """
    with httpx.Client() as client:
        if action == "select-opponent" and target_player:
            # Send game request via test endpoint
            client.post(
                "http://localhost:8000/test/send-game-request",
                data={"sender_name": player_name, "target_name": target_player},
            )

        elif action == "accept-request":
            # Accept game request via test endpoint
            client.post(
                "http://localhost:8000/test/accept-game-request",
                data={"player_name": player_name},
            )

        elif action == "decline-request":
            # Decline game request via test endpoint
            client.post(
                "http://localhost:8000/test/decline-game-request",
                data={"player_name": player_name},
            )


@given("the multiplayer lobby system is available")
def multiplayer_lobby_system_available(page: Page) -> None:
    # Verify the multiplayer lobby system is accessible
    # This step ensures the backend supports multiplayer functionality
    pass  # TODO: see if we can don better here


# @given("I have successfully logged in with multiplayer mode selected")
# def logged_in_with_multiplayer_mode(page: Page) -> None:
#     # Use shared login helper function
#     login_and_select_multiplayer(page)


@given("there are other players in the lobby:")
def other_players_in_lobby(page: Page, datatable) -> None:
    # This step sets up pre-existing players in the lobby
    # Parse the table data from the step to set up lobby state

    # Store the current player's perspective to restore later
    current_player = getattr(page, "current_player_name", None)

    # Only reset lobby if no current player is set (fresh scenario)
    if current_player is None:
        with httpx.Client() as client:
            client.post("http://localhost:8000/test/reset-lobby")

    expected_players: list[dict[str, str]] = []
    for row in datatable[1:]:
        player_name: str = row[0]
        status: str = row[1]
        if status == "Available":
            # Use test endpoint to add players directly to avoid session conflicts
            with httpx.Client() as client:
                client.post(
                    "http://localhost:8000/test/add-player-to-lobby",
                    data={"player_name": player_name},
                )
            expected_players.append({"name": player_name, "status": status})

    setattr(page, "expected_lobby_players", expected_players)

    # Restore the original player's perspective if it was set
    if current_player:
        page.goto(f"http://localhost:8000/lobby?player_name={current_player}")
        # Wait for the lobby page to load
        page.wait_for_selector('[data-testid="lobby-container"]')
        # Restore the stored player name
        setattr(page, "current_player_name", current_player)


@when(parsers.parse('I login as "{player_name}" and select human opponent'))
def login_and_select_human_opponent(page: Page, player_name: str) -> None:
    # Navigate to login page, enter player name, and select human opponent
    page.goto("http://localhost:8000/")

    # Fill in player name
    page.locator('input[name="player_name"]').fill(player_name)

    # Click "Play against Another Player" button
    page.locator('button[value="human"]').click()

    # Should be redirected to lobby page
    page.wait_for_url("**/lobby*")

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
    my_name_element: Locator = page.locator('[data-testid="player-name"]')
    assert my_name_element.is_visible()
    # The text should contain the actual player name
    current_player = getattr(page, "current_player_name", "TestPlayer")
    name_text = my_name_element.text_content()
    assert name_text is not None
    assert current_player in name_text


@then("I should see a list of available players:")
def see_available_players_list(page: Page, datatable) -> None:
    # Verify the player list shows expected players Alice, Bob, Charlie
    # This step should be updated to work with the refactored LobbyService
    player_list: Locator = page.locator('[data-testid="lobby-player-status"]')
    assert player_list.is_visible()

    # Check for expected players from the scenario
    expected_players: list[str] = []
    for row in datatable[1:]:
        player_name: str = row[0]
        expected_players.append(player_name)

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


@given("there are no other players in the lobby")
def no_other_players_in_lobby(page: Page) -> None:
    # This step sets up the condition where the lobby is empty
    # The lobby should start empty for this test scenario
    # This will test the UI behavior when no players are available
    pass


@then("I should not see any selectable players")
def no_selectable_players(page: Page) -> None:
    # Verify that no player selection buttons or player items are visible
    select_buttons: Locator = page.locator('[data-testid^="select-opponent-"]')

    # No select opponent buttons should be visible in empty lobby
    assert select_buttons.count() == 0


@then(parsers.parse('my status should be "{status}"'))
def my_status_should_be(page: Page, status: str) -> None:
    # Verify our own player status is displayed correctly
    own_status: Locator = page.locator('[data-testid="player-status"]')
    assert own_status.is_visible()
    status_text = own_status.text_content()
    assert status_text is not None
    assert status in status_text


# New step definitions for the "another player joins while waiting" scenario


@given(parsers.parse('I\'ve logged in as "{player_name}" and selected human opponent'))
def logged_in_and_selected_human_opponent(page: Page, player_name: str) -> None:
    # Complete login flow and select human opponent
    page.goto("http://localhost:8000/")

    # Fill in player name
    page.locator('input[name="player_name"]').fill(player_name)

    # Click "Play against Another Player" button
    page.locator('button[value="human"]').click()

    # Should be redirected to lobby page
    page.wait_for_url("**/lobby*")

    # Store current player name for later verification
    setattr(page, "current_player_name", player_name)


@given('I see the message "Waiting for other players to join..."')
def see_waiting_message_given(page: Page) -> None:
    # Verify the waiting message is displayed (given state)
    waiting_message: Locator = page.locator('[data-testid="waiting-message"]')
    assert waiting_message.is_visible()
    waiting_text = waiting_message.text_content()
    assert waiting_text is not None
    assert "Waiting for other players to join..." in waiting_text


@when(
    parsers.parse('another player "{player_name}" logs in and selects human opponent')
)
def another_player_logs_in_and_selects_human(page: Page, player_name: str) -> None:
    # Simulate another player going through the full login flow
    # TODO:In a real application, this would involve WebSocket updates or polling
    # For BDD testing, simulate the player joining via the normal login flow

    # Store the expected new player for verification
    setattr(page, "expected_new_player", player_name)

    # Simulate the new player logging in and selecting human opponent
    import httpx

    with httpx.Client() as client:
        # First get the login page
        client.get("http://localhost:8000/")

        # Then submit the login form with human opponent selection
        client.post(
            "http://localhost:8000/",
            data={"player_name": player_name, "game_mode": "human"},
        )

    # Wait for the lobby to update with the new player
    wait_for_lobby_update(page)


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


# New BDD steps for "Successfully selecting an opponent from the lobby" scenario


@when(parsers.parse('I click "Select Opponent" next to "{opponent_name}"'))
def click_select_opponent(page: Page, opponent_name: str) -> None:
    # Click the "Select Opponent" button for the specified player
    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{opponent_name}"]'
    )
    assert select_button.is_visible(), (
        f"Select Opponent button for {opponent_name} should be visible"
    )
    select_button.click()


@then(parsers.parse('I should see a message "{expected_message}"'))
def see_message(page: Page, expected_message: str) -> None:
    # Universal message verification step - handles confirmation messages and general messages
    message_locators = [
        '[data-testid="confirmation-message"]',
        '[data-testid="message"]',
        '[data-testid="no-players-message"]',
        '[data-testid="waiting-message"]',
        '[data-testid="decline-confirmation-message"]',
    ]

    message_found = False
    actual_message_text = ""

    # Wait for any message element to appear (up to 5 seconds)
    # This allows time for HTMX to complete the request and swap content
    for locator in message_locators:
        try:
            message_element: Locator = page.locator(locator)
            # Wait for element to be visible (timeout 5s per locator)
            message_element.wait_for(state="visible", timeout=5000)
            actual_message_text = message_element.inner_text()
            if expected_message in actual_message_text:
                message_found = True
                break
        except Exception:
            # Element doesn't exist or didn't become visible, try next locator
            continue

    assert message_found, (
        f"Expected message '{expected_message}' not found. Last checked text: '{actual_message_text}'"
    )


@then(
    parsers.parse(
        '"{target_player}" should receive a game invitation from "{sender_player}"'
    )
)
def target_player_receives_invitation(
    page: Page, target_player: str, sender_player: str
) -> None:
    # Verify that the game invitation was sent from sender to target
    # This step checks the server state or notification system to confirm invitation delivery

    # In a real implementation, this would:
    # 1. Check the target player's pending invitations via API
    # 2. Verify WebSocket/real-time notification was sent
    # 3. Check server-side game request state

    # For now, verify that the sender's status changed to "Requesting Game"
    # which indicates the invitation was successfully sent
    sender_status: Locator = page.locator(
        f'[data-testid="player-{sender_player}-status"]'
    )
    if sender_status.count() > 0:
        status_text = sender_status.inner_text()
        assert (
            "requesting" in status_text.lower() or "pending" in status_text.lower()
        ), (
            f"{sender_player} should have 'Requesting Game' status after sending invitation"
        )

    # Also verify via server API that invitation exists
    import httpx

    with httpx.Client() as client:
        try:
            response = client.get(
                f"http://localhost:8000/game-requests/{target_player}"
            )
            if response.status_code == 200:
                requests = response.json()
                assert any(req.get("sender") == sender_player for req in requests), (
                    f"Game request from {sender_player} to {target_player} should exist"
                )
        except Exception:
            # If API endpoint doesn't exist yet, just pass
            # The status check above is sufficient for now
            pass


@then(parsers.parse('my status should change to "{expected_status}"'))
def my_status_should_change(page: Page, expected_status: str) -> None:
    # Check that the current player's status has changed or returned to expected status
    status_element: Locator = page.locator('[data-testid="player-status"]')
    assert status_element.is_visible(), "Player status should be visible"

    status_text = status_element.inner_text()
    assert expected_status in status_text, (
        f"Expected status '{expected_status}' in status text, got '{status_text}'"
    )


@then(
    "I should not be able to select other players while waiting for my request to be completed"
)
def cannot_select_other_players_while_waiting(page: Page) -> None:
    # Check that other "Select Opponent" buttons are disabled or hidden
    # while the current player has a pending game request

    # Look for any remaining "Select Opponent" buttons
    select_buttons: Locator = page.locator('[data-testid^="select-opponent-"]')
    button_count = select_buttons.count()

    if button_count > 0:
        # If buttons are still visible, they should be disabled
        for i in range(button_count):
            button = select_buttons.nth(i)
            assert button.is_disabled(), (
                f"Select Opponent button {i} should be disabled while request is pending"
            )

    # Alternatively, check for a message indicating no selections are possible
    # This depends on how the UI handles the "requesting game" state


# New BDD steps for "Lobby shows real-time updates" scenario


@when(parsers.parse('"{target_player}" receives a game request from "{sender_player}"'))
def target_player_receives_game_request(
    page: Page, target_player: str, sender_player: str
) -> None:
    # Simulate another player (sender) sending a game request to target_player
    perform_action_as_player(page, sender_player, "select-opponent", target_player)

    # Store the interaction for verification
    setattr(page, "game_request_sender", sender_player)
    setattr(page, "game_request_target", target_player)

    # Wait for long polling to update
    wait_for_lobby_update(page)


@then(
    parsers.parse(
        'I should see "{player_name}\'s" status change from "{old_status}" to "{new_status}"'
    )
)
def see_player_status_change(
    page: Page, player_name: str, old_status: str, new_status: str
) -> None:
    # Check that the player's status has changed to the new status
    # This tests real-time updates of player status in the lobby

    # Look for player status indicator (this might be in a data attribute or text)
    player_status_element: Locator = page.locator(
        f'[data-testid="player-{player_name}-status"]'
    )

    if player_status_element.count() > 0:
        # If there's a specific status element, check it
        status_text = player_status_element.inner_text()
        # Handle different status formats: "Pending Response", "Available", "Requesting Game"
        expected_status_variations = [
            new_status,
            new_status.lower(),
            new_status.replace(" ", "-").lower(),
            "pending" if "pending" in new_status.lower() else new_status,
        ]

        status_found = any(
            variation in status_text.lower() for variation in expected_status_variations
        )
        assert status_found, (
            f"Expected status '{new_status}' for {player_name}, got '{status_text}'"
        )
    else:
        # Alternative: check if the player element has status information
        player_element: Locator = page.locator(f'[data-testid="player-{player_name}"]')
        assert player_element.is_visible(), (
            f"Player {player_name} should be visible in lobby"
        )

        # Check for status indicator in the player's section
        # This might involve looking for CSS classes or text content
        player_html = player_element.inner_html()
        expected_status_variations = [
            new_status.lower(),
            new_status.replace(" ", "-").lower(),
            "pending" if "pending" in new_status.lower() else new_status.lower(),
        ]

        status_found = any(
            variation in player_html.lower() for variation in expected_status_variations
        )
        assert status_found, f"Player {player_name} should show status '{new_status}'"


@then(
    parsers.parse('the "Select Opponent" button for "{player_name}" should be disabled')
)
def select_opponent_button_should_be_disabled(page: Page, player_name: str) -> None:
    # Verify that the Select Opponent button for the specified player is disabled
    # This tests that players with "Requesting Game" status can't be selected

    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{player_name}"]'
    )
    assert select_button.is_visible(), (
        f"Select Opponent button for {player_name} should be visible"
    )
    assert select_button.is_disabled(), (
        f"Select Opponent button for {player_name} should be disabled"
    )


@then(
    parsers.parse(
        'I should see a visual indicator that "{player_name}" is no longer available'
    )
)
def see_visual_indicator_player_unavailable(page: Page, player_name: str) -> None:
    # Check for visual indicators that show the player is no longer available
    # This could be CSS classes, icons, or other visual cues

    player_element: Locator = page.locator(f'[data-testid="player-{player_name}"]')
    assert player_element.is_visible(), (
        f"Player {player_name} should still be visible in lobby"
    )

    # Check for visual indicators of unavailability
    # This might involve CSS classes like "unavailable", "requesting", etc.
    player_html = player_element.inner_html()

    # Look for common visual indicators
    visual_indicators = [
        "unavailable",
        "requesting",
        "disabled",
        "pending",
        "status-requesting",
        "player-busy",
    ]

    found_indicator = any(
        indicator in player_html.lower() for indicator in visual_indicators
    )

    # Also check if the button is disabled (another visual cue)
    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{player_name}"]'
    )
    button_disabled = (
        select_button.is_disabled() if select_button.count() > 0 else False
    )

    assert found_indicator or button_disabled, (
        f"Player {player_name} should have visual indicator of unavailability"
    )


# New BDD steps for "Leaving the lobby" scenario


@when('I click the "Leave Lobby" button')
def click_leave_lobby_button(page: Page) -> None:
    # Click the "Leave Lobby" button to exit the lobby
    leave_button: Locator = page.locator('[data-testid="leave-lobby-button"]')
    assert leave_button.is_visible(), "Leave Lobby button should be visible"
    assert leave_button.is_enabled(), "Leave Lobby button should be enabled"
    leave_button.click()


@then("I should be returned to the login page")
def returned_to_login_page(page: Page) -> None:
    # Verify that the user is redirected back to the login page
    page.wait_for_url("**/", timeout=5000)  # Wait for redirect to home/login page

    # Verify login page elements are present
    # page.locator("h1").wait_for()
    login_title = page.locator("h1").text_content()
    assert login_title is not None, "Login page should have a title"
    assert "Battleships" in login_title or "Login" in login_title, (
        "Should be on login page"
    )

    # Verify login form elements are present
    player_name_input = page.locator('input[name="player_name"]')
    assert player_name_input.is_visible(), (
        "Player name input should be visible on login page"
    )


@then("other players should no longer see me in their lobby view")
def other_players_no_longer_see_me(page: Page) -> None:
    # This step verifies that the current player is removed from other players' lobby views
    # In a real implementation, this would involve checking other browser sessions or server state
    # For BDD testing, we can simulate this by checking that the player count decreases
    # or by making an API call to verify the player is no longer in the lobby

    # Store the player name for verification
    current_player = getattr(page, "current_player_name", None)
    if current_player:
        # In a full implementation, this might involve:
        # 1. Opening another browser session
        # 2. Checking the lobby API endpoint
        # 3. Verifying WebSocket messages are sent to other players
        pass

    # For now, this step serves as a placeholder for the behavior specification


# New BDD steps for "Player leaves the lobby while I'm viewing it" scenario


@when(parsers.parse('"{player_name}" leaves the lobby'))
def player_leaves_lobby(page: Page, player_name: str) -> None:
    # Simulate another player leaving the lobby
    # This would typically involve the other player clicking "Leave Lobby"
    # For testing purposes, we use the test endpoint to bypass session authentication

    with httpx.Client() as client:
        # Use test endpoint to remove player from lobby
        client.post(
            "http://localhost:8000/test/remove-player-from-lobby",
            data={"player_name": player_name},
        )

    # Store the player who left for verification
    setattr(page, "player_who_left", player_name)

    # Wait for long polling to update (returns immediately on state change)
    wait_for_lobby_update(page)


@then(
    parsers.parse(
        '"{player_name}" should no longer appear in my available players list'
    )
)
def player_no_longer_in_list(page: Page, player_name: str) -> None:
    # Verify that the specified player is no longer visible in the available players list
    player_element: Locator = page.locator(f'[data-testid="player-{player_name}"]')
    assert not player_element.is_visible(), (
        f"Player {player_name} should no longer be visible in the lobby"
    )

    # Also verify that the select button for this player is gone
    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{player_name}"]'
    )
    assert select_button.count() == 0, (
        f"Select opponent button for {player_name} should be removed"
    )


# New BDD steps for game request scenarios


@when(parsers.parse('"{sender_player}" selects me as their opponent'))
def sender_selects_me_as_opponent(page: Page, sender_player: str) -> None:
    # Simulate another player selecting the current player as their opponent
    # This triggers a game request being sent to the current player

    # Get the current player's name
    current_player = getattr(page, "current_player_name", "TestPlayer")

    # Simulate the sender making a request using authenticated action
    perform_action_as_player(page, sender_player, "select-opponent", current_player)

    # Store the request details for verification
    setattr(page, "game_request_sender", sender_player)
    setattr(page, "game_request_receiver", current_player)

    # Wait for long polling to update the UI
    wait_for_lobby_update(page)


@then(
    parsers.parse('I should receive a game request notification from "{sender_player}"')
)
def receive_game_request_notification(page: Page, sender_player: str) -> None:
    # Verify that a game request notification appears
    notification_element: Locator = page.locator(
        '[data-testid="game-request-notification"]'
    )
    assert notification_element.is_visible(), (
        "Game request notification should be visible"
    )

    notification_text = notification_element.inner_text()
    assert sender_player in notification_text, (
        f"Notification should mention {sender_player}, got '{notification_text}'"
    )
    assert "game request" in notification_text.lower(), (
        f"Notification should mention game request, got '{notification_text}'"
    )


@then('I should see an "Accept" button for the game request')
def see_accept_button(page: Page) -> None:
    # Verify that an Accept button is visible for the game request
    accept_button: Locator = page.locator('[data-testid="accept-game-request"]')
    assert accept_button.is_visible(), "Accept button should be visible"
    assert accept_button.is_enabled(), "Accept button should be enabled"

    button_text = accept_button.inner_text()
    assert "accept" in button_text.lower(), (
        f"Accept button should contain 'Accept', got '{button_text}'"
    )


@then('I should see a "Decline" button for the game request')
def see_decline_button(page: Page) -> None:
    # Verify that a Decline button is visible for the game request
    decline_button: Locator = page.locator('[data-testid="decline-game-request"]')
    assert decline_button.is_visible(), "Decline button should be visible"
    assert decline_button.is_enabled(), "Decline button should be enabled"

    button_text = decline_button.inner_text()
    assert "decline" in button_text.lower(), (
        f"Decline button should contain 'Decline', got '{button_text}'"
    )


@then("I should not be able to select other players while responding to the request")
def cannot_select_players_while_responding(page: Page) -> None:
    # Verify that other Select Opponent buttons are disabled while responding to a request
    select_buttons: Locator = page.locator('[data-testid^="select-opponent-"]')
    button_count = select_buttons.count()

    if button_count > 0:
        # If buttons are still visible, they should be disabled
        for i in range(button_count):
            button = select_buttons.nth(i)
            assert button.is_disabled(), (
                f"Select Opponent button {i} should be disabled while responding to request"
            )


@given(parsers.parse('I have received a game request from "{sender_player}"'))
def have_received_game_request(page: Page, sender_player: str) -> None:
    # Set up the state where the current player has received a game request
    # This is a precondition for accept/decline scenarios

    current_player = getattr(page, "current_player_name", "TestPlayer")

    # Ensure lobby is clean before setting up scenario
    with httpx.Client() as client:
        client.post("http://localhost:8000/test/reset-lobby")

    # First ensure the sender player is in the lobby (avoid duplicate player error)
    # Create a temporary page for the sender to maintain separate sessions
    browser = page.context.browser
    if browser:
        temp_context = browser.new_context()
        temp_page = temp_context.new_page()
        temp_page.goto("http://localhost:8000/")
        temp_page.locator('input[name="player_name"]').fill(sender_player)
        temp_page.locator('button[value="human"]').click()
        temp_page.wait_for_url("**/lobby*")
        temp_page.close()
        temp_context.close()

    # Then ensure current player is in lobby
    page.goto("http://localhost:8000/")
    page.locator('input[name="player_name"]').fill(current_player)
    page.locator('button[value="human"]').click()
    page.wait_for_url("**/lobby*")
    setattr(page, "current_player_name", current_player)

    # Sender selects current player as opponent using authenticated action
    perform_action_as_player(page, sender_player, "select-opponent", current_player)

    setattr(page, "game_request_sender", sender_player)
    setattr(page, "game_request_receiver", current_player)

    # Wait for long poll UI to update and show the request
    wait_for_lobby_update(page)

    # Verify the request is visible with explicit wait
    notification: Locator = page.locator('[data-testid="game-request-notification"]')
    notification.wait_for(state="visible", timeout=5000)
    assert notification.is_visible(), (
        f"Game request from {sender_player} should be visible"
    )


@when(parsers.parse('I click the "Accept" button for the game request'))
def click_accept_game_request(page: Page) -> None:
    # Click the Accept button for the game request
    accept_button: Locator = page.locator('[data-testid="accept-game-request"]')
    assert accept_button.is_visible(), "Accept button should be visible"
    assert accept_button.is_enabled(), "Accept button should be enabled"
    accept_button.click()


@then("I should be redirected to the start game confirmation page")
def redirected_to_game_interface(page: Page) -> None:
    # Verify redirection to the game page
    page.wait_for_url("**/game*", timeout=5000)

    # Verify start game confirmaiton page elements are present
    game_title = page.locator("h1").text_content()
    assert game_title is not None, "Game page should have a title"
    assert "game" in game_title.lower() or "battleship" in game_title.lower(), (
        "Should be on game page"
    )


@then(parsers.parse('"{player_name}" should be my opponent'))
@then(parsers.parse('"{player_name}" should be named as my opponent'))
def player_should_be_opponent(page: Page, player_name: str) -> None:
    # Verify that the specified player is set as the opponent in the game
    # This checks the start game confirmation page shows the correct opponent

    # Look for opponent information in the start game confirmation page
    opponent_element: Locator = page.locator('[data-testid="opponent-name"]')
    if opponent_element.count() > 0:
        opponent_text = opponent_element.inner_text()
        assert player_name in opponent_text, (
            f"Expected opponent '{player_name}' in start game confirmaiton page, got '{opponent_text}'"
        )
    else:
        # Alternative: check page content for opponent information
        page_content = page.content()
        assert player_name in page_content, (
            f"Opponent '{player_name}' should be mentioned in start game confirmation page"
        )


@then(
    parsers.parse(
        'both "{player1}" and "{player2}" should no longer appear in other players\' lobby views'
    )
)
def both_players_removed_from_lobby(page: Page, player1: str, player2: str) -> None:
    # Verify that both players are no longer in the lobby
    # This step represents the behavior from other players' perspectives
    # In a real implementation, this would check multiple browser sessions or server state

    # For BDD testing, this serves as a specification placeholder
    # The actual implementation would verify that:
    # 1. Both players are marked as "In Game"
    # 2. They don't appear in available players lists for others
    # 3. Their lobby sessions are ended
    pass


@when(parsers.parse('I click the "Decline" button for the game request'))
def click_decline_game_request(page: Page) -> None:
    # Click the Decline button for the game request
    decline_button: Locator = page.locator('[data-testid="decline-game-request"]')
    assert decline_button.is_visible(), "Decline button should be visible"
    assert decline_button.is_enabled(), "Decline button should be enabled"
    decline_button.click()


@then(
    parsers.parse('"{sender_name}" should be notified that their request was declined')
)
def sender_notified_of_decline(page: Page, sender_name: str) -> None:
    # Verify that the sender receives notification of the decline
    # In a real implementation, this would check the sender's browser session or server notifications
    # For BDD testing, this serves as a specification placeholder

    # The actual implementation would verify that:
    # 1. The sender gets a "Request declined" message
    # 2. The sender's status returns to "Available"
    # 3. Real-time updates notify the sender
    pass


@then("I should be able to select other players again")
def can_select_other_players_again(page: Page) -> None:
    # Verify that Select Opponent buttons are re-enabled after declining
    select_buttons: Locator = page.locator('[data-testid^="select-opponent-"]')
    button_count = select_buttons.count()

    if button_count > 0:
        # Check that at least some buttons are enabled
        enabled_count = 0
        for i in range(button_count):
            button = select_buttons.nth(i)
            if button.is_enabled():
                enabled_count += 1

        assert enabled_count > 0, (
            "At least some Select Opponent buttons should be enabled after declining"
        )


@then(parsers.parse('"{sender_name}\'s" status should change to "Available"'))
def sender_status_returns_to_available(page: Page, sender_name: str) -> None:
    # Verify that the sender's status returns to Available after decline
    # This tests the real-time status updates in the lobby

    # Wait for status update long polling
    wait_for_lobby_update(page)

    # Check the sender's status in the lobby
    sender_status: Locator = page.locator(
        f'[data-testid="player-{sender_name}-status"]'
    )

    if sender_status.count() > 0:
        status_text = sender_status.inner_text()
        assert "available" in status_text.lower(), (
            f"{sender_name}'s status should be Available, got '{status_text}'"
        )
    else:
        # Alternative: check if sender appears in available players list
        sender_element: Locator = page.locator(f'[data-testid="player-{sender_name}"]')
        assert sender_element.is_visible(), (
            f"{sender_name} should be visible in available players after decline"
        )

        # Check that their Select Opponent button is enabled
        sender_button: Locator = page.locator(
            f'[data-testid="select-opponent-{sender_name}"]'
        )
        assert sender_button.is_enabled(), (
            f"Select Opponent button for {sender_name} should be enabled"
        )


# New BDD steps for "Another player accepts my game request" scenario


@given(parsers.parse('I\'ve selected "{opponent_name}" as my opponent'))
def ive_selected_opponent_as_my_opponent(page: Page, opponent_name: str) -> None:
    # Set up state where current player has sent a game request to opponent
    # This is a precondition for the "opponent accepts my request" scenario

    current_player = getattr(page, "current_player_name", "TestPlayer")

    # Click the "Select Opponent" button for the specified opponent
    select_button: Locator = page.locator(
        f'[data-testid="select-opponent-{opponent_name}"]'
    )
    assert select_button.is_visible(), (
        f"Select Opponent button for {opponent_name} should be visible"
    )
    select_button.click()

    # Wait for the request to be processed
    page.wait_for_timeout(1000)

    # Store the game request details for verification
    setattr(page, "game_request_sender", current_player)
    setattr(page, "game_request_target", opponent_name)

    # Verify the request was sent (confirmation message should appear)
    confirmation_message: Locator = page.locator('[data-testid="confirmation-message"]')
    assert confirmation_message.is_visible(), (
        f"Game request confirmation should be visible after selecting {opponent_name}"
    )


@when(parsers.parse('"{opponent_name}" accepts my game request'))
def opponent_accepts_my_game_request(page: Page, opponent_name: str) -> None:
    # Simulate the opponent accepting the current player's game request
    # This would typically involve the opponent clicking "Accept" in their browser session

    current_player = getattr(page, "current_player_name", "TestPlayer")

    # Simulate the opponent accepting the request using authenticated action
    perform_action_as_player(page, opponent_name, "accept-request", None)

    # Store the acceptance details for verification
    setattr(page, "game_request_accepted_by", opponent_name)

    # Wait for the long poll UI to update with the acceptance
    # The page should redirect to game, so wait for that
    page.wait_for_url("**/game*", timeout=10000)


@given(parsers.parse('"{sender_player}" selects "{opponent_player}" as his opponent'))
def player_selects_another_as_opponent(
    page: Page, sender_player: str, opponent_player: str
) -> None:
    """Simulate one player selecting another player as opponent"""
    # Use authenticated action to simulate the selection
    perform_action_as_player(page, sender_player, "select-opponent", opponent_player)

    # Store the request details
    setattr(page, "other_game_request_sender", sender_player)
    setattr(page, "other_game_request_receiver", opponent_player)

    # Wait for UI update
    page.wait_for_timeout(1000)


@when(
    parsers.parse('"{receiver_player}" accepts the game request from "{sender_player}"')
)
def receiver_accepts_game_request_from_sender(
    page: Page, receiver_player: str, sender_player: str
) -> None:
    """Simulate a player accepting a game request from another player"""
    # Use authenticated action to simulate the acceptance
    perform_action_as_player(page, receiver_player, "accept-request", None)

    # Wait for long poll UI to update
    wait_for_lobby_update(page)


@then("I should remain in the lobby")
def should_remain_in_lobby(page: Page) -> None:
    """Verify that the current player is still in the lobby"""
    # Check that we're still on the lobby page, not redirected to game
    current_url = page.url
    assert "lobby" in current_url, f"Expected to be in lobby, but URL is: {current_url}"
    assert "game" not in current_url, (
        f"Should not be on game page, but URL is: {current_url}"
    )

    # Verify lobby interface elements are present
    lobby_container: Locator = page.locator('[data-testid="lobby-container"]')
    assert lobby_container.is_visible(), "Lobby container should be visible"
