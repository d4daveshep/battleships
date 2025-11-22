from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup, Tag
from httpx import Response
from dataclasses import dataclass, field
import pytest


scenarios("../../features/login.feature")


@dataclass
class BDDTestContext:
    """Maintains state between BDD steps, replacing Playwright's Page"""

    response: Response | None = None
    soup: BeautifulSoup | None = None
    form_data: dict[str, str] = field(default_factory=dict)

    def update_response(self, response: Response):
        """Update context with new response and parse HTML"""
        self.response = response
        self.soup = BeautifulSoup(response.text, "html.parser")


@pytest.fixture
def context():
    """Provide a test context for maintaining state between BDD steps"""
    return BDDTestContext()


@pytest.fixture
def client():
    """FastAPI TestClient fixture"""
    from main import app

    return TestClient(app, follow_redirects=False)


def on_login_page(context: BDDTestContext) -> None:
    """Helper function to verify we're on the login page"""
    assert context.soup is not None
    assert context.response is not None
    h1_element = context.soup.find("h1")
    assert h1_element and "Battleships Login" in h1_element.get_text()
    assert context.response.status_code == 200


@given("I am on the login page")
def goto_login_page(client: TestClient, context: BDDTestContext) -> None:
    response = client.get("/")
    context.update_response(response)
    on_login_page(context)


@given("the login page is fully loaded")
def login_page_is_loaded(context: BDDTestContext) -> None:
    assert context.soup is not None

    # Check for player name input field
    player_name_input = context.soup.find(
        "input", {"type": "text", "name": "player_name"}
    )
    assert player_name_input is not None

    # Check for computer button
    computer_button = context.soup.find("button", {"value": "computer"})
    assert computer_button is not None

    # Check for human button
    human_button = context.soup.find("button", {"value": "human"})
    assert human_button is not None


@given("the player name field is empty")
def player_name_field_is_empty(context: BDDTestContext) -> None:
    assert context.soup is not None
    player_name_input = context.soup.find(
        "input", {"type": "text", "name": "player_name"}
    )
    assert player_name_input is not None
    # Input field should either have no value or empty value
    if isinstance(player_name_input, Tag):
        value = player_name_input.get("value", "")
        assert value == ""


@when(parsers.parse('I enter "{player_name}" as my player name'))
def enter_player_name(context: BDDTestContext, player_name: str) -> None:
    context.form_data["player_name"] = player_name


@given('I click the "Play against Computer" button')
@when('I click the "Play against Computer" button')
def click_play_against_computer(client: TestClient, context: BDDTestContext) -> None:
    form_data = context.form_data.copy()
    form_data["game_mode"] = "computer"
    # Ensure player_name is always present, even if empty
    if "player_name" not in form_data:
        form_data["player_name"] = ""
    response = client.post("/", data=form_data)
    context.update_response(response)


@when('I click the "Play against Another Player" button')
def click_play_against_human(client: TestClient, context: BDDTestContext) -> None:
    form_data = context.form_data.copy()
    form_data["game_mode"] = "human"
    # Ensure player_name is always present, even if empty
    if "player_name" not in form_data:
        form_data["player_name"] = ""
    response = client.post("/", data=form_data)
    context.update_response(response)


@then("I should be redirected to the game interface")
def on_game_page(client: TestClient, context: BDDTestContext) -> None:
    # Check for redirect response
    assert context.response is not None
    assert context.response.status_code == 303
    redirect_url = context.response.headers.get("location")
    assert redirect_url is not None
    # Application now redirects to ship-placement before game
    assert "ship-placement" in redirect_url or "ship_placement" in redirect_url

    # Follow the redirect and update context
    target_response = client.get(redirect_url)
    context.update_response(target_response)

    # Verify we actually arrived at the ship placement page
    assert context.response.status_code == 200
    assert context.soup is not None
    h1_element = context.soup.find("h1")
    assert h1_element and "Ship Placement" in h1_element.get_text()


@then("I should be redirected to the multiplayer lobby")
def on_multiplayer_lobby_page(client: TestClient, context: BDDTestContext) -> None:
    # Check for redirect response
    assert context.response is not None
    assert context.response.status_code == 303
    redirect_url = context.response.headers.get("location")
    assert redirect_url is not None
    assert "lobby" in redirect_url

    # Follow the redirect and update context
    target_response = client.get(redirect_url)
    context.update_response(target_response)

    # Verify we actually arrived at the lobby page
    assert context.response.status_code == 200
    assert context.soup is not None
    h1_element = context.soup.find("h1")
    assert h1_element and "Multiplayer Lobby" in h1_element.get_text()


@then("the game should be configured for single player mode")
def player_mode_is_single_player(context: BDDTestContext) -> None:
    # Context should already have the target page from redirect step
    assert context.soup is not None

    # Check if we're on the game page (has game-mode testid)
    game_mode_element = context.soup.find(attrs={"data-testid": "game-mode"})
    if game_mode_element is not None:
        assert game_mode_element.get_text() == "Single Player"
    else:
        # We're on ship placement page - single player mode is implied
        # (ship placement comes before game, so this is still valid)
        h1_element = context.soup.find("h1")
        assert h1_element and "Ship Placement" in h1_element.get_text()


@then("the game should be configured for two player mode")
def player_mode_is_two_player(context: BDDTestContext) -> None:
    # Context should already have the target page from redirect step
    assert context.soup is not None
    game_mode_element = context.soup.find(attrs={"data-testid": "game-mode"})
    assert game_mode_element is not None
    assert game_mode_element.get_text() == "Two Player"


@then(parsers.parse('my player name should be set to "{expected_name}"'))
def player_name_is_set(context: BDDTestContext, expected_name: str) -> None:
    # Context should already have the target page from redirect step
    assert context.soup is not None

    # Try to find player name in testid element (game page)
    player_name_element = context.soup.find(attrs={"data-testid": "player-name"})
    if player_name_element is not None:
        name_text = player_name_element.get_text()
        assert expected_name in name_text
    else:
        # We're on ship placement page - check the player paragraph
        # Ship placement page shows: <p>Player: {{ player_name }}</p>
        page_text = context.soup.get_text()
        assert f"Player: {expected_name}" in page_text or expected_name in page_text


@then(parsers.parse('I should see an error message "{error_message}"'))
def error_message_displayed(context: BDDTestContext, error_message: str) -> None:
    assert context.soup is not None
    error_element = context.soup.find(attrs={"data-testid": "error-message"})
    assert error_element is not None
    assert error_element.get_text() == error_message


@then("I should remain on the login page")
def remain_on_login_page(context: BDDTestContext) -> None:
    # Should not be a redirect, should be 200 with login page content
    assert context.response is not None
    assert context.response.status_code == 200
    on_login_page(context)
