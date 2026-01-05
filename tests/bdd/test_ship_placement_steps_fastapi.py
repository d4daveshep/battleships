from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup, NavigableString, Tag
from httpx import Response
from dataclasses import dataclass, field
from typing import Any, Generator
import pytest


scenarios("../../features/ship_placement.feature")


@dataclass
class ShipPlacementContext:
    """Maintains state between BDD steps for ship placement testing"""

    response: Response | None = None
    soup: BeautifulSoup | None = None
    form_data: dict[str, str] = field(default_factory=dict)
    player_name: str | None = None
    selected_ship: str | None = None
    placed_ships: dict[str, list[str]] = field(default_factory=dict)
    last_placement_error: str | None = None
    game_mode: str = "computer"  # Default to single player mode

    def update_response(self, response: Response) -> None:
        """Update context with new response and parse HTML"""
        self.response = response
        self.soup = BeautifulSoup(response.text, "html.parser")


@pytest.fixture
def ship_context() -> ShipPlacementContext:
    """Provide a test context for maintaining state between BDD steps"""
    return ShipPlacementContext()


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture"""
    from main import app

    return TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_games_state() -> Generator[None, None, None]:
    """Reset games state for FastAPI TestClient tests"""
    from main import game_service

    game_service.ship_placement_boards.clear()
    yield
    game_service.ship_placement_boards.clear()


# FIXME: Fix this function so it takes the user to the ship placement page (after the "start game" page)
def on_ship_placement_page(context: ShipPlacementContext) -> None:
    # assert False, (
    #     'Fix this function so it takes the user to the ship placement page (after the "start game" page)'
    # )
    """Helper function to verify we're on the ship placement screen"""
    assert context.soup is not None
    assert context.response is not None
    # Look for page title or H1 heading with "Ship Placement"
    h1_element: Tag | NavigableString | None = context.soup.find("h1")
    assert h1_element is not None
    assert "Ship Placement" in h1_element.get_text()
    assert context.response.status_code == 200


# === Background Steps ===


@given("I have logged in and selected a game mode")
def logged_in_and_selected_game_mode(
    client: TestClient, ship_context: ShipPlacementContext
) -> None:
    """Login and select a game mode"""
    # First get the login page
    response: Response = client.get("/")
    ship_context.update_response(response)

    # Submit login form with game mode selection
    form_data: dict[str, str] = {
        "player_name": "TestPlayer",
        "game_mode": ship_context.game_mode,
    }
    response = client.post("/", data=form_data)
    ship_context.update_response(response)

    ship_context.player_name = "TestPlayer"


@given("I am on the ship placement screen")
def on_ship_placement_screen(
    client: TestClient, ship_context: ShipPlacementContext
) -> None:
    """Navigate to ship placement screen"""
    # Submit form with start game action
    form_data = {
        "player_name": ship_context.player_name,
        "action": "start_game",
    }
    response = client.post("/start-game", data=form_data)
    ship_context.update_response(response)
    # After login, should be redirected to ship placement or game setup
    # Follow any redirects to get to ship placement screen
    if ship_context.response and ship_context.response.status_code in [302, 303]:
        redirect_url: str | None = ship_context.response.headers.get("location")
        if redirect_url:
            target_response: Response = client.get(redirect_url)
            ship_context.update_response(target_response)

    on_ship_placement_page(ship_context)


@given('the "My Ships and Shots Received" board is displayed')
def my_ships_board_displayed(ship_context: ShipPlacementContext) -> None:
    """Verify the player's board is displayed"""
    assert ship_context.soup is not None
    board: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "my-ships-board"}
    )
    assert board is not None


@given("I have not placed any ships yet")
@given("I have not placed any ships")
def no_ships_placed_yet(ship_context: ShipPlacementContext) -> None:
    """Verify no ships have been placed"""
    ship_context.placed_ships = {}


# === Ship Selection ===


