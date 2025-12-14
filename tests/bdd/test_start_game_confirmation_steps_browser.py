from pytest_bdd import scenarios, given, when, then
from playwright.sync_api import Page, Locator
from tests.bdd.conftest import BASE_URL
import pytest
from dataclasses import dataclass


scenarios("../../features/start_game_confirmation_page.feature")


@dataclass
class StartGameConfirmationContext:
    """Maintains state between BDD steps for start game confirmation testing"""

    player_name: str = "TestPlayer"
    game_mode: str = "computer"


@pytest.fixture
def confirmation_context() -> StartGameConfirmationContext:
    """Provide a test context for maintaining state between BDD steps"""
    return StartGameConfirmationContext()


def on_start_game_confirmation_page(page: Page) -> None:
    """Helper function to verify we're on the start game confirmation page"""
    h1_element: Locator = page.locator("h1")
    h1_text: str | None = h1_element.text_content()
    assert h1_text is not None
    assert "Start Game Confirmation" in h1_text


# === Background Steps ===


@given("I am on the start game confirmation page")
def goto_start_game_confirmation_page(
    page: Page, confirmation_context: StartGameConfirmationContext
) -> None:
    """Navigate to start game confirmation page"""
    # First login to create a session
    page.goto(BASE_URL)
    page.locator('input[type="text"][name="player_name"]').fill(
        confirmation_context.player_name
    )
    page.locator(f'button[value="{confirmation_context.game_mode}"]').click()

    # Wait for redirect to confirmation page
    page.wait_for_load_state("networkidle")


@given("the page is fully loaded")
def page_is_fully_loaded(page: Page) -> None:
    """Verify page is fully loaded"""
    on_start_game_confirmation_page(page)


# === Scenario: Start game ===


@given("the game details are correct")
def game_details_are_correct(
    page: Page, confirmation_context: StartGameConfirmationContext
) -> None:
    """Verify game details are displayed correctly"""
    # Check for player name display
    player_name_element: Locator = page.locator('[data-testid="player-name"]')
    assert player_name_element.is_visible()
    player_name_text: str | None = player_name_element.text_content()
    assert player_name_text is not None
    assert confirmation_context.player_name in player_name_text

    # Check for game mode display
    game_mode_element: Locator = page.locator('[data-testid="game-mode"]')
    assert game_mode_element.is_visible()


@when('I choose "Start Game"')
def choose_start_game(page: Page) -> None:
    """Click the Start Game button"""
    start_game_button: Locator = page.locator(
        'button[type="submit"][value="start_game"]'
    )
    start_game_button.click()
    page.wait_for_load_state("networkidle")


@then("I should be redirected to the ship placement page")
def redirected_to_ship_placement(page: Page) -> None:
    """Verify redirect to ship placement page"""
    page.wait_for_url("**/ship-placement**")
    assert "ship-placement" in page.url or "ship_placement" in page.url

    # Verify we're on the ship placement page
    h1_element: Locator = page.locator("h1")
    h1_text: str | None = h1_element.text_content()
    assert h1_text is not None
    assert "Ship Placement" in h1_text


# === Scenario: Return to login page ===


@when('I choose "Return to Login"')
def choose_return_to_login(page: Page) -> None:
    """Click the Return to Login button"""
    return_to_login_button: Locator = page.locator(
        'button[type="submit"][value="return_to_login"]'
    )
    return_to_login_button.click()
    page.wait_for_load_state("networkidle")


@then("I should be redirected to the login page")
def redirected_to_login_page(page: Page) -> None:
    """Verify redirect to login page"""
    page.wait_for_url(BASE_URL)
    assert page.url == BASE_URL or page.url.endswith("/")

    # Verify we're on the login page
    h1_element: Locator = page.locator("h1")
    h1_text: str | None = h1_element.text_content()
    assert h1_text is not None
    assert "Battleships Login" in h1_text


# === Scenario: Exit completely ===


@when('I choose "Exit"')
def choose_exit(page: Page) -> None:
    """Click the Exit button"""
    exit_button: Locator = page.locator('button[type="submit"][value="exit"]')
    exit_button.click()
    page.wait_for_load_state("networkidle")


@then("I should be redirected to the goodbye page")
def redirected_to_goodbye_page(page: Page) -> None:
    """Verify redirect to goodbye page"""
    page.wait_for_url("**/goodbye**")
    assert "goodbye" in page.url

    # Verify we're on the goodbye page
    h1_element: Locator = page.locator("h1")
    h1_text: str | None = h1_element.text_content()
    assert h1_text is not None
    assert "Goodbye" in h1_text
