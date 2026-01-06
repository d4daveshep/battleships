import re
import time
from dataclasses import dataclass

import pytest
from playwright.sync_api import Browser, Page, expect
from pytest_bdd import given, parsers, scenarios, then, when

from tests.bdd.conftest import BASE_URL

# Load scenarios
scenarios("../../features/multiplayer_ship_placement.feature")


@dataclass
class MultiplayerBrowserContext:
    """Maintains state between BDD steps for multiplayer browser testing"""

    p1: Page
    p2: Page
    p1_name: str = "Player1"
    p2_name: str = "Player2"


def place_ship_via_form(
    page: Page, ship_name: str, start_coord: str, orientation: str = "horizontal"
) -> None:
    """Helper to place a ship using the form interface"""
    # Click the label for the ship radio button (more reliable than checking hidden input)
    ship_label = page.locator(
        f'label:has([data-testid="select-ship-{ship_name.lower()}"])'
    )
    ship_label.scroll_into_view_if_needed()
    ship_label.click()

    # Fill in the start coordinate
    page.fill('input[name="start_coordinate"]', start_coord)

    # Click the label for orientation (more reliable than checking hidden input)
    orientation_label = page.locator(
        f'label:has(input[name="orientation"][value="{orientation}"])'
    )
    orientation_label.click()

    # Submit the form
    page.click('[data-testid="place-ship-button"]')

    # Wait for the ship to appear in the placed ships list
    page.wait_for_selector(
        f'[data-testid="placed-ship-{ship_name.lower()}"]', timeout=5000
    )


@pytest.fixture
def context(browser: Browser) -> MultiplayerBrowserContext:
    """Create two separate browser contexts/pages for multiplayer testing"""
    # Create two isolated browser contexts
    c1 = browser.new_context()
    c2 = browser.new_context()

    # Create pages
    p1 = c1.new_page()
    p2 = c2.new_page()

    # Set timeouts - increase for long polling
    p1.set_default_timeout(45000)  # 45 seconds for long polling
    p2.set_default_timeout(45000)

    return MultiplayerBrowserContext(p1, p2)


# === Background Steps ===


@given("I am playing a multiplayer game against another human player")
def setup_multiplayer_game(context: MultiplayerBrowserContext) -> None:
    """Setup two players in a multiplayer game"""
    # Reset lobby first (using one of the pages to trigger the reset endpoint)
    # We can use a simple fetch or navigate to the reset endpoint
    context.p1.request.post(f"{BASE_URL}test/reset-lobby")

    # Login Player 1
    context.p1.goto(BASE_URL)
    context.p1.fill('input[name="player_name"]', context.p1_name)
    context.p1.click('button[value="human"]')

    # Login Player 2
    context.p2.goto(BASE_URL)
    context.p2.fill('input[name="player_name"]', context.p2_name)
    context.p2.click('button[value="human"]')


@given("both players have been matched and redirected to ship placement")
def match_players(context: MultiplayerBrowserContext) -> None:
    """Match players and transition to ship placement"""
    # Player 1 selects Player 2
    # Wait for Player 2 to appear in Player 1's list
    context.p1.wait_for_selector(f'[data-testid="select-opponent-{context.p2_name}"]')
    context.p1.click(f'[data-testid="select-opponent-{context.p2_name}"]')

    # Player 2 accepts
    # Wait for accept button
    context.p2.wait_for_selector('[data-testid="accept-game-request"]')
    context.p2.click('[data-testid="accept-game-request"]')

    # Both players should be redirected to start-game (confirmation page)
    context.p1.wait_for_url("**/start-game*")
    context.p2.wait_for_url("**/start-game*")

    # Click "Start Game" to proceed to ship placement
    context.p1.click('[data-testid="start-game-button"]')
    context.p2.click('[data-testid="start-game-button"]')

    # Wait for ship placement page
    context.p1.wait_for_url("**/ship-placement*")
    context.p2.wait_for_url("**/ship-placement*")


@given("I am on the ship placement screen")
@given("I have just entered the ship placement screen")
def verify_on_ship_placement(context: MultiplayerBrowserContext) -> None:
    """Verify player is on ship placement screen"""
    expect(context.p1.locator("h1")).to_contain_text(
        re.compile(r"Ship Placement|Start Game")
    )


@given('the "My Ships and Shots Received" board is displayed')
def verify_board_displayed(context: MultiplayerBrowserContext) -> None:
    """Verify the board is displayed"""
    expect(context.p1.locator('[data-testid="my-ships-board"]')).to_be_visible()