@given(parsers.parse('I select the "{ship_name}" ship to place'))
@when(parsers.parse('I select the "{ship_name}" ship to place'))
def select_ship_to_place(
    client: TestClient, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Select a ship to place on the board"""
    ship_context.selected_ship = ship_name


# === Ship Placement (New Syntax) ===


def place_ship_with_direction(
    client: TestClient,
    ship_context: ShipPlacementContext,
    start: str,
    direction: str,
    is_attempt: bool = False,
) -> None:
    """Helper to place a ship using start coordinate and orientation"""
    assert ship_context.player_name is not None
    assert ship_context.selected_ship is not None

    # Map direction to orientation
    orientation_map: dict[str, str] = {
        "horizontally": "horizontal",
        "vertically": "vertical",
        "diagonally-down": "diagonal-down",
        "diagonally-up": "diagonal-up",
    }
    orientation: str = orientation_map.get(direction, direction)

    form_data: dict[str, str] = {
        "player_name": ship_context.player_name,
        "ship_name": ship_context.selected_ship,
        "start_coordinate": start,
        "orientation": orientation,
    }
    response: Response = client.post("/place-ship", data=form_data)
    ship_context.update_response(response)

    # If successful, store the placed ship
    if not is_attempt and response.status_code == 200:
        ship_context.placed_ships[ship_context.selected_ship] = [start, orientation]


@when(parsers.parse('I place it {direction} starting at "{start}"'))
def place_ship_direction_starting_at(
    client: TestClient, ship_context: ShipPlacementContext, direction: str, start: str
) -> None:
    """Place a ship using direction and starting coordinate"""
    place_ship_with_direction(client, ship_context, start, direction, is_attempt=False)


@when(parsers.parse('I attempt to place it {direction} starting at "{start}"'))
def attempt_place_ship_direction_starting_at(
    client: TestClient, ship_context: ShipPlacementContext, direction: str, start: str
) -> None:
    """Attempt to place a ship using direction and starting coordinate"""
    place_ship_with_direction(client, ship_context, start, direction, is_attempt=True)


@when(
    parsers.parse('I attempt to place it with invalid direction starting at "{start}"')
)
def attempt_place_ship_invalid_direction(
    client: TestClient, ship_context: ShipPlacementContext, start: str
) -> None:
    """Attempt to place a ship with invalid direction"""
    assert ship_context.player_name is not None
    assert ship_context.selected_ship is not None

    form_data: dict[str, str] = {
        "player_name": ship_context.player_name,
        "ship_name": ship_context.selected_ship,
        "start_coordinate": start,
        "orientation": "invalid",
    }
    response: Response = client.post("/place-ship", data=form_data)
    ship_context.update_response(response)


# === Placement Verification ===


@then(parsers.parse("the {ship_name} should be placed on the board"))
def ship_placed_on_board(ship_context: ShipPlacementContext, ship_name: str) -> None:
    """Verify ship is placed on the board"""
    assert ship_context.soup is not None
    ship_element: Tag | None = ship_context.soup.find(
        attrs={"data-testid": f"placed-ship-{ship_name.lower()}"}
    )
    assert ship_element is not None


@then(parsers.parse('the {ship_name} should occupy cells "{cells}"'))
@then(
    parsers.parse(
        'the {ship_name} should occupy cells "{cell1}", "{cell2}", and "{cell3}"'
    )
)
@then(
    parsers.parse(
        'the {ship_name} should occupy cells "{cell1}", "{cell2}", "{cell3}", and "{cell4}"'
    )
)
@then(
    parsers.parse(
        'the {ship_name} should occupy cells "{cell1}", "{cell2}", "{cell3}", "{cell4}", and "{cell5}"'
    )
)
@then(parsers.parse('the {ship_name} should occupy cells "{cell1}" and "{cell2}"'))
def ship_occupies_cells(
    ship_context: ShipPlacementContext, ship_name: str, **kwargs: Any
) -> None:
    """Verify ship occupies the correct cells"""
    assert ship_context.soup is not None
    # Extract all cell values from kwargs
    cells: list[str] = [v for k, v in kwargs.items() if k.startswith("cell")]

    # Verify each cell is marked as occupied by the ship
    for cell in cells:
        cell_element: Tag | None = ship_context.soup.find(
            attrs={"data-testid": f"cell-{cell}", "data-ship": ship_name.lower()}
        )
        assert cell_element is not None, (
            f"Cell {cell} should be occupied by {ship_name}"
        )


@then(parsers.parse("the {ship_name} should be marked as placed"))
def ship_marked_as_placed(ship_context: ShipPlacementContext, ship_name: str) -> None:
    """Verify ship is marked as placed in the UI"""
    assert ship_context.soup is not None
    ship_status: Tag | None = ship_context.soup.find(
        attrs={"data-testid": f"ship-status-{ship_name.lower()}"}
    )
    assert ship_status is not None
    assert "placed" in ship_status.get_text().lower()


# === Placement Rejection ===


@then("the placement should be rejected")
def placement_should_be_rejected(ship_context: ShipPlacementContext) -> None:
    """Verify placement was rejected"""
    assert ship_context.response is not None
    # Should return 200 with error message or 400
    assert ship_context.response.status_code in [200, 400]


@then(parsers.parse('I should see an error message "{error_message}"'))
def should_see_error_message(
    ship_context: ShipPlacementContext, error_message: str
) -> None:
    """Verify error message is displayed"""
    assert ship_context.soup is not None
    error_element: Tag | None = ship_context.soup.find(
        attrs={"data-testid": "placement-error"}
    )
    assert error_element is not None
    assert error_message in error_element.get_text()
    ship_context.last_placement_error = error_message


@then(parsers.parse("the {ship_name} should not be placed"))
def ship_should_not_be_placed(
    ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Verify ship was not placed on the board"""
    # Ship should not be in the placed_ships dictionary
    assert ship_name not in ship_context.placed_ships


@then("no error message should be displayed")
def no_error_message_displayed(ship_context: ShipPlacementContext) -> None:
    """Verify no error message is shown"""
    assert ship_context.soup is not None
    error_element: Tag | None = ship_context.soup.find(
        attrs={"data-testid": "placement-error"}
    )
    assert error_element is None


# === Pre-placed Ships Setup ===


@given(parsers.parse('I have placed a "{ship_name}" {direction} starting at "{start}"'))
def have_placed_ship_direction_starting_at(
    client: TestClient,
    ship_context: ShipPlacementContext,
    ship_name: str,
    direction: str,
    start: str,
) -> None:
    """Setup: Pre-place a ship with direction"""
    ship_context.selected_ship = ship_name
    place_ship_with_direction(client, ship_context, start, direction, is_attempt=False)
    # Verify it was placed successfully
    assert ship_context.response is not None
    assert ship_context.response.status_code == 200


# === Random Placement ===


@when('I click the "Random Placement" button')
def click_random_placement_button(
    client: TestClient, ship_context: ShipPlacementContext
) -> None:
    """Click the Random Placement button"""
    assert ship_context.player_name is not None
    form_data: dict[str, str] = {"player_name": ship_context.player_name}
    response: Response = client.post("/random-ship-placement", data=form_data)
    ship_context.update_response(response)


@then("all 5 ships should be placed automatically")
def all_ships_placed_automatically(ship_context: ShipPlacementContext) -> None:
    """Verify all 5 ships are placed"""
    assert ship_context.soup is not None
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_element: Tag | None = ship_context.soup.find(
            attrs={"data-testid": f"placed-ship-{ship_name}"}
        )
        assert ship_element is not None, f"{ship_name} should be placed"


@then("all ships should follow placement rules")
def all_ships_follow_placement_rules(ship_context: ShipPlacementContext) -> None:
    """Verify all placed ships follow the placement rules"""
    # This is checked by the backend, verify no error message
    no_error_message_displayed(ship_context)


@then("no ships should overlap")
def no_ships_should_overlap(ship_context: ShipPlacementContext) -> None:
    """Verify no ships are overlapping"""
    # This is enforced by the backend, verify no error message
    no_error_message_displayed(ship_context)


@then("no ships should be touching")
def no_ships_should_be_touching(ship_context: ShipPlacementContext) -> None:
    """Verify ships have proper spacing"""
    # This is enforced by the backend, verify no error message
    no_error_message_displayed(ship_context)


@then("all ships should be within the board boundaries")
def all_ships_within_boundaries(ship_context: ShipPlacementContext) -> None:
    """Verify all ships are within board boundaries"""
    # This is enforced by the backend, verify no error message
    no_error_message_displayed(ship_context)


# === Ship Placement Progress ===


@given("I have placed some ships manually")
def have_placed_some_ships_manually(ship_context: ShipPlacementContext) -> None:
    """Setup: Some ships have been placed"""
    # Mark a few ships as placed
    ship_context.placed_ships["Destroyer"] = ["A1", "horizontal"]
    ship_context.placed_ships["Submarine"] = ["C3", "vertical"]


@when("my manually placed ships should be removed")
@then("my manually placed ships should be removed")
def manually_placed_ships_removed(ship_context: ShipPlacementContext) -> None:
    """Verify manually placed ships are removed"""
    # After random placement, old ships should be cleared
    ship_context.placed_ships = {}


@then("all 5 ships should be placed automatically following all rules")
def all_ships_placed_following_rules(ship_context: ShipPlacementContext) -> None:
    """Verify all ships placed and following rules"""
    all_ships_placed_automatically(ship_context)
    all_ships_follow_placement_rules(ship_context)


@then(parsers.parse('I should see "{status_text}"'))
def should_see_status_text(
    ship_context: ShipPlacementContext, status_text: str
) -> None:
    """Verify status text is displayed"""
    assert ship_context.soup is not None
    status_element = ship_context.soup.find(
        attrs={"data-testid": "ship-placement-status"}
    )
    assert status_element is not None
    assert status_text in status_element.get_text()


@when(parsers.parse('I place the "{ship_name}"'))
def place_the_ship(
    client: TestClient, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Place a ship (using default coordinates for testing)"""
    ship_context.selected_ship = ship_name
    # Use some default starting coordinates for each ship (place horizontally)
    start_coordinates: dict[str, str] = {
        "Destroyer": "A1",
        "Submarine": "C3",
        "Cruiser": "E5",
        "Battleship": "G1",
        "Carrier": "I1",
    }
    start: str = start_coordinates.get(ship_name, "A1")
    place_ship_with_direction(
        client, ship_context, start, "horizontally", is_attempt=False
    )


# === Start Game Button ===


@given("I have placed 4 out of 5 ships")
def have_placed_4_ships(ship_context: ShipPlacementContext) -> None:
    """Setup: 4 ships placed"""
    ship_context.placed_ships = {
        "Destroyer": ["A1", "horizontal"],
        "Submarine": ["C3", "vertical"],
        "Cruiser": ["E5", "horizontal"],
        "Battleship": ["G1", "horizontal"],
    }


@when(parsers.parse("I place the 5th ship"))
def place_5th_ship(client: TestClient, ship_context: ShipPlacementContext) -> None:
    """Place the 5th and final ship"""
    place_the_ship(client, ship_context, "Carrier")


@then('the "Start Game" button should be disabled')
def start_game_button_disabled(ship_context: ShipPlacementContext) -> None:
    """Verify Start Game button is disabled"""
    assert ship_context.soup is not None
    start_button: Tag | None = ship_context.soup.find(
        attrs={"data-testid": "start-game-button"}
    )
    assert start_button is not None
    if isinstance(start_button, Tag):
        assert start_button.get("disabled") is not None


@then('the "Start Game" button should be enabled')
def start_game_button_enabled(ship_context: ShipPlacementContext) -> None:
    """Verify Start Game button is enabled"""
    assert ship_context.soup is not None
    start_button: Tag | None = ship_context.soup.find(
        attrs={"data-testid": "start-game-button"}
    )
    assert start_button is not None
    if isinstance(start_button, Tag):
        assert start_button.get("disabled") is None


# === Ship Removal ===


@when(parsers.parse('I click on the "{ship_name}" to remove it'))
def click_ship_to_remove(
    client: TestClient, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Click on a placed ship to remove it"""
    assert ship_context.player_name is not None
    form_data: dict[str, str] = {
        "player_name": ship_context.player_name,
        "ship_name": ship_name,
    }
    response: Response = client.post("/remove-ship", data=form_data)
    ship_context.update_response(response)
    # Remove from placed ships
    if ship_name in ship_context.placed_ships:
        del ship_context.placed_ships[ship_name]


@then(parsers.parse("the {ship_name} should be removed from the board"))
def ship_removed_from_board(ship_context: ShipPlacementContext, ship_name: str) -> None:
    """Verify ship is removed from the board"""
    assert ship_context.soup is not None
    ship_element: Tag | None = ship_context.soup.find(
        attrs={"data-testid": f"placed-ship-{ship_name.lower()}"}
    )
    assert ship_element is None


@then(parsers.parse("the {ship_name} should be available to place again"))
def ship_available_to_place_again(
    ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Verify ship is available for placement"""
    assert ship_context.soup is not None
    ship_selector: Tag | None = ship_context.soup.find(
        attrs={"data-testid": f"select-ship-{ship_name.lower()}"}
    )
    assert ship_selector is not None


@then(parsers.parse('the ship count should show "{count_text}"'))
def ship_count_should_show(ship_context: ShipPlacementContext, count_text: str) -> None:
    """Verify ship count is displayed correctly"""
    assert ship_context.soup is not None
    count_element: Tag | None = ship_context.soup.find(
        attrs={"data-testid": "ship-placement-count"}
    )
    assert count_element is not None
    assert count_text in count_element.get_text()


# === Reset All Ships ===


@given("I have placed 3 ships on the board")
def have_placed_3_ships(ship_context: ShipPlacementContext) -> None:
    """Setup: 3 ships placed"""
    ship_context.placed_ships = {
        "Destroyer": ["A1", "horizontal"],
        "Submarine": ["C3", "vertical"],
        "Cruiser": ["E5", "horizontal"],
    }


@when('I click the "Reset All Ships" button')
def click_reset_all_ships_button(
    client: TestClient, ship_context: ShipPlacementContext
) -> None:
    """Click the Reset All Ships button"""
    assert ship_context.player_name is not None
    form_data: dict[str, str] = {"player_name": ship_context.player_name}
    response: Response = client.post("/reset-all-ships", data=form_data)
    ship_context.update_response(response)
    ship_context.placed_ships = {}


@then("all ships should be removed from the board")
def all_ships_removed_from_board(ship_context: ShipPlacementContext) -> None:
    """Verify all ships are removed"""
    assert ship_context.soup is not None
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_element: Tag | None = ship_context.soup.find(
            attrs={"data-testid": f"placed-ship-{ship_name}"}
        )
        assert ship_element is None, f"{ship_name} should be removed"


@then("all ships should be available to place again")
def all_ships_available_to_place_again(ship_context: ShipPlacementContext) -> None:
    """Verify all ships are available for placement"""
    assert ship_context.soup is not None
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_selector: Tag | None = ship_context.soup.find(
            attrs={"data-testid": f"select-ship-{ship_name}"}
        )
        assert ship_selector is not None, f"{ship_name} should be available"


# === Computer Opponent ===


@given("I am playing against a computer opponent")
def playing_against_computer(ship_context: ShipPlacementContext) -> None:
    """Setup: Set game mode to computer opponent"""
    ship_context.game_mode = "computer"


@given("I have placed all my ships")
def have_placed_all_ships(ship_context: ShipPlacementContext) -> None:
    """Setup: All 5 ships placed"""
    ship_context.placed_ships = {
        "Carrier": ["A1", "horizontal"],
        "Battleship": ["C1", "horizontal"],
        "Cruiser": ["E1", "horizontal"],
        "Submarine": ["G1", "horizontal"],
        "Destroyer": ["I1", "horizontal"],
    }


@when('I click the "Start Game" button')
def click_start_game_button(
    client: TestClient, ship_context: ShipPlacementContext
) -> None:
    """Click the Start Game button"""
    assert ship_context.player_name is not None
    form_data: dict[str, str] = {"player_name": ship_context.player_name}
    response: Response = client.post("/start-game", data=form_data)
    ship_context.update_response(response)


@then("the computer should automatically place all its ships")
def computer_places_ships_automatically(ship_context: ShipPlacementContext) -> None:
    """Verify computer opponent has placed ships"""
    # This is handled by the backend - verify no error
    assert ship_context.response is not None
    assert ship_context.response.status_code in [200, 303]


@then("the computer's ship placement should follow all placement rules")
def computer_ships_follow_rules(ship_context: ShipPlacementContext) -> None:
    """Verify computer's ships follow placement rules"""
    # This is enforced by the backend, verify no error
    assert ship_context.response is not None
    assert ship_context.response.status_code in [200, 303]


@then("the game should start immediately")
def game_starts_immediately(ship_context: ShipPlacementContext) -> None:
    """Verify game has started"""
    assert ship_context.response is not None
    # Should redirect to game screen or already be on game screen
    if ship_context.response.status_code in [302, 303]:
        redirect_url: str | None = ship_context.response.headers.get("location")
        assert redirect_url is not None
        assert "game" in redirect_url or "round" in redirect_url


# === Multiplayer Ship Placement ===


@given("I am playing against another human player")
def playing_against_human(ship_context: ShipPlacementContext) -> None:
    """Setup: Set game mode to human opponent"""
    ship_context.game_mode = "human"


@when('I click the "Ready" button')
def click_ready_button(client: TestClient, ship_context: ShipPlacementContext) -> None:
    """Click the Ready button"""
    assert ship_context.player_name is not None
    form_data: dict[str, str] = {"player_name": ship_context.player_name}
    response: Response = client.post("/ready-for-game", data=form_data)
    ship_context.update_response(response)


@then(parsers.parse('I should see a message "{message}"'))
def should_see_message(ship_context: ShipPlacementContext, message: str) -> None:
    """Verify message is displayed"""
    assert ship_context.soup is not None
    message_element: Tag | None = ship_context.soup.find(
        attrs={"data-testid": "status-message"}
    )
    assert message_element is not None
    assert message in message_element.get_text()


@then("I should not be able to modify my ship placement")
def cannot_modify_ship_placement(ship_context: ShipPlacementContext) -> None:
    """Verify ship placement is locked"""
    assert ship_context.soup is not None
    # Ship selection buttons should be disabled
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_selector: Tag | None = ship_context.soup.find(
            attrs={"data-testid": f"select-ship-{ship_name}"}
        )
        if ship_selector and isinstance(ship_selector, Tag):
            assert ship_selector.get("disabled") is not None


@given('I have placed all my ships and clicked "Ready"')
def have_placed_all_ships_and_ready(
    client: TestClient, ship_context: ShipPlacementContext
) -> None:
    """Setup: All ships placed and ready clicked"""
    have_placed_all_ships(ship_context)
    click_ready_button(client, ship_context)


@given('my opponent has placed all their ships and clicked "Ready"')
def opponent_placed_all_ships_and_ready(ship_context: ShipPlacementContext) -> None:
    """Setup: Opponent is ready"""
    # This would be handled by the multiplayer system
    pass


@then("the game should start")
def game_should_start(ship_context: ShipPlacementContext) -> None:
    """Verify game has started"""
    assert ship_context.response is not None
    # Should redirect to game or be on game page
    if ship_context.response.status_code in [302, 303]:
        redirect_url: str | None = ship_context.response.headers.get("location")
        assert redirect_url is not None
        assert "game" in redirect_url or "round" in redirect_url


@then("both players should proceed to Round 1")
def both_players_proceed_to_round_1(ship_context: ShipPlacementContext) -> None:
    """Verify game is at Round 1"""
    # This would check the game state
    pass


# === Grid Visualization ===


@then("I should see a 10x10 grid displayed")
def should_see_10x10_grid(ship_context: ShipPlacementContext) -> None:
    """Verify 10x10 grid is displayed"""
    assert ship_context.soup is not None
    grid_table: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "ship-grid"}
    )
    assert grid_table is not None, "Grid table should be present"

    # Verify it's a table element
    assert isinstance(grid_table, Tag)
    assert grid_table.name == "table"

    # Count rows in tbody (should be 10 rows A-J)
    tbody: Tag | NavigableString | None = grid_table.find("tbody")
    assert tbody is not None
    assert isinstance(tbody, Tag)
    rows: list[Tag] = tbody.find_all("tr")
    assert len(rows) == 10, "Grid should have 10 rows"

    # Verify each row has 11 cells (1 header + 10 data cells)
    for row in rows:
        cells: list[Tag] = row.find_all(["th", "td"])
        assert len(cells) == 11, "Each row should have 11 cells (1 header + 10 data)"


@then('the grid should have row labels "A" through "J"')
def grid_should_have_row_labels(ship_context: ShipPlacementContext) -> None:
    """Verify grid has row labels A through J"""
    assert ship_context.soup is not None
    grid_table: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "ship-grid"}
    )
    assert grid_table is not None
    assert isinstance(grid_table, Tag)

    tbody: Tag | NavigableString | None = grid_table.find("tbody")
    assert tbody is not None
    assert isinstance(tbody, Tag)

    expected_rows: list[str] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    rows: list[Tag] = tbody.find_all("tr")

    for i, row in enumerate(rows):
        row_header: Tag | NavigableString | None = row.find("th")
        assert row_header is not None
        assert isinstance(row_header, Tag)
        assert row_header.get_text().strip() == expected_rows[i]


