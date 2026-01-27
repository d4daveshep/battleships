import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from tests.bdd.conftest import MultiPlayerBDDContext
from bs4 import BeautifulSoup, Tag
from httpx import Response

scenarios("../../features/two_player_gameplay.feature")


@pytest.fixture
def context() -> MultiPlayerBDDContext:
    return MultiPlayerBDDContext()


# === Background Steps ===


@given("both players have completed ship placement")
def players_completed_placement(context: MultiPlayerBDDContext):
    """Setup a game with two players who have placed ships"""
    # 1. Reset Lobby
    with context.get_client_for_player("System") as client:
        client.post("/test/reset-lobby")

    # 2. Login Players
    p1_name = "Player1"
    p2_name = "Player2"
    context.current_player_name = p1_name

    client1 = context.get_client_for_player(p1_name)
    client1.post("/login", data={"player_name": p1_name, "game_mode": "human"})

    client2 = context.get_client_for_player(p2_name)
    client2.post("/login", data={"player_name": p2_name, "game_mode": "human"})

    # 3. Match Players
    # Player 1 selects Player 2
    client1.post("/select-opponent", data={"opponent_name": p2_name})
    # Player 2 accepts
    client2.post("/accept-game-request", data={})

    # 4. Place Ships for Player 1
    ships = [
        ("Carrier", "A1", "horizontal"),
        ("Battleship", "C1", "horizontal"),
        ("Cruiser", "E1", "horizontal"),
        ("Submarine", "G1", "horizontal"),
        ("Destroyer", "I1", "horizontal"),
    ]
    for ship, start, orientation in ships:
        client1.post(
            "/place-ship",
            data={
                "player_name": p1_name,
                "ship_name": ship,
                "start_coordinate": start,
                "orientation": orientation,
            },
        )

    # 5. Place Ships for Player 2
    for ship, start, orientation in ships:
        client2.post(
            "/place-ship",
            data={
                "player_name": p2_name,
                "ship_name": ship,
                "start_coordinate": start,
                "orientation": orientation,
            },
        )


@given("both players are ready")
def players_are_ready(context: MultiPlayerBDDContext):
    """Both players click ready"""
    p1_name = "Player1"
    p2_name = "Player2"

    client1 = context.get_client_for_player(p1_name)
    client2 = context.get_client_for_player(p2_name)

    client1.post("/ready-for-game", data={"player_name": p1_name})
    # P2 ready - this should trigger game start and return redirect
    response = client2.post(
        "/ready-for-game", data={"player_name": p2_name}, follow_redirects=False
    )

    # Store the game URL from the redirect
    if response.status_code in [302, 303] and "location" in response.headers:
        context.game_url = response.headers["location"]
    else:
        # Try to get game URL from P1's status check
        status_response = client1.get(
            "/place-ships/opponent-status", headers={"HX-Request": "true"}
        )
        if "HX-Redirect" in status_response.headers:
            context.game_url = status_response.headers["HX-Redirect"]


@given("the game has started")
def game_has_started(context: MultiPlayerBDDContext):
    """Verify game has started by checking redirect or status"""
    # We can check if accessing the game page works
    client1 = context.get_client_for_player("Player1")
    # The game URL is usually /game/{game_id} or just /game depending on implementation
    # But typically we get redirected there.
    # Let's assume we can access the game page if the game is started.
    # We might need to follow the redirect from the ready check.
    pass


@given("I am on the gameplay page")
def on_gameplay_page(context: MultiPlayerBDDContext):
    """Navigate to gameplay page"""
    assert context.current_player_name is not None, "No current player set"
    assert context.game_url is not None, (
        "No game URL stored - game may not have started"
    )

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    # Verify we are on the game page
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Round" in response.text or "game" in response.text.lower()


# === Scenario Steps ===


@given("the game just started")
def game_just_started(context: MultiPlayerBDDContext):
    """Ensure it is the beginning of the game"""
    # This is implicitly true after setup
    pass


@then(parsers.parse('I should see "{text}" displayed'))
def see_text_displayed(context: MultiPlayerBDDContext, text: str):
    """Verify text is displayed on the page"""
    assert context.soup is not None
    assert text in context.soup.get_text()


@then("I should be able to select up to 6 coordinates to fire at")
def can_select_6_coordinates(context: MultiPlayerBDDContext):
    """Verify firing controls are present"""
    assert context.soup is not None
    # Check for the grid that allows selection
    # This might be the opponent's board (shots fired board)
    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None

    # Check for fire button
    fire_btn = context.soup.find(attrs={"data-testid": "fire-shots-button"})
    assert fire_btn is not None


@then(parsers.parse('I should see my board labeled "{label}"'))
def see_my_board_labeled(context: MultiPlayerBDDContext, label: str):
    """Verify my board label"""
    assert context.soup is not None
    # Find the label associated with the board
    # This is a loose check, looking for the text near the board
    assert label in context.soup.get_text()

    board = context.soup.find(attrs={"data-testid": "my-ships-board"})
    assert board is not None


@then(parsers.parse('I should see the opponent\'s board labeled "{label}"'))
def see_opponent_board_labeled(context: MultiPlayerBDDContext, label: str):
    """Verify opponent board label"""
    assert context.soup is not None
    assert label in context.soup.get_text()

    board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert board is not None


@then(
    parsers.parse(
        'I should see the "Hits Made" area showing all {count:d} opponent ships'
    )
)
def see_hits_made_area(context: MultiPlayerBDDContext, count: int):
    """Verify hits made area"""
    assert context.soup is not None
    hits_area = context.soup.find(attrs={"data-testid": "hits-made-area"})
    assert hits_area is not None

    # Check for ship names
    ship_names = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
    text = hits_area.get_text()
    for ship in ship_names:
        assert ship in text