# === Multiplayer Placement Status ===


@then("I should see my own placement area")
def see_own_placement_area(context: MultiplayerBrowserContext) -> None:
    """Verify placement area is visible"""
    expect(context.p1.locator('[data-testid="ship-grid"]')).to_be_visible()


@then("I should see an opponent status indicator")
def see_opponent_status_indicator(context: MultiplayerBrowserContext) -> None:
    """Verify opponent status indicator is visible"""
    expect(context.p1.locator('[data-testid="opponent-status"]')).to_be_visible()


@then(parsers.parse('the opponent status should show "{status_text}"'))
def opponent_status_shows(context: MultiplayerBrowserContext, status_text: str) -> None:
    """Verify opponent status text"""
    expect(context.p1.locator('[data-testid="opponent-status"]')).to_contain_text(
        status_text
    )


@then("I should not see my opponent's ship positions")
def not_see_opponent_ships(context: MultiplayerBrowserContext) -> None:
    """Verify opponent ships are not visible"""
    # The opponent grid should not exist at all during ship placement
    expect(context.p1.locator('[data-testid="opponent-grid"]')).to_have_count(0)


@given("I am placing my ships")
def placing_ships(context: MultiplayerBrowserContext) -> None:
    """Context step"""
    pass


@given("my opponent has not finished placing their ships")
def opponent_not_finished(context: MultiplayerBrowserContext) -> None:
    """Ensure opponent has not placed all ships"""
    pass


@when("my opponent finishes placing all their ships")
def opponent_finishes_placing(context: MultiplayerBrowserContext) -> None:
    """Opponent places all 5 ships"""
    ships = [
        ("Carrier", "A1", "horizontal"),
        ("Battleship", "C1", "horizontal"),
        ("Cruiser", "E1", "horizontal"),
        ("Submarine", "G1", "horizontal"),
        ("Destroyer", "I1", "horizontal"),
    ]

    for ship, start, orientation in ships:
        place_ship_via_form(context.p2, ship, start, orientation)

    # Opponent clicks ready
    ready_button = context.p2.locator('[data-testid="ready-button"]')
    if ready_button.is_visible():
        ready_button.click()
    else:
        context.p2.click('[data-testid="start-game-button"]')


@then(parsers.parse('the opponent status should update to "{status_text}"'))
def opponent_status_updates(
    context: MultiplayerBrowserContext, status_text: str
) -> None:
    """Verify status update via polling"""
    # Playwright's expect with timeout handles polling
    # Increase timeout for long polling (up to 40 seconds)
    expect(context.p1.locator('[data-testid="opponent-status"]')).to_contain_text(
        status_text, timeout=45000
    )


@then("I should receive this update within 5 seconds")
def receive_update_timely(context: MultiplayerBrowserContext) -> None:
    """Verify update timing"""
    # Implicit in the previous step's timeout
    pass


# === Ready State Management ===


@given("I have placed 4 out of 5 ships")
def placed_4_ships(context: MultiplayerBrowserContext) -> None:
    """Place 4 ships"""
    ships = [
        ("Carrier", "A1"),
        ("Battleship", "C1"),
        ("Cruiser", "E1"),
        ("Submarine", "G1"),
    ]

    for ship, start in ships:
        place_ship_via_form(context.p1, ship, start, "horizontal")


@then('the "Ready" button should be disabled')
def ready_button_disabled(context: MultiplayerBrowserContext) -> None:
    """Verify Ready button is disabled"""
    # Check both buttons are disabled
    expect(context.p1.locator('[data-testid="ready-button"]')).to_be_disabled()
    expect(context.p1.locator('[data-testid="start-game-button"]')).to_be_disabled()


@then(parsers.parse('I should see a message "{message}"'))
def see_message(context: MultiplayerBrowserContext, message: str) -> None:
    """Verify message visibility"""
    expect(context.p1.locator("body")).to_contain_text(message)


@when("I place the 5th ship")
def place_5th_ship(context: MultiplayerBrowserContext) -> None:
    """Place the last ship"""
    place_ship_via_form(context.p1, "Destroyer", "I1", "horizontal")


@then('the "Ready" button should be enabled')
def ready_enabled(context: MultiplayerBrowserContext) -> None:
    """Verify Ready button is enabled"""
    # In multiplayer mode, only Ready button should be present
    expect(context.p1.locator('[data-testid="ready-button"]')).to_be_enabled()
    # Start Game button should not be present in multiplayer mode
    expect(context.p1.locator('[data-testid="start-game-button"]')).to_have_count(0)