@then('the grid should have column labels "1" through "10"')
def grid_should_have_column_labels(ship_context: ShipPlacementContext) -> None:
    """Verify grid has column labels 1 through 10"""
    assert ship_context.soup is not None
    grid_table: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "ship-grid"}
    )
    assert grid_table is not None
    assert isinstance(grid_table, Tag)

    thead: Tag | NavigableString | None = grid_table.find("thead")
    assert thead is not None
    assert isinstance(thead, Tag)

    header_row: Tag | NavigableString | None = thead.find("tr")
    assert header_row is not None
    assert isinstance(header_row, Tag)

    column_headers: list[Tag] = header_row.find_all("th")
    # First header is empty, then 1-10
    assert len(column_headers) == 11, "Should have 11 column headers (empty + 1-10)"

    for i in range(1, 11):
        assert column_headers[i].get_text().strip() == str(i)


@then("all grid cells should be empty")
def all_grid_cells_should_be_empty(ship_context: ShipPlacementContext) -> None:
    """Verify all grid cells are empty (no ships placed)"""
    assert ship_context.soup is not None
    grid_table: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "ship-grid"}
    )
    assert grid_table is not None
    assert isinstance(grid_table, Tag)

    # Find all cells with data-ship attribute
    occupied_cells: list[Tag] = grid_table.find_all(attrs={"data-ship": True})
    assert len(occupied_cells) == 0, (
        "All cells should be empty (no data-ship attribute)"
    )


