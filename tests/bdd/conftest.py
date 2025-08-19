import subprocess
import time

import httpx
import pytest
from playwright.sync_api import Browser, Page, sync_playwright


# Base URL constant
BASE_URL = "http://localhost:8000/"


@pytest.fixture(scope="session")
def fastapi_server():
    """Start FastAPI server for the entire test session"""
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--port", "8000", "--host", "127.0.0.1"]
    )

    # Wait for server to be ready with health check
    for _ in range(30):  # 30 second timeout
        try:
            with httpx.Client() as client:
                response = client.get(f"{BASE_URL}health", timeout=1)
                if response.status_code == 200:
                    break
        except:
            time.sleep(1)
    else:
        process.kill()
        raise RuntimeError("FastAPI server failed to start")

    yield process
    process.terminate()
    process.wait()


@pytest.fixture(scope="function")
def browser():
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser, fastapi_server):
    """Page fixture that depends on running server"""
    page: Page = browser.new_page()
    page.set_default_timeout(5000)  # 5 seconds
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