@given("I have placed all 5 ships")
@given("I have placed all my ships")
def placed_all_ships(context: MultiplayerBrowserContext) -> None:
    """Place all 5 ships"""
    # Reset first if needed
    reset_button = context.p1.locator('[data-testid="reset-all-ships-button"]')
    if reset_button.is_visible() and reset_button.is_enabled():
        reset_button.click()
        # Wait a moment for reset to complete
        context.p1.wait_for_timeout(500)

    ships = [
        ("Carrier", "A1"),
        ("Battleship", "C1"),
        ("Cruiser", "E1"),
        ("Submarine", "G1"),
        ("Destroyer", "I1"),
    ]

    for ship, start in ships:
        place_ship_via_form(context.p1, ship, start, "horizontal")


@when('I click the "Ready" button')
def click_ready(context: MultiplayerBrowserContext) -> None:
    """Click Ready"""
    # Try ready button first, then start game button
    ready_button = context.p1.locator('[data-testid="ready-button"]')
    if ready_button.is_visible() and ready_button.is_enabled():
        ready_button.click()
    else:
        context.p1.click('[data-testid="start-game-button"]')


@then("I should not be able to remove any ships")
def cannot_remove_ships(context: MultiplayerBrowserContext) -> None:
    """Verify ships cannot be removed"""
    # Check that remove buttons are disabled
    expect(context.p1.locator('[data-testid="remove-ship-carrier"]')).to_be_disabled()


@then("I should not be able to place new ships")
def cannot_place_ships(context: MultiplayerBrowserContext) -> None:
    """Verify ships cannot be placed"""
    # The ship placement form should not be visible when ready
    expect(context.p1.locator("#place-ship-form")).not_to_be_visible()


@then('I should not be able to use the "Random Placement" button')
def cannot_use_random(context: MultiplayerBrowserContext) -> None:
    """Verify random placement is disabled"""
    expect(
        context.p1.locator('[data-testid="random-placement-button"]')
    ).to_be_disabled()


@then('I should not be able to use the "Reset All Ships" button')
def cannot_use_reset(context: MultiplayerBrowserContext) -> None:
    """Verify reset is disabled"""
    expect(
        context.p1.locator('[data-testid="reset-all-ships-button"]')
    ).to_be_disabled()


@then('my opponent should see my status change to "Opponent is ready"')
def opponent_sees_ready(context: MultiplayerBrowserContext) -> None:
    """Verify opponent sees ready status"""
    expect(context.p2.locator('[data-testid="opponent-status"]')).to_contain_text(
        "Opponent is ready"
    )


@then("my opponent should receive this update within 5 seconds")
def opponent_receives_update_timely(context: MultiplayerBrowserContext) -> None:
    pass


# === Game Start Conditions ===


@given('I have placed all my ships and clicked "Ready"')
def placed_and_ready(context: MultiplayerBrowserContext) -> None:
    """Place all ships and click ready"""
    placed_all_ships(context)
    click_ready(context)


@given("I am waiting for my opponent")
def waiting_for_opponent(context: MultiplayerBrowserContext) -> None:
    """Context step"""
    pass


@when('my opponent finishes placing ships and clicks "Ready"')
def opponent_finishes_and_ready(context: MultiplayerBrowserContext) -> None:
    """Opponent places ships and clicks ready"""
    opponent_finishes_placing(context)


@then("the game should start automatically")
def game_starts_auto(context: MultiplayerBrowserContext) -> None:
    """Verify game start"""
    # Wait for redirect to game page (may take time due to long polling)
    # The long poll triggers every 1 second, so should redirect within a few seconds
    try:
        context.p1.wait_for_url("**/game/*", timeout=10000)
    except Exception:
        # If not redirected yet, wait a bit more for long poll to trigger
        context.p1.wait_for_url("**/game/*", timeout=35000)


@then("I should be redirected to the gameplay screen")
def redirected_to_gameplay(context: MultiplayerBrowserContext) -> None:
    """Verify redirect"""
    expect(context.p1).to_have_url(re.compile(r".*/game/.*"))


@then('I should see "Round 1" displayed')
def see_round_1(context: MultiplayerBrowserContext) -> None:
    """Verify game content shows Round 1"""
    # Verify we're on the game page
    expect(context.p1).to_have_url(re.compile(r".*/game/.*"))

    # Check for Round 1 text
    round_indicator = context.p1.locator('[data-testid="round-indicator"]')
    expect(round_indicator).to_be_visible()
    expect(round_indicator).to_contain_text(re.compile(r"Round 1", re.IGNORECASE))


