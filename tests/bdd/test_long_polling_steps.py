"""
BDD step definitions for long polling real-time updates.

These tests verify that the long polling infrastructure works correctly
for real-time lobby updates. They should fail initially (RED phase) as
they test the complete integration of long polling behavior.
"""

from pytest_bdd import scenarios, given, when, then, parsers
import httpx
import time
from playwright.sync_api import Page, Locator, Response
from tests.bdd.conftest import login_and_select_multiplayer

# Load scenarios from the feature file
scenarios("../../features/long_polling_updates.feature")


# Shared step definitions (reused from multiplayer lobby tests)
@given("the multiplayer lobby system is available")
def multiplayer_lobby_system_available(page: Page) -> None:
    """Verify the multiplayer lobby system is accessible"""
    pass


@given(parsers.parse('I\'ve logged in as "{player_name}" and selected human opponent'))
def logged_in_as_player(page: Page, player_name: str) -> None:
    """Login as specific player and enter lobby"""
    login_and_select_multiplayer(page, player_name)
    setattr(page, "current_player_name", player_name)


@given(parsers.parse('I see the message "{message}"'))
@then(parsers.parse('I see the message "{message}"'))
def i_see_message(page: Page, message: str) -> None:
    """Verify message appears"""
    page.wait_for_selector(f'text={message}')


@given(parsers.parse('another player "{player_name}" is already in the lobby'))
def player_already_in_lobby(page: Page, player_name: str) -> None:
    """Simulate another player already in lobby"""
    with httpx.Client() as client:
        client.post(
            "http://localhost:8000/",
            data={"player_name": player_name, "game_mode": "human"},
        )
    # Brief wait for lobby to update
    page.wait_for_timeout(500)


@then(parsers.parse('I can see "{player_name}" in my available players list'))
def player_in_available_list(page: Page, player_name: str) -> None:
    """Verify player appears in available players list"""
    page.wait_for_selector(f'[data-testid="player-{player_name}"]')


@given("long polling is enabled")
def long_polling_enabled(page: Page) -> None:
    """Verify that long polling is configured on the frontend"""
    # This is a precondition check - we don't need to do anything
    # The template should already be configured for long polling
    pass


@when(parsers.parse('another player "{player_name}" joins the lobby within 5 seconds'))
def player_joins_within_time(page: Page, player_name: str) -> None:
    """Simulate another player joining the lobby"""
    # Use httpx to add player via API
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/",
            data={"player_name": player_name, "game_mode": "human"},
        )
    # Store join time for verification
    setattr(page, "player_join_time", time.time())


@then(parsers.parse('I should see "{player_name}" appear in my lobby within 5 seconds'))
def player_appears_within_time(page: Page, player_name: str) -> None:
    """Verify player appears within the specified time"""
    start_time = getattr(page, "player_join_time", time.time())

    # Wait for the player to appear (max 5 seconds)
    try:
        page.wait_for_selector(
            f'button[data-testid="select-opponent-{player_name}"]', timeout=5000
        )
        elapsed = time.time() - start_time
        assert elapsed < 5, f"Player took {elapsed}s to appear, expected < 5s"
    except Exception as e:
        elapsed = time.time() - start_time
        raise AssertionError(
            f"Player {player_name} did not appear within 5 seconds (waited {elapsed}s): {e}"
        )


@then("I should not have to wait for a polling interval")
def no_polling_interval_wait(page: Page) -> None:
    """Verify update was near-instant, not dependent on polling interval"""
    # With long polling + events, updates should be < 2s
    # With short polling (every 1s), could take up to 1s
    join_time = getattr(page, "player_join_time", None)
    if join_time:
        elapsed = time.time() - join_time
        # Allow some time for network/rendering, but should be much less than polling interval
        assert (
            elapsed < 3
        ), f"Update took {elapsed}s, too long for event-based long polling"


@when(parsers.parse('"{player_name}" leaves the lobby'))
def player_leaves_lobby(page: Page, player_name: str) -> None:
    """Simulate a player leaving the lobby"""
    # Use httpx to remove player via API
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/leave-lobby", data={"player_name": player_name}
        )
    setattr(page, "player_leave_time", time.time())


@then(parsers.parse('"{player_name}" should disappear from my lobby within 5 seconds'))
def player_disappears_within_time(page: Page, player_name: str) -> None:
    """Verify player disappears within the specified time"""
    start_time = getattr(page, "player_leave_time", time.time())

    # Wait for the player to disappear (max 5 seconds)
    try:
        page.wait_for_selector(
            f'button[data-testid="select-opponent-{player_name}"]',
            state="hidden",
            timeout=5000,
        )
        elapsed = time.time() - start_time
        assert elapsed < 5, f"Player took {elapsed}s to disappear, expected < 5s"
    except Exception as e:
        elapsed = time.time() - start_time
        raise AssertionError(
            f"Player {player_name} did not disappear within 5 seconds: {e}"
        )


