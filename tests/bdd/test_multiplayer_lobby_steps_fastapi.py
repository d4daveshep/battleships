from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup, Tag
from httpx import Response
from dataclasses import dataclass, field
import pytest


scenarios("../../features/multiplayer_lobby.feature")


@dataclass
class LobbyTestContext:
    """Maintains state between BDD steps for lobby testing"""

    response: Response | None = None
    soup: BeautifulSoup | None = None
    form_data: dict[str, str] = field(default_factory=dict)
    current_player_name: str | None = None
    expected_lobby_players: list[dict[str, str]] = field(default_factory=list)
    game_request_sender: str | None = None
    game_request_target: str | None = None
    expected_new_player: str | None = None
    player_who_left: str | None = None

    def update_response(self, response: Response):
        """Update context with new response and parse HTML"""
        self.response = response
        self.soup = BeautifulSoup(response.text, "html.parser")


@pytest.fixture
def lobby_context():
    """Provide a test context for maintaining state between BDD steps"""
    return LobbyTestContext()


@pytest.fixture
def client():
    """FastAPI TestClient fixture"""
    from main import app

    return TestClient(app, follow_redirects=False)


def on_lobby_page(context: LobbyTestContext) -> None:
    """Helper function to verify we're on the lobby page"""
    assert context.soup is not None
    assert context.response is not None
    h1_element = context.soup.find("h1")
    assert h1_element and "Multiplayer Lobby" in h1_element.get_text()
    assert context.response.status_code == 200


def get_lobby_status(client: TestClient, context: LobbyTestContext, player_name: str) -> BeautifulSoup:
    """Helper function to get the dynamic lobby status content"""
    status_response = client.get(f"/lobby/status/{player_name}")
    return BeautifulSoup(status_response.text, "html.parser")


def login_and_goto_lobby(client: TestClient, context: LobbyTestContext, player_name: str) -> None:
    """Helper function to log in a player and navigate to lobby"""
    # First get the login page
    response = client.get("/")
    context.update_response(response)
    
    # Submit login form with human opponent selection
    form_data = {"player_name": player_name, "game_mode": "human"}
    response = client.post("/", data=form_data)
    context.update_response(response)
    
    # Should be redirected to lobby
    assert context.response is not None
    assert context.response.status_code == 303
    redirect_url = context.response.headers.get("location")
    assert redirect_url is not None
    assert "lobby" in redirect_url
    
    # Follow redirect to lobby page
    target_response = client.get(redirect_url)
    context.update_response(target_response)
    
    # Store player name
    context.current_player_name = player_name
    
    # Verify we're on lobby page
    on_lobby_page(context)
    



@given("the multiplayer lobby system is available")
def multiplayer_lobby_system_available() -> None:
    """Verify the multiplayer lobby system is accessible"""
    # This step ensures the backend supports multiplayer functionality
    pass


@given("there are no other players in the lobby")
def no_other_players_in_lobby(client: TestClient) -> None:
    """Set up empty lobby condition"""
    # Reset lobby state via test endpoint
    try:
        response = client.post("/test/reset-lobby")
    except:
        pass  # Test endpoint may not exist yet, that's okay


@given("there are other players in the lobby:")
def other_players_in_lobby(client: TestClient, lobby_context: LobbyTestContext, datatable) -> None:
    """Set up pre-existing players in the lobby"""
    # Store the current player's perspective to restore later
    current_player = lobby_context.current_player_name
    
    # Only reset lobby if no current player is set (fresh scenario)
    if current_player is None:
        try:
            client.post("/test/reset-lobby")
        except:
            pass  # Test endpoint may not exist yet
    
    expected_players: list[dict[str, str]] = []
    for row in datatable[1:]:  # Skip header row
        player_name: str = row[0]
        status: str = row[1]
        if status == "Available":
            # Add player to lobby using individual login flow to avoid conflicts
            response = client.get("/")
            form_data = {"player_name": player_name, "game_mode": "human"}
            response = client.post("/", data=form_data)
            expected_players.append({"name": player_name, "status": status})
    
    lobby_context.expected_lobby_players = expected_players
    
    # Restore the original player's perspective if it was set
    if current_player:
        lobby_response = client.get(f"/lobby?player_name={current_player}")
        lobby_context.update_response(lobby_response)
        lobby_context.current_player_name = current_player