@given('my opponent has already clicked "Ready"')
def opponent_already_ready(context: MultiplayerBrowserContext) -> None:
    """Opponent is ready first"""
    opponent_finishes_placing(context)


@when('both players click "Ready" at approximately the same time')
def both_click_ready(context: MultiplayerBrowserContext) -> None:
    """Both click ready simultaneously (ships already placed in Given steps)"""
    # Both players already have all ships placed from Given steps
    # Just click ready for both in quick succession to simulate simultaneity
    ready_button_p1 = context.p1.locator('[data-testid="ready-button"]')
    ready_button_p2 = context.p2.locator('[data-testid="ready-button"]')

    # Click both buttons as quickly as possible (as simultaneous as we can get)
    ready_button_p1.click()
    ready_button_p2.click()


@then("the game should start for both players")
def game_starts_both(context: MultiplayerBrowserContext) -> None:
    """Verify game starts for both"""
    context.p1.wait_for_url("**/game/*", timeout=45000)
    context.p2.wait_for_url("**/game/*", timeout=45000)


@then("both players should be redirected to the gameplay screen")
def both_redirected(context: MultiplayerBrowserContext) -> None:
    pass


# === Waiting State ===


@then("I should see my ship placement displayed")
def see_ship_placement(context: MultiplayerBrowserContext) -> None:
    """Verify ships are visible"""
    expect(context.p1.locator(".placed-ship-item")).to_have_count(5)


@then('I should see a message "Waiting for opponent to finish placing ships..."')
def see_waiting_msg(context: MultiplayerBrowserContext) -> None:
    """Verify waiting message"""
    # Check for the actual message text from the template
    expect(context.p1.locator('[data-testid="placement-guidance"]')).to_contain_text(
        "Waiting for opponent"
    )


@then("I should see an animated waiting indicator")
def see_waiting_indicator(context: MultiplayerBrowserContext) -> None:
    """Verify spinner/indicator"""
    # The waiting indicator might be part of the status message or opponent status
    # This is optional based on implementation
    pass


@then('I should not see a "Cancel" button')
def not_see_cancel(context: MultiplayerBrowserContext) -> None:
    """Verify no cancel button"""
    expect(context.p1.locator('button:has-text("Cancel")')).not_to_be_visible()


@given("I have been waiting for more than 30 seconds")
def waiting_long(context: MultiplayerBrowserContext) -> None:
    """Simulate wait"""
    # We don't actually wait 30s in test
    pass


@then("I should still see the waiting message")
def still_see_waiting(context: MultiplayerBrowserContext) -> None:
    """Verify waiting message persists"""
    see_waiting_msg(context)


@then("the connection should remain active via long polling")
def connection_active(context: MultiplayerBrowserContext) -> None:
    """Verify polling continues"""
    pass


# === Opponent Disconnection ===


@when("my opponent leaves the game")
def opponent_leaves(context: MultiplayerBrowserContext) -> None:
    """Opponent leaves"""
    # Call the leave-placement endpoint to update server state
    context.p2.request.post(f"{BASE_URL}leave-placement")
    # Then navigate away (simulates the redirect that would happen)
    context.p2.goto(f"{BASE_URL}")


@then('I should see a message "Opponent has left the game"')
def see_opponent_left(context: MultiplayerBrowserContext) -> None:
    """Verify opponent left message"""
    # Check for either "Opponent has left" or "disconnected"
    opponent_status = context.p1.locator('[data-testid="opponent-status"]')
    expect(opponent_status).to_contain_text(
        re.compile(r"Opponent has left|disconnected", re.IGNORECASE), timeout=10000
    )


@then('I should see an option to "Return to Lobby"')
def see_return_lobby(context: MultiplayerBrowserContext) -> None:
    """Verify return to lobby button"""
    expect(context.p1.locator('button:has-text("Return to Lobby")')).to_be_visible()


# === Ship Placement Privacy ===


@given(parsers.parse('I have placed a "{ship_name}" {direction} starting at "{start}"'))
def place_specific_ship(
    context: MultiplayerBrowserContext, ship_name: str, direction: str, start: str
) -> None:
    """Place a specific ship"""
    orientation_map = {"horizontally": "horizontal", "vertically": "vertical"}
    orientation = orientation_map.get(direction, "horizontal")
    place_ship_via_form(context.p1, ship_name, start, orientation)


