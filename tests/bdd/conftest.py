import subprocess
import time
from dataclasses import dataclass, field

import httpx
import pytest
from bs4 import BeautifulSoup
from httpx import Response
from playwright.sync_api import Browser, Page, sync_playwright
from starlette.testclient import TestClient


# =============================================================================
# Constants
# =============================================================================

BASE_URL = "http://localhost:8000/"

# Long-polling timeout in milliseconds
# Server-side long-poll timeout is 35 seconds, so client timeout must be higher
LONG_POLL_TIMEOUT_MS = 40000


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
    game_url: str | None = None

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


@dataclass
class ShipPlacementBDDContext(BaseBDDContext):
    """BDD context for ship placement scenarios.

    Extends base context with ship placement-specific state tracking.
    """

    player_name: str | None = None
    selected_ship: str | None = None
    placed_ships: dict[str, list[str]] = field(default_factory=dict)
    last_placement_error: str | None = None
    game_mode: str = "computer"


@dataclass
class LobbyBDDContext(MultiPlayerBDDContext):
    """BDD context for lobby-related scenarios.

    Extends multiplayer context with lobby-specific state tracking.
    """

    expected_lobby_players: list[dict[str, str]] = field(default_factory=list)
    game_request_sender: str | None = None
    game_request_target: str | None = None
    expected_new_player: str | None = None
    player_who_left: str | None = None
    player_versions: dict[str, int] = field(default_factory=dict)


# =============================================================================
# Ship Placement Utilities
# =============================================================================

# Maps human-readable orientation names to API values
ORIENTATION_MAP: dict[str, str] = {
    "horizontally": "horizontal",
    "vertically": "vertical",
    "diagonally-down": "diagonal-down",
    "diagonally-up": "diagonal-up",
}

# Standard ship names in placement order
SHIP_NAMES: list[str] = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]

# Default ship placement coordinates for non-overlapping horizontal layout
DEFAULT_SHIP_PLACEMENTS: list[tuple[str, str, str]] = [
    ("Carrier", "A1", "horizontal"),
    ("Battleship", "C1", "horizontal"),
    ("Cruiser", "E1", "horizontal"),
    ("Submarine", "G1", "horizontal"),
    ("Destroyer", "I1", "horizontal"),
]


def get_orientation_value(orientation_text: str) -> str:
    """Convert human-readable orientation to API value.

    Args:
        orientation_text: Text like "horizontally" or "diagonal-down"

    Returns:
        API-compatible orientation value
    """
    return ORIENTATION_MAP.get(orientation_text, orientation_text)


def place_ship_fastapi(
    client: TestClient,
    player_name: str,
    ship_name: str,
    start_coordinate: str,
    orientation: str,
) -> Response:
    """Place a ship via FastAPI endpoint.

    Args:
        client: TestClient instance
        player_name: Name of the player
        ship_name: Name of the ship (e.g., "Carrier")
        start_coordinate: Starting coordinate (e.g., "A1")
        orientation: Orientation value (e.g., "horizontal")

    Returns:
        Response from the place-ship endpoint
    """
    return client.post(
        "/place-ship",
        data={
            "player_name": player_name,
            "ship_name": ship_name,
            "start_coordinate": start_coordinate,
            "orientation": get_orientation_value(orientation),
        },
    )


def place_all_ships_fastapi(
    client: TestClient,
    player_name: str,
    ships: list[tuple[str, str, str]] | None = None,
) -> None:
    """Place all 5 ships for a player using default non-overlapping layout.

    Args:
        client: TestClient instance
        player_name: Name of the player
        ships: Optional list of (ship_name, start_coord, orientation) tuples
               Defaults to standard horizontal layout
    """
    if ships is None:
        ships = DEFAULT_SHIP_PLACEMENTS

    for ship_name, start_coord, orientation in ships:
        place_ship_fastapi(client, player_name, ship_name, start_coord, orientation)


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
    page.set_default_timeout(LONG_POLL_TIMEOUT_MS)
    yield page
    page.close()


# =============================================================================
# Browser Helper Functions (Playwright)
# =============================================================================


def navigate_to_login(page: Page) -> None:
    """Navigate to login page."""
    page.goto(f"{BASE_URL}login")


def fill_player_name(page: Page, player_name: str) -> None:
    """Fill in player name field."""
    page.locator('input[type="text"][name="player_name"]').fill(player_name)


def click_multiplayer_button(page: Page) -> None:
    """Click the 'Play against Another Player' button."""
    page.locator('button[value="human"]').click()


def click_computer_button(page: Page) -> None:
    """Click the 'Play against Computer' button."""
    page.locator('button[value="computer"]').click()


def login_and_select_multiplayer(page: Page, player_name: str = "TestPlayer") -> None:
    """Complete login flow and select multiplayer mode.

    Args:
        page: Playwright Page instance
        player_name: Name for the player (defaults to "TestPlayer")
    """
    navigate_to_login(page)
    fill_player_name(page, player_name)
    click_multiplayer_button(page)
    page.wait_for_url("**/lobby*")


def login_and_select_computer(page: Page, player_name: str = "TestPlayer") -> None:
    """Complete login flow and select single-player (computer) mode.

    Args:
        page: Playwright Page instance
        player_name: Name for the player (defaults to "TestPlayer")
    """
    navigate_to_login(page)
    fill_player_name(page, player_name)
    click_computer_button(page)
    page.wait_for_url("**/start-game*")


# =============================================================================
# FastAPI Helper Functions (TestClient)
# =============================================================================


def login_player_fastapi(
    client: TestClient,
    player_name: str,
    game_mode: str = "human",
) -> Response:
    """Complete login flow for a player via FastAPI.

    Args:
        client: TestClient instance
        player_name: Name of the player
        game_mode: Game mode ("human" or "computer")

    Returns:
        Response from the login endpoint
    """
    client.get("/")  # Ensure session is initialized
    return client.post(
        "/login",
        data={"player_name": player_name, "game_mode": game_mode},
    )


def verify_on_page_fastapi(
    context: BaseBDDContext,
    expected_h1_text: str,
    expected_status: int = 200,
) -> None:
    """Verify current page in FastAPI context.

    Args:
        context: BDD context with response and soup
        expected_h1_text: Text that should appear in h1 element
        expected_status: Expected HTTP status code (default 200)
    """
    assert context.soup is not None, "No page loaded"
    assert context.response is not None, "No response received"
    h1_element = context.soup.find("h1")
    assert h1_element is not None, "No h1 element found"
    assert expected_h1_text in h1_element.get_text(), (
        f"Expected '{expected_h1_text}' in page title, got '{h1_element.get_text()}'"
    )
    assert context.response.status_code == expected_status, (
        f"Expected status {expected_status}, got {context.response.status_code}"
    )


def login_and_goto_lobby_fastapi(
    client: TestClient,
    player_name: str,
) -> Response:
    """Login as player and navigate to lobby page.

    Args:
        client: TestClient instance
        player_name: Name of the player

    Returns:
        Response from lobby page (after following redirect)
    """
    login_response = login_player_fastapi(client, player_name, "human")
    if login_response.status_code == 303:
        redirect_url = login_response.headers.get("location", "/lobby")
        return client.get(redirect_url)
    return login_response
