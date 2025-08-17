import pytest
from playwright.sync_api import sync_playwright, Page, Browser


# Base URL constant
BASE_URL = "http://localhost:8000/"


@pytest.fixture(scope="function")
def browser():
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser):
    page: Page = browser.new_page()
    page.set_default_timeout(3000)  # 3 seconds
    yield page
    page.close()


# Shared helper functions
def navigate_to_login(page: Page) -> None:
    """Navigate to login page"""
    page.goto(BASE_URL)


def fill_player_name(page: Page, player_name: str) -> None:
    """Fill in player name field"""
    page.locator('input[type="text"][name="player_name"]').fill(player_name)


def click_multiplayer_button(page: Page) -> None:
    """Click the 'Play against Another Player' button"""
    page.locator('button[value="human"]').click()


def login_and_select_multiplayer(page: Page, player_name: str = "TestPlayer") -> None:
    """Complete login flow and select multiplayer mode"""
    navigate_to_login(page)
    fill_player_name(page, player_name)
    click_multiplayer_button(page)
    # Should be redirected to lobby page
    page.wait_for_url("**/lobby*")