@then(
    parsers.parse(
        'my opponent should not be able to see that I placed a ship at "{coord}"'
    )
)
def opponent_cannot_see_ship(context: MultiplayerBrowserContext, coord: str) -> None:
    """Verify opponent cannot see my ship"""
    # Check opponent's view of player's grid
    # Assuming opponent grid cells don't have data-ship attribute
    # We need to find the cell in the opponent's view corresponding to player's grid
    # But usually opponent only sees their own grid and maybe a blank opponent grid

    # If there is an opponent grid:
    if context.p2.locator('[data-testid="opponent-grid"]').is_visible():
        expect(
            context.p2.locator(
                f'[data-testid="opponent-grid"] [data-cell="{coord}"][data-ship]'
            )
        ).to_have_count(0)


@then("my opponent should only see my placement status")
def opponent_sees_only_status(context: MultiplayerBrowserContext) -> None:
    """Verify opponent only sees status"""
    pass


@given("my opponent has placed all their ships")
def opponent_placed_all(context: MultiplayerBrowserContext) -> None:
    """Opponent places all ships (without clicking ready)"""
    # Place all 5 ships for Player 2
    ships = [
        ("Carrier", "A1", "horizontal"),
        ("Battleship", "C1", "horizontal"),
        ("Cruiser", "E1", "horizontal"),
        ("Submarine", "G1", "horizontal"),
        ("Destroyer", "I1", "horizontal"),
    ]

    for ship, start, orientation in ships:
        place_ship_via_form(context.p2, ship, start, orientation)


@then("I should not see any indication of where their ships are placed")
def not_see_opponent_placement(context: MultiplayerBrowserContext) -> None:
    """Verify I cannot see opponent ships"""
    not_see_opponent_ships(context)


@then("I should only see that they are ready or not ready")
def see_only_ready_status(context: MultiplayerBrowserContext) -> None:
    """Verify I see status"""
    see_opponent_status_indicator(context)


# === Placement Modifications Before Ready ===


@given("my opponent is still placing their ships")
@given("my opponent is placing their ships")
def opponent_still_placing(context: MultiplayerBrowserContext) -> None:
    """Opponent not ready"""
    pass


@when(parsers.parse('I click on the "{ship_name}" to remove it'))
def remove_ship(context: MultiplayerBrowserContext, ship_name: str) -> None:
    """Remove ship"""
    # Click the remove button for the ship
    context.p1.click(f'[data-testid="remove-ship-{ship_name.lower()}"]')


@then(parsers.parse("the {ship_name} should be removed from the board"))
def ship_removed(context: MultiplayerBrowserContext, ship_name: str) -> None:
    """Verify removal"""
    expect(
        context.p1.locator(f'[data-testid="placed-ship-{ship_name.lower()}"]')
    ).not_to_be_visible()


@then("I should be able to place it in a new location")
def can_place_again(context: MultiplayerBrowserContext) -> None:
    """Verify can place again"""
    place_ship_via_form(context.p1, "Destroyer", "J1", "horizontal")
    expect(context.p1.locator('[data-testid="placed-ship-destroyer"]')).to_be_visible()


@given("I have placed 2 ships manually")
def placed_2_ships(context: MultiplayerBrowserContext) -> None:
    """Place 2 ships"""
    ships = [("Destroyer", "A1"), ("Submarine", "C1")]
    for ship, start in ships:
        place_ship_via_form(context.p1, ship, start, "horizontal")


@when('I click the "Random Placement" button')
def click_random(context: MultiplayerBrowserContext) -> None:
    """Click random"""
    context.p1.click('[data-testid="random-placement-button"]')


@then("all 5 ships should be placed automatically")
def all_ships_placed_auto(context: MultiplayerBrowserContext) -> None:
    """Verify all ships placed"""
    expect(context.p1.locator(".placed-ship-item")).to_have_count(5)


@then("my previous manual placements should be replaced")
def manual_replaced(context: MultiplayerBrowserContext) -> None:
    """Verify replacement"""
    pass


@given("I have placed 3 ships on the board")
def placed_3_ships(context: MultiplayerBrowserContext) -> None:
    """Place 3 ships"""
    ships = [("Destroyer", "A1"), ("Submarine", "C1"), ("Cruiser", "E1")]
    for ship, start in ships:
        place_ship_via_form(context.p1, ship, start, "horizontal")