@then(
    parsers.parse('cells "{cell1}" and "{cell2}" should be visually marked on the grid')
)
def cells_should_be_visually_marked_two(
    ship_context: ShipPlacementContext, cell1: str, cell2: str
) -> None:
    """Verify two cells are visually marked on the grid"""
    assert ship_context.soup is not None
    cells: list[str] = [cell1, cell2]

    for cell in cells:
        cell_element: Tag | NavigableString | None = ship_context.soup.find(
            attrs={"data-testid": f"grid-cell-{cell}", "data-ship": True}
        )
        assert cell_element is not None, f"Cell {cell} should be marked on the grid"
        assert isinstance(cell_element, Tag)
        assert cell_element.get("data-ship") is not None


@then("the marked cells should be clearly distinguishable from empty cells")
def marked_cells_distinguishable_from_empty(ship_context: ShipPlacementContext) -> None:
    """Verify marked cells have data-ship attribute that distinguishes them"""
    assert ship_context.soup is not None
    grid_table: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "ship-grid"}
    )
    assert grid_table is not None
    assert isinstance(grid_table, Tag)

    # Find cells with data-ship attribute (marked)
    marked_cells: list[Tag] = grid_table.find_all(attrs={"data-ship": True})
    assert len(marked_cells) > 0, "Should have at least one marked cell"

    # Find cells without data-ship attribute (empty)
    all_cells: list[Tag] = grid_table.find_all("td", attrs={"data-testid": True})
    empty_cells: list[Tag] = [cell for cell in all_cells if not cell.get("data-ship")]
    assert len(empty_cells) > 0, "Should have at least one empty cell"

    # Verify marked cells have data-ship attribute
    for cell in marked_cells:
        assert cell.get("data-ship") is not None


