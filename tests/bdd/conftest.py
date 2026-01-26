import subprocess
import time
from dataclasses import dataclass, field

import httpx
import pytest
from bs4 import BeautifulSoup
from httpx import Response
from playwright.sync_api import Browser, Page, sync_playwright
from starlette.testclient import TestClient


# Base URL constant
BASE_URL = "http://localhost:8000/"


@dataclass
class BaseBDDContext:
    """Base class for BDD test contexts with HTTP response handling.

    This provides common functionality for maintaining state between BDD steps,
    including response tracking and HTML parsing. Feature-specific contexts
    should inherit from this class and add their own fields.
    """

    response: Response | None = None
    soup: BeautifulSoup | None = None
    form_data: dict[str, str] = field(default_factory=dict)

    def update_response(self, response: Response) -> None:
        """Update context with new response and parse HTML.

        Args:
            response: The HTTP response to store and parse
        """
        self.response = response
        self.soup = BeautifulSoup(response.text, "html.parser")

    def assert_on_page(self, page_title_contains: str) -> None:
        """Assert that the current page contains expected title text.

        Args:
            page_title_contains: Text that should appear in the h1 element
        """
        assert self.soup is not None, "No page loaded"
        assert self.response is not None, "No response received"
        h1_element = self.soup.find("h1")
        assert h1_element is not None, "No h1 element found"
        assert page_title_contains in h1_element.get_text(), (
            f"Expected '{page_title_contains}' in page title, "
            f"got '{h1_element.get_text()}'"
        )


@dataclass
class MultiPlayerBDDContext(BaseBDDContext):
    """Extended BDD context for multi-player scenarios.

    Adds support for managing multiple player clients and tracking
    game state across players.
    """

    current_player_name: str | None = None
    player_clients: dict[str, TestClient] = field(default_factory=dict)

    def get_client_for_player(self, player_name: str) -> TestClient:
        """Get or create a TestClient for a specific player.

        Args:
            player_name: The name of the player

        Returns:
            TestClient instance for the player
        """
        if player_name not in self.player_clients:
            from main import app

            self.player_clients[player_name] = TestClient(app, follow_redirects=False)
        return self.player_clients[player_name]


@pytest.fixture(autouse=True)
def reset_lobby(fastapi_server):
    """Reset global lobby state before each BDD scenario"""
    # Reset lobby state via HTTP call to the running server
    try:
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}test/reset-lobby", timeout=5)
            if response.status_code == 200:
                print(f"Lobby reset successful: {response.json()}")
            else:
                print(f"Lobby reset failed: {response.status_code}")
    except Exception as e:
        print(f"Failed to reset lobby: {e}")

    yield

    # Optional: cleanup after test too
    try:
        with httpx.Client() as client:
            client.post(f"{BASE_URL}test/reset-lobby", timeout=5)
    except Exception:
        pass  # Ignore cleanup failures


@pytest.fixture(scope="session")
def fastapi_server():
    """Start FastAPI server for the entire test session"""
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--port", "8000", "--host", "0.0.0.0"]
    )

    # Wait for server to be ready with health check
    for _ in range(30):  # 30 second timeout
        try:
            with httpx.Client() as client:
                response = client.get(f"{BASE_URL}health", timeout=1)
                if response.status_code == 200:
                    break
        except Exception:
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
    page.set_default_timeout(40000)  # 40 seconds (to accommodate 35s long poll timeout)
    yield page
    page.close()


# Shared helper functions
def navigate_to_login(page: Page) -> None:
    """Navigate to login page"""
    page.goto(f"{BASE_URL}login")


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
