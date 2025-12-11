from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from httpx import Response
from dataclasses import dataclass, field
import pytest


scenarios("../../features/start_game_confirmation_page.feature")


@dataclass
class StartGameConfirmationContext:
    """Maintains state between BDD steps for start game confirmation testing"""

    response: Response | None = None
    soup: BeautifulSoup | None = None
    form_data: dict[str, str] = field(default_factory=dict)
    player_name: str = "TestPlayer"
    game_mode: str = "computer"

    def update_response(self, response: Response) -> None:
        """Update context with new response and parse HTML"""
        self.response = response
        self.soup = BeautifulSoup(response.text, "html.parser")


@pytest.fixture
def confirmation_context() -> StartGameConfirmationContext:
    """Provide a test context for maintaining state between BDD steps"""
    return StartGameConfirmationContext()


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture"""
    from main import app

    return TestClient(app, follow_redirects=False)


def on_start_game_confirmation_page(context: StartGameConfirmationContext) -> None:
    """Helper function to verify we're on the start game confirmation page"""
    assert context.soup is not None
    assert context.response is not None
    h1_element = context.soup.find("h1")
    assert h1_element and "Start Game Confirmation" in h1_element.get_text()
    assert context.response.status_code == 200


# === Background Steps ===


@given("I am on the start game confirmation page")
def goto_start_game_confirmation_page(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Navigate to start game confirmation page"""
    # First login to create a session
    login_response = client.post(
        "/",
        data={
            "player_name": confirmation_context.player_name,
            "game_mode": confirmation_context.game_mode,
        },
    )

    # Follow redirect if there is one
    if login_response.status_code in [302, 303]:
        redirect_url = login_response.headers.get("location")
        if redirect_url:
            response = client.get(redirect_url)
            confirmation_context.update_response(response)
    else:
        confirmation_context.update_response(login_response)


@given("the page is fully loaded")
def page_is_fully_loaded(confirmation_context: StartGameConfirmationContext) -> None:
    """Verify page is fully loaded"""
    on_start_game_confirmation_page(confirmation_context)


# === Scenario: Start game ===


@given("the game details are correct")
def game_details_are_correct(
    confirmation_context: StartGameConfirmationContext,
) -> None:
    """Verify game details are displayed correctly"""
    assert confirmation_context.soup is not None

    # Check for player name display
    player_name_element = confirmation_context.soup.find(
        attrs={"data-testid": "confirmation-player-name"}
    )
    assert player_name_element is not None
    assert confirmation_context.player_name in player_name_element.get_text()

    # Check for game mode display
    game_mode_element = confirmation_context.soup.find(
        attrs={"data-testid": "confirmation-game-mode"}
    )
    assert game_mode_element is not None


@when('I choose "Start Game"')
def choose_start_game(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Click the Start Game button"""
    # Submit form with start game action
    form_data = {
        "player_name": confirmation_context.player_name,
        "action": "start_game",
    }
    response = client.post("/start-game-confirmation", data=form_data)
    confirmation_context.update_response(response)


@then("I should be redirected to the ship placement page")
def redirected_to_ship_placement(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Verify redirect to ship placement page"""
    assert confirmation_context.response is not None
    assert confirmation_context.response.status_code == 303
    redirect_url = confirmation_context.response.headers.get("location")
    assert redirect_url is not None
    assert "ship-placement" in redirect_url or "ship_placement" in redirect_url

    # Follow the redirect and verify we arrive at ship placement page
    target_response = client.get(redirect_url)
    confirmation_context.update_response(target_response)

    assert confirmation_context.response.status_code == 200
    assert confirmation_context.soup is not None
    h1_element = confirmation_context.soup.find("h1")
    assert h1_element and "Ship Placement" in h1_element.get_text()


# === Scenario: Return to login page ===


@when('I choose "Return to Login"')
def choose_return_to_login(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Click the Return to Login button"""
    # Submit form with return to login action
    form_data = {
        "player_name": confirmation_context.player_name,
        "action": "return_to_login",
    }
    response = client.post("/start-game-confirmation", data=form_data)
    confirmation_context.update_response(response)


@then("I should be redirected to the login page")
def redirected_to_login_page(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Verify redirect to login page"""
    assert confirmation_context.response is not None
    assert confirmation_context.response.status_code == 303
    redirect_url = confirmation_context.response.headers.get("location")
    assert redirect_url is not None
    assert redirect_url == "/" or "login" in redirect_url

    # Follow the redirect and verify we arrive at login page
    target_response = client.get(redirect_url)
    confirmation_context.update_response(target_response)

    assert confirmation_context.response.status_code == 200
    assert confirmation_context.soup is not None
    h1_element = confirmation_context.soup.find("h1")
    assert h1_element and "Battleships Login" in h1_element.get_text()


# === Scenario: Exit completely ===


@when('I choose "Exit"')
def choose_exit(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Click the Exit button"""
    # Submit form with exit action
    form_data = {
        "player_name": confirmation_context.player_name,
        "action": "exit",
    }
    response = client.post("/start-game-confirmation", data=form_data)
    confirmation_context.update_response(response)


@then("I should be redirected to the goodbye page")
def redirected_to_goodbye_page(
    client: TestClient, confirmation_context: StartGameConfirmationContext
) -> None:
    """Verify redirect to goodbye page"""
    assert confirmation_context.response is not None
    assert confirmation_context.response.status_code == 303
    redirect_url = confirmation_context.response.headers.get("location")
    assert redirect_url is not None
    assert "goodbye" in redirect_url

    # Follow the redirect and verify we arrive at goodbye page
    target_response = client.get(redirect_url)
    confirmation_context.update_response(target_response)

    assert confirmation_context.response.status_code == 200
    assert confirmation_context.soup is not None
    h1_element = confirmation_context.soup.find("h1")
    assert h1_element and "Goodbye" in h1_element.get_text()