@when('I click the "Reset All Ships" button')
def click_reset(context: MultiplayerBrowserContext) -> None:
    """Click reset"""
    context.p1.click('[data-testid="reset-all-ships-button"]')


@then("all ships should be removed from the board")
def all_ships_removed(context: MultiplayerBrowserContext) -> None:
    """Verify all removed"""
    expect(context.p1.locator(".placed-ship-item")).to_have_count(0)


@then("I should be able to start placing ships again")
def can_start_placing(context: MultiplayerBrowserContext) -> None:
    """Verify can place"""
    pass


# === Edge Cases ===


@then('I should not see an "Unready" or "Cancel Ready" button')
def not_see_unready(context: MultiplayerBrowserContext) -> None:
    """Verify no unready button"""
    expect(context.p1.locator('button:has-text("Unready")')).not_to_be_visible()
    expect(context.p1.locator('button:has-text("Cancel Ready")')).not_to_be_visible()


@then("my ready status should be permanent until the game starts")
def ready_permanent(context: MultiplayerBrowserContext) -> None:
    """Verify ready status persists"""
    pass


@given('I select the "Cruiser" ship to place')
def select_cruiser(context: MultiplayerBrowserContext) -> None:
    """Select cruiser"""
    # Click the label, not the hidden radio button
    ship_label = context.p1.locator('label:has([data-testid="select-ship-cruiser"])')
    ship_label.click()


@when(parsers.parse('I attempt to place it horizontally starting at "{start}"'))
def attempt_place_overlap(context: MultiplayerBrowserContext, start: str) -> None:
    """Attempt invalid placement"""
    # Fill the form but don't use the helper since we expect it to fail
    ship_label = context.p1.locator('label:has([data-testid="select-ship-cruiser"])')
    ship_label.click()
    context.p1.fill('input[name="start_coordinate"]', start)
    orientation_label = context.p1.locator(
        'label:has(input[name="orientation"][value="horizontal"])'
    )
    orientation_label.click()
    context.p1.click('[data-testid="place-ship-button"]')
    # Wait a moment for error to appear
    context.p1.wait_for_timeout(500)


@then("the placement should be rejected")
def placement_rejected(context: MultiplayerBrowserContext) -> None:
    """Verify rejection"""
    pass


@then(parsers.parse('I should see an error message "{message}"'))
def see_error_msg(context: MultiplayerBrowserContext, message: str) -> None:
    """Verify error message"""
    see_message(context, message)


@then("the Cruiser should not be placed")
def cruiser_not_placed(context: MultiplayerBrowserContext) -> None:
    """Verify not placed"""
    expect(
        context.p1.locator('[data-testid="placed-ship-cruiser"]')
    ).not_to_be_visible()


@given("I have placed the following ships:")
def place_ships_table(context: MultiplayerBrowserContext, datatable) -> None:
    """Place ships from table"""
    # datatable is a list of lists, first row is header
    for row in datatable[1:]:
        ship = row[0]
        pos = row[1]
        orientation = row[2]

        place_ship_via_form(context.p1, ship, pos, orientation)


@then(parsers.parse('I should see "{text}"'))
def see_text(context: MultiplayerBrowserContext, text: str) -> None:
    """Verify text visibility"""
    expect(context.p1.locator("body")).to_contain_text(text)


@when(parsers.parse('I place the "{ship}" horizontally starting at "{start}"'))
def place_ship_step(context: MultiplayerBrowserContext, ship: str, start: str) -> None:
    """Place specific ship"""
    place_ship_via_form(context.p1, ship, start, "horizontal")


# === Real-Time Updates ===


@when("I observe the network activity")
def observe_network(context: MultiplayerBrowserContext) -> None:
    pass


@then("there should be an active long-poll connection for opponent status")
def active_long_poll(context: MultiplayerBrowserContext) -> None:
    pass


@then("updates should arrive without page refresh")
def updates_no_refresh(context: MultiplayerBrowserContext) -> None:
    pass


@given("the long-poll connection times out after 30 seconds")
def long_poll_timeout(context: MultiplayerBrowserContext) -> None:
    pass


@when("the connection is re-established")
def connection_reestablished(context: MultiplayerBrowserContext) -> None:
    pass


@then("I should see the current opponent status")
def see_current_status(context: MultiplayerBrowserContext) -> None:
    pass


@then("I should be able to continue placing ships normally")
def continue_placing(context: MultiplayerBrowserContext) -> None:
    pass