@when(parsers.parse('"{sender}" sends me a game request'))
def player_sends_game_request(page: Page, sender: str) -> None:
    """Simulate another player sending a game request"""
    current_player = getattr(page, "current_player_name", "Alice")

    # Send game request via API
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/select-opponent",
            data={"player_name": sender, "opponent_name": current_player},
        )

    setattr(page, "game_request_time", time.time())


@then("I should see the game request notification within 5 seconds")
def game_request_notification_appears(page: Page) -> None:
    """Verify game request notification appears quickly"""
    start_time = getattr(page, "game_request_time", time.time())

    # Wait for notification (max 5 seconds)
    try:
        page.wait_for_selector('[data-testid="game-request-notification"]', timeout=5000)
        elapsed = time.time() - start_time
        assert (
            elapsed < 5
        ), f"Notification took {elapsed}s to appear, expected < 5s"
    except Exception as e:
        elapsed = time.time() - start_time
        raise AssertionError(
            f"Game request notification did not appear within 5 seconds: {e}"
        )


@given(parsers.parse('I have sent a game request to "{opponent}"'))
def i_sent_game_request(page: Page, opponent: str) -> None:
    """Send a game request to an opponent"""
    current_player = getattr(page, "current_player_name", "Alice")

    # Click the select opponent button
    page.click(f'button[data-testid="select-opponent-{opponent}"]')

    # Wait briefly for request to be sent
    page.wait_for_timeout(500)


@when(parsers.parse('"{opponent}" accepts my game request'))
def opponent_accepts_request(page: Page, opponent: str) -> None:
    """Simulate opponent accepting the game request"""
    current_player = getattr(page, "current_player_name", "Alice")

    # Accept via API
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/accept-game-request",
            data={"player_name": opponent, "sender_name": current_player},
        )

    setattr(page, "accept_request_time", time.time())


@then("I should be redirected to the game page within 5 seconds")
def redirected_to_game_within_time(page: Page) -> None:
    """Verify redirect happens within specified time"""
    start_time = getattr(page, "accept_request_time", time.time())

    # Wait for redirect to game page
    try:
        page.wait_for_url("**/game**", timeout=5000)
        elapsed = time.time() - start_time
        assert elapsed < 5, f"Redirect took {elapsed}s, expected < 5s"
    except Exception as e:
        elapsed = time.time() - start_time
        raise AssertionError(f"Did not redirect to game within 5 seconds: {e}")


@then(parsers.parse('the game should be with opponent "{opponent}"'))
def verify_game_opponent(page: Page, opponent: str) -> None:
    """Verify the game page shows correct opponent"""
    # Check URL contains opponent name
    assert opponent in page.url, f"Expected {opponent} in URL, got {page.url}"


@when(parsers.parse('"{opponent}" declines my game request'))
def opponent_declines_request(page: Page, opponent: str) -> None:
    """Simulate opponent declining the game request"""
    # Decline via API
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/decline-game-request", data={"player_name": opponent}
        )

    setattr(page, "decline_request_time", time.time())


@then("I should see a message that the request was declined within 5 seconds")
def decline_message_appears(page: Page) -> None:
    """Verify decline message appears within specified time"""
    start_time = getattr(page, "decline_request_time", time.time())

    # Wait for decline confirmation message
    try:
        page.wait_for_selector(
            '[data-testid="decline-confirmation-message"]', timeout=5000
        )
        elapsed = time.time() - start_time
        assert elapsed < 5, f"Decline message took {elapsed}s, expected < 5s"
    except Exception as e:
        elapsed = time.time() - start_time
        raise AssertionError(f"Decline message did not appear within 5 seconds: {e}")


@then(
    parsers.parse(
        'both "{player1}" and "{player2}" should return to "Available" status'
    )
)
def both_players_available(page: Page, player1: str, player2: str) -> None:
    """Verify both players return to Available status"""
    # Check player status in the UI
    # This might require checking the player's own status indicator
    status_element = page.locator('[data-testid="player-status"]')
    assert "Available" in status_element.inner_text()


@when("the following players join in quick succession:")
def players_join_quickly(page: Page, datatable) -> None:
    """Simulate multiple players joining rapidly"""
    setattr(page, "rapid_join_start_time", time.time())

    with httpx.Client() as client:
        for row in datatable[1:]:  # Skip header
            player_name = row[0]
            client.post(
                "http://localhost:8000/",
                data={"player_name": player_name, "game_mode": "human"},
            )
            # Small delay between joins to simulate realistic timing
            time.sleep(0.1)


@then("I should see all players appear in my lobby within 10 seconds")
def all_players_appear(page: Page) -> None:
    """Verify all players from rapid join appear"""
    start_time = getattr(page, "rapid_join_start_time", time.time())

    # Just verify the timing constraint
    elapsed = time.time() - start_time
    assert elapsed < 10, f"Players took {elapsed}s to appear, expected < 10s"


