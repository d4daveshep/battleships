import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import sync_playwright, Page, Browser, Locator


scenarios("features/login.feature")


@pytest.fixture(scope="function")
def browser():
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser):
    page: Page = browser.new_page()
    yield page
    page.close()


@given("I am on the login page")
def on_login_page(page: Page):
    page.goto("http://localhost:8000/")
    assert page.locator("h1").text_content() == "Battleships Login"


@given("the login page is fully loaded")
def login_page_is_loaded(page: Page):
    assert page.locator('input[type="text"][name="player_name"]').is_visible()
    assert page.locator('button[value="computer"]').is_visible()
    assert page.locator('button[value="human"]').is_visible()


@given("the player name field is empty")
def player_name_field_is_empty(page: Page):
    player_name_input: Locator = page.locator('input[type="text"][name="player_name"]')
    assert player_name_input.input_value() == ""


@when(parsers.parse('I enter "{player_name}" as my player name'))
def enter_player_name(page: Page, player_name: str):
    page.locator('input[type="text"][name="player_name"]').fill(player_name)


@when('I click the "Play against Computer" button')
def click_play_against_computer(page: Page):
    page.locator('button[value="computer"]').click()


@when('I click the "Play against Another Player" button')
def click_play_against_human(page: Page):
    page.locator('button[value="human"]').click()


@then("I should be redirected to the game interface")
def on_game_page(page: Page):
    page.wait_for_url("**/game")
    assert "game" in page.url


@then("I should be redirected to the multiplayer lobby")
def on_multiplayer_lobby_page(page: Page):
    page.wait_for_url("**/lobby")
    assert "lobby" in page.url


@then("the game should be configured for single player mode")
def player_mode_is_single_player(page: Page):
    assert page.locator('[data-testid="game-mode"]').text_content() == "Single Player"


@then("the game should be configured for two player mode")
def player_mode_is_two_player(page: Page):
    assert page.locator('[data-testid="game-mode"]').text_content() == "Two Player"


@then(parsers.parse('my player name should be set to "{expected_name}"'))
def player_name_is_set(page: Page, expected_name: str):
    assert page.locator('[data-testid="player-name"]').text_content() == expected_name