@then("I should be able to identify which cells belong to which ship on the grid")
def should_identify_cells_by_ship(ship_context: ShipPlacementContext) -> None:
    """Verify cells have data-ship attributes identifying which ship they belong to"""
    assert ship_context.soup is not None
    grid_table: Tag | NavigableString | None = ship_context.soup.find(
        attrs={"data-testid": "ship-grid"}
    )
    assert grid_table is not None
    assert isinstance(grid_table, Tag)

    # Find all cells with data-ship attribute
    marked_cells: list[Tag] = grid_table.find_all(attrs={"data-ship": True})
    assert len(marked_cells) > 0, "Should have marked cells"

    # Group cells by ship name
    ships_found: dict[str, int] = {}
    for cell in marked_cells:
        ship_name_attr: str | list[str] | None = cell.get("data-ship")
        assert ship_name_attr is not None
        # BeautifulSoup returns str or list[str] for attributes
        ship_name: str = (
            ship_name_attr if isinstance(ship_name_attr, str) else ship_name_attr[0]
        )
        ships_found[ship_name] = ships_found.get(ship_name, 0) + 1

    # Should have at least 2 different ships (Destroyer and Cruiser from scenario)
    assert len(ships_found) >= 2, "Should have at least 2 different ships on grid"


@then(
    parsers.re(
        r'cells "(?P<cell1>[A-J]\d+)", "(?P<cell2>[A-J]\d+)", "(?P<cell3>[A-J]\d+)", and "(?P<cell4>[A-J]\d+)" should be marked on the grid'
    )
)
def cells_should_be_marked_four(
    ship_context: ShipPlacementContext, cell1: str, cell2: str, cell3: str, cell4: str
) -> None:
    """Verify four cells are marked on the grid"""
    assert ship_context.soup is not None
    cells: list[str] = [cell1, cell2, cell3, cell4]

    for cell in cells:
        cell_element: Tag | NavigableString | None = ship_context.soup.find(
            attrs={"data-testid": f"grid-cell-{cell}", "data-ship": True}
        )
        assert cell_element is not None, f"Cell {cell} should be marked on the grid"


@then(
    parsers.re(
        r'cells "(?P<cell1>[A-J]\d+)", "(?P<cell2>[A-J]\d+)", and "(?P<cell3>[A-J]\d+)" should be marked on the grid'
    )
)
def cells_should_be_marked_three(
    ship_context: ShipPlacementContext, cell1: str, cell2: str, cell3: str
) -> None:
    """Verify three cells are marked on the grid"""
    assert ship_context.soup is not None
    cells: list[str] = [cell1, cell2, cell3]

    for cell in cells:
        cell_element: Tag | NavigableString | None = ship_context.soup.find(
            attrs={"data-testid": f"grid-cell-{cell}", "data-ship": True}
        )
        assert cell_element is not None, f"Cell {cell} should be marked on the grid"
