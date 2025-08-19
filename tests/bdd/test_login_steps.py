from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, Locator
from tests.bdd.conftest import BASE_URL


scenarios("../../features/login.feature")


def on_login_page(page: Page) -> None:
    assert page.locator("h1").text_content() == "Battleships Login"
    assert page.url.endswith("/") or "login" in page.url


@given("I am on the login page")
def goto_login_page(page: Page) -> None:
    page.goto(BASE_URL)
    on_login_page(page)


@given("the login page is fully loaded")
def login_page_is_loaded(page: Page) -> None:
    assert page.locator('input[type="text"][name="player_name"]').is_visible()
    assert page.locator('button[value="computer"]').is_visible()
    assert page.locator('button[value="human"]').is_visible()


@given("the player name field is empty")
def player_name_field_is_empty(page: Page) -> None:
    player_name_input: Locator = page.locator('input[type="text"][name="player_name"]')
    assert player_name_input.input_value() == ""


@when(parsers.parse('I enter "{player_name}" as my player name'))
def enter_player_name(page: Page, player_name: str) -> None:
    page.locator('input[type="text"][name="player_name"]').fill(player_name)


@given('I click the "Play against Computer" button')
@when('I click the "Play against Computer" button')
def click_play_against_computer(page: Page) -> None:
    page.locator('button[value="computer"]').click()


@when('I click the "Play against Another Player" button')
def click_play_against_human(page: Page) -> None:
    page.locator('button[value="human"]').click()


@then("I should be redirected to the game interface")
def on_game_page(page: Page) -> None:
    page.wait_for_url("**/game*")
    assert "game" in page.url


@then("I should be redirected to the multiplayer lobby")
def on_multiplayer_lobby_page(page: Page) -> None:
    page.wait_for_url("**/lobby*")
    assert "lobby" in page.url


@then("the game should be configured for single player mode")
def player_mode_is_single_player(page: Page) -> None:
    assert page.locator('[data-testid="game-mode"]').text_content() == "Single Player"


@then("the game should be configured for two player mode")
def player_mode_is_two_player(page: Page) -> None:
    assert page.locator('[data-testid="game-mode"]').text_content() == "Two Player"


@then(parsers.parse('my player name should be set to "{expected_name}"'))
def player_name_is_set(page: Page, expected_name: str) -> None:
    assert page.locator('[data-testid="player-name"]').text_content() == expected_name


@then(parsers.parse('I should see an error message "{error_message}"'))
def error_message_displayed(page: Page, error_message: str) -> None:
    assert page.locator('[data-testid="error-message"]').text_content() == error_message


@then("I should remain on the login page")
def remain_on_login_page(page: Page) -> None:
    on_login_page(page)