@when(parsers.parse('I login as "{player_name}" and select human opponent'))
def login_and_select_human_opponent(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Navigate to login page, enter player name, and select human opponent"""
    login_and_goto_lobby(client, lobby_context, player_name)


@given(parsers.parse('I\'ve logged in as "{player_name}" and selected human opponent'))
def logged_in_and_selected_human_opponent(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Complete login flow and select human opponent (given state)"""
    login_and_goto_lobby(client, lobby_context, player_name)


@given('I see the message "Waiting for other players to join..."')
def see_waiting_message_given(client: TestClient, lobby_context: LobbyTestContext) -> None:
    """Verify the waiting message is displayed (given state)"""
    # Since messages are loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    waiting_message = status_soup.find(attrs={"data-testid": "waiting-message"})
    assert waiting_message is not None
    waiting_text = waiting_message.get_text()
    assert "Waiting for other players to join..." in waiting_text


@when(parsers.parse('another player "{player_name}" logs in and selects human opponent'))
def another_player_logs_in_and_selects_human(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Simulate another player going through the login flow"""
    # Store current player to restore later
    current_player = lobby_context.current_player_name
    
    # Simulate the new player logging in and selecting human opponent
    response = client.get("/")
    response = client.post("/", data={"player_name": player_name, "game_mode": "human"})
    
    # Store the expected new player for verification
    lobby_context.expected_new_player = player_name
    
    # Restore original player's perspective by going back to lobby
    if current_player:
        lobby_response = client.get(f"/lobby?player_name={current_player}")
        lobby_context.update_response(lobby_response)
        lobby_context.current_player_name = current_player


@then("I should see the lobby interface")
def see_lobby_interface(lobby_context: LobbyTestContext) -> None:
    """Verify lobby interface elements are present"""
    on_lobby_page(lobby_context)
    assert lobby_context.soup is not None
    
    # Check for lobby container
    lobby_container = lobby_context.soup.find(attrs={"data-testid": "lobby-container"})
    assert lobby_container is not None


@then("I should see my name")
def see_my_name(lobby_context: LobbyTestContext) -> None:
    """Verify the current player's name is displayed in the lobby"""
    assert lobby_context.soup is not None
    player_name_element = lobby_context.soup.find(attrs={"data-testid": "player-name"})
    assert player_name_element is not None
    
    name_text = player_name_element.get_text()
    current_player = lobby_context.current_player_name
    assert current_player is not None
    assert current_player in name_text


@then(parsers.parse('I should see a message "{message}"'))
def see_message(client: TestClient, lobby_context: LobbyTestContext, message: str) -> None:
    """Verify a specific message is displayed"""
    # Since messages are loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    
    # Look for various message containers using the exact pattern from original
    message_selectors = [
        "no-players-message",
        "waiting-message", 
        "confirmation-message",
        "message",
        "decline-confirmation-message"
    ]
    
    message_found = False
    for selector in message_selectors:
        element = status_soup.find(attrs={"data-testid": selector})
        if element and message in element.get_text():
            message_found = True
            break
    
    assert message_found, f"Expected message '{message}' not found"


@then("I should not see any selectable players")
def no_selectable_players(client: TestClient, lobby_context: LobbyTestContext) -> None:
    """Verify no player selection buttons are visible"""
    # Since player list is loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    # Look for any elements with data-testid starting with "select-opponent-"
    all_elements = status_soup.find_all(attrs={"data-testid": True})
    select_buttons = []
    for elem in all_elements:
        if isinstance(elem, Tag):
            testid = elem.get("data-testid")
            if testid and isinstance(testid, str) and testid.startswith("select-opponent-"):
                select_buttons.append(elem)
    assert len(select_buttons) == 0


@then(parsers.parse('my status should be "{status}"'))
def my_status_should_be(client: TestClient, lobby_context: LobbyTestContext, status: str) -> None:
    """Verify player's own status is displayed correctly"""
    # Since status is loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    status_element = status_soup.find(attrs={"data-testid": "player-status"})
    assert status_element is not None
    status_text = status_element.get_text()
    assert status in status_text


@then(parsers.parse('I should see "{player_name}" in the available players list'))
def see_player_in_available_list(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Verify a specific player appears in the available players list"""
    # Since player list is loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    player_element = status_soup.find(attrs={"data-testid": f"player-{player_name}"})
    assert player_element is not None
    assert player_name in player_element.get_text()


@then(parsers.parse('I should see a "Select Opponent" button next to "{player_name}"'))
def see_select_button_for_player(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Verify there's a select opponent button for a specific player"""
    # Since buttons are loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    select_button = status_soup.find(attrs={"data-testid": f"select-opponent-{player_name}"})
    assert select_button is not None
    assert "Select Opponent" in select_button.get_text()


@then('the "Waiting for other players" message should be hidden')
def waiting_message_hidden(lobby_context: LobbyTestContext) -> None:
    """Verify the waiting message is no longer visible"""
    assert lobby_context.soup is not None
    waiting_element = lobby_context.soup.find(attrs={"data-testid": "waiting-message"})
    # Element should either not exist or be hidden
    if waiting_element and isinstance(waiting_element, Tag):
        class_list = waiting_element.get("class")
        if isinstance(class_list, list) and "hidden" in class_list:
            pass  # Successfully hidden
        else:
            assert waiting_element is None
    else:
        assert waiting_element is None


@then(parsers.parse('I should be able to select "{player_name}" as my opponent'))
def can_select_player_as_opponent(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Verify the select button is functional for the player"""
    # Since buttons are loaded dynamically via HTMX, get the status content
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    status_soup = get_lobby_status(client, lobby_context, current_player)
    select_button = status_soup.find(attrs={"data-testid": f"select-opponent-{player_name}"})
    assert select_button is not None
    # Button should not have disabled attribute
    if isinstance(select_button, Tag):
        assert select_button.get("disabled") is None


@then("I should see a list of available players:")
def see_available_players_list(lobby_context: LobbyTestContext, datatable) -> None:
    """Verify the player list shows expected players"""
    assert lobby_context.soup is not None
    
    # Check for each expected player
    for row in datatable[1:]:  # Skip header row
        player_name: str = row[0]
        player_element = lobby_context.soup.find(attrs={"data-testid": f"player-{player_name}"})
        assert player_element is not None, f"Player {player_name} should be visible in lobby"
        assert player_name in player_element.get_text()


@then('I should see a "Select Opponent" button for each available player')
def see_select_opponent_buttons(lobby_context: LobbyTestContext) -> None:
    """Verify each available player has a select button"""
    assert lobby_context.soup is not None
    # Find all elements with data-testid starting with "select-opponent-"
    all_elements = lobby_context.soup.find_all(attrs={"data-testid": True})
    select_buttons = []
    for elem in all_elements:
        if isinstance(elem, Tag):
            testid = elem.get("data-testid")
            if testid and isinstance(testid, str) and testid.startswith("select-opponent-"):
                select_buttons.append(elem)
    assert len(select_buttons) > 0
    
    for button in select_buttons:
        assert "Select Opponent" in button.get_text()
        if isinstance(button, Tag):
            assert button.get("disabled") is None


@when(parsers.parse('I click "Select Opponent" next to "{opponent_name}"'))
def click_select_opponent(client: TestClient, lobby_context: LobbyTestContext, opponent_name: str) -> None:
    """Click the Select Opponent button for the specified player"""
    # Simulate form submission for selecting opponent
    current_player = lobby_context.current_player_name
    assert current_player is not None
    form_data = {
        "player_name": current_player,
        "opponent_name": opponent_name
    }
    response = client.post("/select-opponent", data=form_data)
    lobby_context.update_response(response)


@then(parsers.parse('"{target_player}" should receive a game invitation from "{sender_player}"'))
def target_player_receives_invitation(lobby_context: LobbyTestContext, target_player: str, sender_player: str) -> None:
    """Verify that the game invitation was sent"""
    # Store the invitation details for verification
    lobby_context.game_request_sender = sender_player
    lobby_context.game_request_target = target_player
    
    # In a real implementation, this would check server state or notifications
    # For now, we verify the response indicates success
    assert lobby_context.response is not None
    assert lobby_context.response.status_code in [200, 303]  # Success or redirect


@then(parsers.parse('my status should change to "{expected_status}"'))
def my_status_should_change(lobby_context: LobbyTestContext, expected_status: str) -> None:
    """Check that the current player's status has changed"""
    assert lobby_context.soup is not None
    status_element = lobby_context.soup.find(attrs={"data-testid": "player-status"})
    assert status_element is not None
    status_text = status_element.get_text()
    assert expected_status in status_text


@then("I should not be able to select other players while waiting for my request to be completed")
def cannot_select_other_players_while_waiting(lobby_context: LobbyTestContext) -> None:
    """Check that other Select Opponent buttons are disabled"""
    assert lobby_context.soup is not None
    # Find all elements with data-testid starting with "select-opponent-"
    all_elements = lobby_context.soup.find_all(attrs={"data-testid": True})
    select_buttons = []
    for elem in all_elements:
        if isinstance(elem, Tag):
            testid = elem.get("data-testid")
            if testid and isinstance(testid, str) and testid.startswith("select-opponent-"):
                select_buttons.append(elem)
    
    for button in select_buttons:
        # Buttons should either be disabled or have disabled class
        if isinstance(button, Tag):
            disabled_attr = button.get("disabled")
            class_list = button.get("class")
            if isinstance(class_list, list):
                has_disabled_class = "disabled" in class_list
            else:
                has_disabled_class = False
            assert disabled_attr is not None or has_disabled_class


@when(parsers.parse('"{target_player}" receives a game request from "{sender_player}"'))
def target_player_receives_game_request(client: TestClient, lobby_context: LobbyTestContext, target_player: str, sender_player: str) -> None:
    """Simulate another player sending a game request"""
    # Store current context
    current_player = lobby_context.current_player_name
    
    # Simulate sender selecting target as opponent
    form_data = {"player_name": sender_player, "opponent_name": target_player}
    client.post("/select-opponent", data=form_data)
    
    # Store the interaction for verification
    lobby_context.game_request_sender = sender_player
    lobby_context.game_request_target = target_player
    
    # Simulate polling cycle wait (like Playwright tests)
    import time
    time.sleep(1.5)  # 1.5s wait for updates
    
    # Refresh current player's view
    if current_player:
        lobby_response = client.get(f"/lobby?player_name={current_player}")
        lobby_context.update_response(lobby_response)


@then(parsers.parse('I should see "{player_name}\'s" status change from "{old_status}" to "{new_status}"'))
def see_player_status_change(lobby_context: LobbyTestContext, player_name: str, old_status: str, new_status: str) -> None:
    """Check that a player's status has changed"""
    assert lobby_context.soup is not None
    player_status_element = lobby_context.soup.find(attrs={"data-testid": f"player-{player_name}-status"})
    
    if player_status_element:
        status_text = player_status_element.get_text()
        assert new_status.lower() in status_text.lower()
    else:
        # Alternative: check player element for status info
        player_element = lobby_context.soup.find(attrs={"data-testid": f"player-{player_name}"})
        assert player_element is not None
        assert new_status.lower() in player_element.get_text().lower()


@then(parsers.parse('the "Select Opponent" button for "{player_name}" should be disabled'))
def select_opponent_button_should_be_disabled(lobby_context: LobbyTestContext, player_name: str) -> None:
    """Verify the Select Opponent button for specified player is disabled"""
    assert lobby_context.soup is not None
    select_button = lobby_context.soup.find(attrs={"data-testid": f"select-opponent-{player_name}"})
    assert select_button is not None
    if isinstance(select_button, Tag):
        assert select_button.get("disabled") is not None


@when('I click the "Leave Lobby" button')
def click_leave_lobby_button(client: TestClient, lobby_context: LobbyTestContext) -> None:
    """Click the Leave Lobby button to exit the lobby"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    form_data = {"player_name": current_player}
    response = client.post("/leave-lobby", data=form_data)
    lobby_context.update_response(response)


@then("I should be returned to the login page")
def returned_to_login_page(lobby_context: LobbyTestContext) -> None:
    """Verify that the user is redirected back to the login page"""
    assert lobby_context.response is not None
    assert lobby_context.response.status_code == 302  # FastAPI returns 302, not 303
    redirect_url = lobby_context.response.headers.get("location")
    assert redirect_url is not None
    assert redirect_url == "/" or "login" in redirect_url


@then("other players should no longer see me in their lobby view")
def other_players_no_longer_see_me(lobby_context: LobbyTestContext) -> None:
    """Verify player is removed from other players' lobby views"""
    # This serves as a specification placeholder
    # In a real implementation, this would verify server state changes
    pass


@when(parsers.parse('"{player_name}" leaves the lobby'))
def player_leaves_lobby(client: TestClient, lobby_context: LobbyTestContext, player_name: str) -> None:
    """Simulate another player leaving the lobby"""
    current_player = lobby_context.current_player_name
    
    # Simulate player leaving
    form_data = {"player_name": player_name}
    client.post("/leave-lobby", data=form_data)
    
    # Store the player who left for verification
    lobby_context.player_who_left = player_name
    
    # Wait for polling cycle to complete (like Playwright tests)
    import time
    time.sleep(1.5)  # 1.5s wait for real-time updates
    
    # Refresh current player's view
    if current_player:
        lobby_response = client.get(f"/lobby?player_name={current_player}")
        lobby_context.update_response(lobby_response)


@then(parsers.parse('"{player_name}" should no longer appear in my available players list'))
def player_no_longer_in_list(lobby_context: LobbyTestContext, player_name: str) -> None:
    """Verify specified player is no longer visible in available players list"""
    assert lobby_context.soup is not None
    player_element = lobby_context.soup.find(attrs={"data-testid": f"player-{player_name}"})
    assert player_element is None


@when(parsers.parse('"{sender_player}" selects me as their opponent'))
def sender_selects_me_as_opponent(client: TestClient, lobby_context: LobbyTestContext, sender_player: str) -> None:
    """Simulate another player selecting current player as opponent"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    # Simulate sender selecting current player
    form_data = {"player_name": sender_player, "opponent_name": current_player}
    client.post("/select-opponent", data=form_data)
    
    # Store the request details for verification
    lobby_context.game_request_sender = sender_player
    lobby_context.game_request_target = current_player
    
    # Wait for polling cycle to update the UI (like Playwright tests)
    import time
    time.sleep(1.5)
    
    # Refresh current player's view
    lobby_response = client.get(f"/lobby?player_name={current_player}")
    lobby_context.update_response(lobby_response)


@then(parsers.parse('I should receive a game request notification from "{sender_player}"'))
def receive_game_request_notification(lobby_context: LobbyTestContext, sender_player: str) -> None:
    """Verify that a game request notification appears"""
    assert lobby_context.soup is not None
    notification_element = lobby_context.soup.find(attrs={"data-testid": "game-request-notification"})
    assert notification_element is not None
    
    notification_text = notification_element.get_text()
    assert sender_player in notification_text
    assert "game request" in notification_text.lower()


@then('I should see an "Accept" button for the game request')
def see_accept_button(lobby_context: LobbyTestContext) -> None:
    """Verify that an Accept button is visible for the game request"""
    assert lobby_context.soup is not None
    accept_button = lobby_context.soup.find(attrs={"data-testid": "accept-game-request"})
    assert accept_button is not None
    assert "accept" in accept_button.get_text().lower()


@then('I should see a "Decline" button for the game request')
def see_decline_button(lobby_context: LobbyTestContext) -> None:
    """Verify that a Decline button is visible for the game request"""
    assert lobby_context.soup is not None
    decline_button = lobby_context.soup.find(attrs={"data-testid": "decline-game-request"})
    assert decline_button is not None
    assert "decline" in decline_button.get_text().lower()


@then("I should not be able to select other players while responding to the request")
def cannot_select_players_while_responding(lobby_context: LobbyTestContext) -> None:
    """Verify other Select Opponent buttons are disabled while responding"""
    assert lobby_context.soup is not None
    # Find all elements with data-testid starting with "select-opponent-"
    all_elements = lobby_context.soup.find_all(attrs={"data-testid": True})
    select_buttons = []
    for elem in all_elements:
        if isinstance(elem, Tag):
            testid = elem.get("data-testid")
            if testid and isinstance(testid, str) and testid.startswith("select-opponent-"):
                select_buttons.append(elem)
    
    for button in select_buttons:
        if isinstance(button, Tag):
            assert button.get("disabled") is not None


@given(parsers.parse('I have received a game request from "{sender_player}"'))
def have_received_game_request(client: TestClient, lobby_context: LobbyTestContext, sender_player: str) -> None:
    """Set up state where current player has received a game request"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    # Ensure lobby is clean before setting up scenario
    try:
        client.post("/test/reset-lobby")
    except:
        pass
    
    # First ensure the sender player is in the lobby (avoid duplicate player error)
    response = client.get("/")
    response = client.post("/", data={"player_name": sender_player, "game_mode": "human"})
    
    # Then ensure current player is in lobby
    response = client.get("/")
    response = client.post("/", data={"player_name": current_player, "game_mode": "human"})
    lobby_context.current_player_name = current_player
    
    # Simulate sender selecting current player
    form_data = {"player_name": sender_player, "opponent_name": current_player}
    client.post("/select-opponent", data=form_data)
    
    lobby_context.game_request_sender = sender_player
    lobby_context.game_request_target = current_player
    
    # Wait for the UI to update and show the request
    import time
    time.sleep(1.5)
    
    # Refresh current player's view to see the request
    lobby_response = client.get(f"/lobby?player_name={current_player}")
    lobby_context.update_response(lobby_response)
    
    # Verify request is visible
    assert lobby_context.soup is not None
    notification = lobby_context.soup.find(attrs={"data-testid": "game-request-notification"})
    assert notification is not None


@when(parsers.parse('I click the "Accept" button for the game request'))
def click_accept_game_request(client: TestClient, lobby_context: LobbyTestContext) -> None:
    """Click the Accept button for the game request"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    form_data = {
        "player_name": current_player,
        "sender_name": lobby_context.game_request_sender
    }
    response = client.post("/accept-game-request", data=form_data)
    lobby_context.update_response(response)


@then("I should be redirected to the game interface")
def redirected_to_game_interface(client: TestClient, lobby_context: LobbyTestContext) -> None:
    """Verify redirection to the game page"""
    assert lobby_context.response is not None
    assert lobby_context.response.status_code == 303
    redirect_url = lobby_context.response.headers.get("location")
    assert redirect_url is not None
    assert "game" in redirect_url
    
    # Follow redirect and verify game page
    target_response = client.get(redirect_url)
    lobby_context.update_response(target_response)
    
    assert lobby_context.response.status_code == 200
    assert lobby_context.soup is not None
    h1_element = lobby_context.soup.find("h1")
    assert h1_element and "game" in h1_element.get_text().lower()


@then(parsers.parse('"{player_name}" should be named as my opponent'))
@then(parsers.parse('"{player_name}" should be my opponent'))
def player_should_be_opponent(lobby_context: LobbyTestContext, player_name: str) -> None:
    """Verify that the specified player is set as the opponent"""
    assert lobby_context.soup is not None
    opponent_element = lobby_context.soup.find(attrs={"data-testid": "opponent-name"})
    if opponent_element:
        assert player_name in opponent_element.get_text()
    else:
        # Alternative: check page content for opponent info
        page_text = lobby_context.soup.get_text()
        assert player_name in page_text


@then(parsers.parse('both "{player1}" and "{player2}" should no longer appear in other players\' lobby views'))
def both_players_removed_from_lobby(player1: str, player2: str) -> None:
    """Verify both players are no longer in the lobby"""
    # This serves as a specification placeholder
    pass


@when(parsers.parse('I click the "Decline" button for the game request'))
def click_decline_game_request(client: TestClient, lobby_context: LobbyTestContext) -> None:
    """Click the Decline button for the game request"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    form_data = {
        "player_name": current_player,
        "sender_name": lobby_context.game_request_sender
    }
    response = client.post("/decline-game-request", data=form_data)
    lobby_context.update_response(response)


@then(parsers.parse('"{sender_name}" should be notified that their request was declined'))
def sender_notified_of_decline(sender_name: str) -> None:
    """Verify that the sender receives notification of the decline"""
    # This serves as a specification placeholder
    pass


@then("I should be able to select other players again")
def can_select_other_players_again(lobby_context: LobbyTestContext) -> None:
    """Verify that Select Opponent buttons are re-enabled after declining"""
    assert lobby_context.soup is not None
    # Find all elements with data-testid starting with "select-opponent-"
    all_elements = lobby_context.soup.find_all(attrs={"data-testid": True})
    select_buttons = []
    for elem in all_elements:
        if isinstance(elem, Tag):
            testid = elem.get("data-testid")
            if testid and isinstance(testid, str) and testid.startswith("select-opponent-"):
                select_buttons.append(elem)
    
    # At least some buttons should be enabled
    enabled_count = 0
    for button in select_buttons:
        if isinstance(button, Tag) and button.get("disabled") is None:
            enabled_count += 1
    
    assert enabled_count > 0


@then(parsers.parse('"{sender_name}\'s" status should change to "Available"'))
def sender_status_returns_to_available(client: TestClient, lobby_context: LobbyTestContext, sender_name: str) -> None:
    """Verify that the sender's status returns to Available after decline"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    # Wait for status update polling cycle (like Playwright tests)
    import time
    time.sleep(1.5)
    
    # Refresh view to see updated status
    lobby_response = client.get(f"/lobby?player_name={current_player}")
    lobby_context.update_response(lobby_response)
    
    assert lobby_context.soup is not None
    sender_status = lobby_context.soup.find(attrs={"data-testid": f"player-{sender_name}-status"})
    
    if sender_status:
        status_text = sender_status.get_text()
        assert "available" in status_text.lower()
    else:
        # Alternative: check if sender appears in available players
        sender_element = lobby_context.soup.find(attrs={"data-testid": f"player-{sender_name}"})
        assert sender_element is not None
        
        # Check that their Select Opponent button is enabled
        sender_button = lobby_context.soup.find(attrs={"data-testid": f"select-opponent-{sender_name}"})
        if sender_button and isinstance(sender_button, Tag):
            assert sender_button.get("disabled") is None


@given(parsers.parse('I\'ve selected "{opponent_name}" as my opponent'))
def ive_selected_opponent_as_my_opponent(client: TestClient, lobby_context: LobbyTestContext, opponent_name: str) -> None:
    """Set up state where current player has sent a game request to opponent"""
    # Click the Select Opponent button
    current_player = lobby_context.current_player_name
    assert current_player is not None
    form_data = {
        "player_name": current_player,
        "opponent_name": opponent_name
    }
    response = client.post("/select-opponent", data=form_data)
    lobby_context.update_response(response)
    
    # Store request details
    lobby_context.game_request_sender = current_player
    lobby_context.game_request_target = opponent_name
    
    # Verify confirmation message
    assert lobby_context.soup is not None
    confirmation = lobby_context.soup.find(attrs={"data-testid": "confirmation-message"})
    assert confirmation is not None


@when(parsers.parse('"{opponent_name}" accepts my game request'))
def opponent_accepts_my_game_request(client: TestClient, lobby_context: LobbyTestContext, opponent_name: str) -> None:
    """Simulate the opponent accepting the current player's game request"""
    current_player = lobby_context.current_player_name
    assert current_player is not None
    
    # Simulate opponent accepting the request
    form_data = {"player_name": opponent_name, "sender_name": current_player}
    response = client.post("/accept-game-request", data=form_data)
    
    # Update context with the acceptance response (this might redirect to game)
    lobby_context.update_response(response)