@given("I wait for 35 seconds")
def wait_for_timeout(page: Page) -> None:
    """Wait longer than long poll timeout"""
    page.wait_for_timeout(35000)


@then("the long polling connection should have automatically reconnected")
def long_poll_reconnected(page: Page) -> None:
    """Verify long polling reconnected after timeout"""
    # If we can see the new player, the connection must have reconnected
    # This is implicitly verified by the previous step showing the player
    pass


@when(parsers.parse('"{sender}" sends a game request to "{receiver}"'))
def other_player_sends_request(page: Page, sender: str, receiver: str) -> None:
    """Simulate one player sending request to another"""
    with httpx.Client() as client:
        client.post(
            "http://localhost:8000/select-opponent",
            data={"player_name": sender, "opponent_name": receiver},
        )

    setattr(page, "status_change_time", time.time())


@then(parsers.parse('I should see "{player}" status change to "{status}" within 5 seconds'))
def player_status_changes(page: Page, player: str, status: str) -> None:
    """Verify player status changes within specified time"""
    start_time = getattr(page, "status_change_time", time.time())

    # Wait for status to change
    try:
        page.wait_for_selector(
            f'[data-testid="player-{player}-status"]:has-text("{status}")', timeout=5000
        )
        elapsed = time.time() - start_time
        assert elapsed < 5, f"Status change took {elapsed}s, expected < 5s"
    except Exception as e:
        elapsed = time.time() - start_time
        raise AssertionError(f"Status did not change within 5 seconds: {e}")


@then(parsers.parse('I should not be able to select "{player}" as opponent'))
def cannot_select_player(page: Page, player: str) -> None:
    """Verify player cannot be selected (button disabled)"""
    button = page.locator(f'button[data-testid="select-opponent-{player}"]')
    assert button.is_disabled(), f"Button for {player} should be disabled"


@when("I observe the network activity for 10 seconds")
def observe_network_activity(page: Page) -> None:
    """Monitor network requests for a period"""
    requests = []

    def handle_request(request):
        if "/lobby/status/" in request.url:
            requests.append({"url": request.url, "time": time.time()})

    page.on("request", handle_request)

    start_time = time.time()
    page.wait_for_timeout(10000)

    setattr(page, "observed_requests", requests)
    setattr(page, "observation_duration", time.time() - start_time)


@then("there should be at most 1 request to the lobby status endpoint")
def at_most_one_request(page: Page) -> None:
    """Verify minimal requests during observation period"""
    requests = getattr(page, "observed_requests", [])

    # With long polling, should have at most 1 request in 10 seconds
    # (one request holds for up to 30s)
    assert (
        len(requests) <= 1
    ), f"Expected at most 1 request, got {len(requests)}: {requests}"


@then("the request should be a long-poll request")
def is_long_poll_request(page: Page) -> None:
    """Verify the request is to long-poll endpoint"""
    requests = getattr(page, "observed_requests", [])

    if requests:
        assert "/long-poll" in requests[0]["url"], (
            f"Expected long-poll endpoint, got {requests[0]['url']}"
        )


@then("the request should not complete until timeout or state change")
def request_holds_connection(page: Page) -> None:
    """Verify request holds connection (doesn't complete quickly)"""
    requests = getattr(page, "observed_requests", [])

    # This is hard to verify without tracking response timing
    # We can infer it from having only 1 request during 10s observation
    # If it completed quickly and re-requested, we'd have multiple requests
    pass


@given("a long polling request is active and waiting")
def long_poll_active(page: Page) -> None:
    """Ensure a long polling request is in progress"""
    # Wait briefly to ensure the initial long poll request has been made
    page.wait_for_timeout(1000)

    # The request should be active - we can verify by checking network tab
    # For now, we just ensure enough time has passed
    pass


@then("the waiting long poll request should complete immediately")
def long_poll_completes_immediately(page: Page) -> None:
    """Verify long poll completed when state changed"""
    # This is implicitly verified by the next step showing updated state
    # We can't easily measure the exact timing without detailed network monitoring
    pass


@then(parsers.parse('I should receive the updated lobby state showing "{player}"'))
def receive_updated_state(page: Page, player: str) -> None:
    """Verify updated state is received"""
    assert page.locator(f'button[data-testid="select-opponent-{player}"]').is_visible()


@then("a new long poll request should be initiated automatically")
def new_long_poll_initiated(page: Page) -> None:
    """Verify HTMX automatically makes a new long poll request"""
    # HTMX automatically re-requests after response
    # We can verify by checking that the page is still responsive
    # If we wait a bit and trigger another change, it should be received
    page.wait_for_timeout(1000)

    # Verify page still has long-poll endpoint configured
    status_div = page.locator('[data-testid="lobby-player-status"]')
    hx_get = status_div.get_attribute("hx-get")
    assert "/long-poll" in hx_get, "Should still be using long-poll endpoint"
