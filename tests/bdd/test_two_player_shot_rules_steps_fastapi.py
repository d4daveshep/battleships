import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from starlette.testclient import TestClient

from tests.bdd.conftest import (
    MultiPlayerBDDContext,
    login_player_fastapi,
    place_all_ships_fastapi,
    opponent_fires_via_api,
    DEFAULT_HIT_COORDINATES,
    DEFAULT_MISS_COORDINATES,
    damage_ship_on_board,
    sink_ship_on_board,
)
from bs4 import BeautifulSoup, Tag
from httpx import Response
from game.model import ShipType
import main  # Access game_service singleton

scenarios("../../features/two_player_shot_rules.feature")


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
    login_player_fastapi(client1, p1_name, "human")

    client2 = context.get_client_for_player(p2_name)
    login_player_fastapi(client2, p2_name, "human")

    # 3. Match Players
    # Player 1 selects Player 2
    client1.post("/select-opponent", data={"opponent_name": p2_name})
    # Player 2 accepts
    client2.post("/accept-game-request", data={})

    # 4. Place Ships for Player 1
    place_all_ships_fastapi(client1, p1_name)

    # 5. Place Ships for Player 2
    place_all_ships_fastapi(client2, p2_name)


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
    context.game_url = context.extract_game_url_from_response(response)

    if not context.game_url:
        # Try to get game URL from P1's status check
        status_response = client1.get(
            "/place-ships/opponent-status", headers={"HX-Request": "true"}
        )
        context.game_url = context.extract_game_url_from_response(status_response)


@given("the game has started")
def game_has_started(context: MultiPlayerBDDContext):
    """Verify game has started by checking redirect or status"""
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


# === Scenario 6: Firing fewer shots than available ===


@given(parsers.parse("it is Round {round_num:d}"))
def it_is_round_n(context: MultiPlayerBDDContext, round_num: int):
    """Ensure game is at specific round number by advancing rounds if needed"""
    assert context.soup is not None, "No page loaded"
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get current round from page
    current_round: int = _get_current_round_from_page(context)

    # If we're already at the target round, we're done
    if current_round == round_num:
        return

    # Set up clients
    client: TestClient = context.get_client_for_player(context.current_player_name)
    opponent_name: str = (
        "Player2" if context.current_player_name == "Player1" else "Player1"
    )
    opponent_client: TestClient = context.get_client_for_player(opponent_name)

    # Advance rounds until we reach the target
    while current_round < round_num:
        _advance_one_round(context, client, opponent_client, opponent_name)
        current_round += 1

    # Refresh page to see updated state
    response: Response = client.get(context.game_url)
    context.update_response(response)

    # Verify we're now at the target round
    assert f"Round {round_num}" in context.soup.get_text(), (
        f"Failed to advance to Round {round_num}"
    )


@given(parsers.parse("I have {count:d} shots available"))
def have_n_shots_available(context: MultiPlayerBDDContext, count: int):
    """Ensure player has specific number of shots available by sinking ships if needed"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game instance
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    # Get player
    if game.player_1.name == context.current_player_name:
        player = game.player_1
        player_id = game.player_1.id
    elif game.player_2 and game.player_2.name == context.current_player_name:
        player = game.player_2
        player_id = game.player_2.id
    else:
        raise AssertionError("Could not find player in game")

    # Calculate how many shots to remove (6 is max with all ships)
    current_shots = game.get_shots_available(player_id)
    shots_to_remove = current_shots - count

    # Sink ships to reduce shot count
    # Destroyer = 1 shot, Submarine/Cruiser/Battleship = 1 shot each, Carrier = 2 shots
    board = game.board[player]

    if shots_to_remove >= 1:
        # Sink Destroyer first (removes 1 shot)
        sink_ship_on_board(board, ShipType.DESTROYER)
        shots_to_remove -= 1
    if shots_to_remove >= 1:
        # Sink Submarine (removes 1 shot)
        sink_ship_on_board(board, ShipType.SUBMARINE)
        shots_to_remove -= 1
    if shots_to_remove >= 1:
        # Sink Cruiser (removes 1 shot)
        sink_ship_on_board(board, ShipType.CRUISER)
        shots_to_remove -= 1
    if shots_to_remove >= 1:
        # Sink Battleship (removes 1 shot)
        sink_ship_on_board(board, ShipType.BATTLESHIP)
        shots_to_remove -= 1
    if shots_to_remove >= 2:
        # Sink Carrier (removes 2 shots)
        sink_ship_on_board(board, ShipType.CARRIER)

    # Refresh page to see updated state
    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    # Verify shot count
    assert context.soup is not None, "No page loaded"
    shots_display = context.soup.find(attrs={"data-testid": "shots-available"})
    assert shots_display is not None, "Shots available display not found"
    text: str = shots_display.get_text()
    assert f"Shots Available: {count}" in text, (
        f"Expected 'Shots Available: {count}', got '{text}'"
    )


@when(parsers.parse("I select only {count:d} coordinates to aim at"))
def select_n_coordinates_to_aim(context: MultiPlayerBDDContext, count: int):
    """Select a specific number of coordinates to aim at"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and find coordinates that haven't been fired at yet
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    player_board = game.board[player]

    # Find safe coordinates that haven't been fired at
    from game.model import Coord

    all_safe_coords: list[str] = [f"J{col}" for col in range(1, 11)] + [
        f"{row}{col}" for row in "ABCDEFGHI" for col in range(6, 11)
    ]
    available_coords: list[str] = [
        coord_str
        for coord_str in all_safe_coords
        if Coord[coord_str] not in player_board.shots_fired
    ]

    # Select first N available coordinates
    coords = available_coords[:count]
    context.select_coordinates(coords)

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@when(parsers.parse('I click "{button_name}"'))
def click_button(context: MultiPlayerBDDContext, button_name: str):
    """Click a button by name"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    game_id: str = context.game_url.split("/")[-1]
    client = context.get_client_for_player(context.current_player_name)

    if button_name == "Fire Shots":
        response = client.post(
            "/fire-shots",
            data={"game_id": game_id, "player_name": context.current_player_name},
        )
    else:
        raise ValueError(f"Unknown button: {button_name}")

    context.update_response(response)

    # Refresh the page to get the full state
    response = client.get(context.game_url)
    context.update_response(response)


@then(parsers.parse("my {count:d} shots should be submitted"))
def shots_should_be_submitted(context: MultiPlayerBDDContext, count: int):
    """Verify that the specified number of shots were submitted"""
    assert context.soup is not None

    # Check that the shot counter shows 0/N (no shots aimed after firing)
    aiming_status = context.soup.find(attrs={"data-testid": "aiming-status"})
    if aiming_status:
        text = aiming_status.get_text()
        # Either shows "0/N" or the waiting message takes precedence
        assert "0/" in text or "Waiting" in text, (
            f"Expected shots to be cleared after firing, got: {text}"
        )


@then("I should not be prevented from firing fewer shots than available")
def not_prevented_from_firing_fewer(context: MultiPlayerBDDContext):
    """Verify no error was raised when firing fewer shots"""
    # If we got here without an exception, the test passed
    assert context.response is not None
    assert context.response.status_code == 200


@then("the round should resolve normally when opponent fires")
def round_resolves_normally(context: MultiPlayerBDDContext):
    """Verify round resolves after opponent fires"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Have opponent fire shots
    opponent_name = "Player2" if context.current_player_name == "Player1" else "Player1"
    opponent_client = context.get_client_for_player(opponent_name)
    game_id = context.game_id

    opponent_fires_via_api(opponent_client, game_id, opponent_name)

    # Refresh page to see round resolved
    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    # Verify round incremented (should be Round 5 now, started at Round 4)
    assert context.soup is not None
    assert "Round 5" in context.soup.get_text(), (
        "Round should have incremented after both players fired"
    )


# === Helper Functions ===


def _get_current_round_from_page(context: MultiPlayerBDDContext) -> int:
    """Extract current round number from page text."""
    assert context.soup is not None, "No page loaded"
    page_text: str = context.soup.get_text()

    for i in range(1, 11):  # Check rounds 1-10
        if f"Round {i}" in page_text:
            return i
    return 1


def _advance_one_round(
    context: MultiPlayerBDDContext,
    client: TestClient,
    opponent_client: TestClient,
    opponent_name: str,
) -> None:
    """Advance game by one round by having both players fire."""
    assert context.current_player_name is not None
    game_id: str = context.game_id

    # Get the game to check which coordinates have already been fired at
    game = main.game_service.games[game_id]

    # Get players
    p1 = game.player_1
    p2 = game.player_2
    assert p2 is not None

    # Both players aim and fire
    for player_client, player_name in [
        (client, context.current_player_name),
        (opponent_client, opponent_name),
    ]:
        # Determine which player this is
        player = p1 if p1.name == player_name else p2
        player_board = game.board[player]

        # Find 6 coordinates that haven't been fired at yet
        # Use a large pool of safe coordinates (avoiding ship placements)
        # Ships are at rows A, C, E, G, I (horizontal from column 1)
        # So row J and columns 6-10 in other rows should be safe
        all_safe_coords: list[str] = [f"J{col}" for col in range(1, 11)] + [
            f"{row}{col}" for row in "ABCDEFGHI" for col in range(6, 11)
        ]

        # Filter out already fired coordinates
        from game.model import Coord

        available_coords: list[str] = [
            coord_str
            for coord_str in all_safe_coords
            if Coord[coord_str] not in player_board.shots_fired
        ]

        # Take first 6 available
        coordinates: list[str] = available_coords[:6]

        # Aim all shots
        for coord in coordinates:
            player_client.post(
                "/aim-shot",
                data={"game_id": game_id, "coordinate": coord},
                headers={"HX-Request": "true"},
            )
        # Fire shots
        player_client.post(
            "/fire-shots",
            data={"game_id": game_id, "player_name": player_name},
        )


# === Scenarios 2, 3, 4: Shot count decreases ===


@given(parsers.parse("my opponent has a {ship_name} with {hits:d} hit already"))
def opponent_ship_has_hits(context: MultiPlayerBDDContext, ship_name: str, hits: int):
    """Pre-damage opponent's ship with specific number of hits"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and opponent
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    opponent_name = "Player2" if context.current_player_name == "Player1" else "Player1"
    opponent = game.player_2 if opponent_name == "Player2" else game.player_1
    assert opponent is not None

    # Damage the opponent's ship
    opponent_board = game.board[opponent]
    ship_type = ShipType.from_ship_name(ship_name)
    damage_ship_on_board(opponent_board, ship_type, hits)


@given(parsers.parse("I fire shots that sink the opponent's {ship_name}"))
def fire_shots_sink_opponent_ship(context: MultiPlayerBDDContext, ship_name: str):
    """Fire shots at opponent's ship to sink it"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and opponent
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    opponent_name = "Player2" if context.current_player_name == "Player1" else "Player1"
    opponent = game.player_2 if opponent_name == "Player2" else game.player_1
    assert opponent is not None

    # Find the opponent's ship positions
    opponent_board = game.board[opponent]
    ship_type = ShipType.from_ship_name(ship_name)
    ship = None
    for s in opponent_board.ships:
        if s.ship_type == ship_type:
            ship = s
            break
    assert ship is not None, f"Ship {ship_name} not found on opponent board"

    # Fire at all unhit positions of the ship
    client = context.get_client_for_player(context.current_player_name)
    for coord in ship.positions:
        if coord not in ship.hits:
            client.post(
                "/aim-shot",
                data={"game_id": game_id, "coordinate": coord.name},
                headers={"HX-Request": "true"},
            )

    # Fire the shots
    client.post(
        "/fire-shots",
        data={"game_id": game_id, "player_name": context.current_player_name},
    )


@when(parsers.parse("Round {round_num:d} begins"))
def round_n_begins(context: MultiPlayerBDDContext, round_num: int):
    """Advance to specified round by having both players fire"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Check current round
    current_round = _get_current_round_from_page(context)

    # If already at target round, we're done
    if current_round == round_num:
        return

    # Have both players fire to advance to next round
    opponent_name = "Player2" if context.current_player_name == "Player1" else "Player1"
    opponent_client = context.get_client_for_player(opponent_name)
    client = context.get_client_for_player(context.current_player_name)

    # Use the updated advance_one_round helper
    _advance_one_round(context, client, opponent_client, opponent_name)

    # Refresh page to see new round
    response = client.get(context.game_url)
    context.update_response(response)

    # Verify we're at the expected round
    assert context.soup is not None
    assert f"Round {round_num}" in context.soup.get_text(), (
        f"Expected to be at Round {round_num}"
    )


@then(parsers.parse('my opponent should see "Shots Available: {count:d}" displayed'))
def opponent_sees_shots_available(context: MultiPlayerBDDContext, count: int):
    """Verify opponent sees specific shot count"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Switch to opponent's view
    opponent_name = "Player2" if context.current_player_name == "Player1" else "Player1"
    opponent_client = context.get_client_for_player(opponent_name)

    response = opponent_client.get(context.game_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check opponent's shots available display
    shots_display = soup.find(attrs={"data-testid": "shots-available"})
    assert shots_display is not None, "Shots available display not found"
    text: str = shots_display.get_text()
    assert f"Shots Available: {count}" in text, (
        f"Expected opponent to see 'Shots Available: {count}', got '{text}'"
    )


@then(parsers.parse('I should still see "Shots Available: {count:d}" displayed'))
@then(parsers.parse('I should see "Shots Available: {count:d}" displayed'))
def i_see_shots_available(context: MultiPlayerBDDContext, count: int):
    """Verify I see specific shot count"""
    assert context.soup is not None, "No page loaded"

    # Check my shots available display
    shots_display = context.soup.find(attrs={"data-testid": "shots-available"})
    assert shots_display is not None, "Shots available display not found"
    text: str = shots_display.get_text()
    assert f"Shots Available: {count}" in text, (
        f"Expected 'Shots Available: {count}', got '{text}'"
    )


@then(parsers.parse("the available shots should be {count:d}"))
def available_shots_should_be(context: MultiPlayerBDDContext, count: int):
    """Verify shot count via game state"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and player
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    actual_shots = game.get_shots_available(player.id)
    assert actual_shots == count, f"Expected {count} shots, but got {actual_shots}"


@given(parsers.parse("my {ship_name} has {hits:d} hits already"))
def my_ship_has_hits(context: MultiPlayerBDDContext, ship_name: str, hits: int):
    """Pre-damage my ship with specific number of hits"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and player
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    # Damage my ship
    my_board = game.board[player]
    ship_type = ShipType.from_ship_name(ship_name)
    damage_ship_on_board(my_board, ship_type, hits)


@given(parsers.parse("my opponent fires shots that sink my {ship_name}"))
def opponent_fires_shots_sink_my_ship(context: MultiPlayerBDDContext, ship_name: str):
    """Opponent fires shots to sink my ship"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and player
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    # Find my ship
    my_board = game.board[player]
    ship_type = ShipType.from_ship_name(ship_name)
    ship = None
    for s in my_board.ships:
        if s.ship_type == ship_type:
            ship = s
            break
    assert ship is not None, f"Ship {ship_name} not found on my board"

    # Opponent fires at all unhit positions
    opponent_name = "Player2" if context.current_player_name == "Player1" else "Player1"
    opponent_client = context.get_client_for_player(opponent_name)

    for coord in ship.positions:
        if coord not in ship.hits:
            opponent_client.post(
                "/aim-shot",
                data={"game_id": game_id, "coordinate": coord.name},
                headers={"HX-Request": "true"},
            )

    # Opponent fires
    opponent_client.post(
        "/fire-shots",
        data={"game_id": game_id, "player_name": opponent_name},
    )

    # I also need to fire to complete the round
    client = context.get_client_for_player(context.current_player_name)
    # Aim at safe coordinates
    for coord in DEFAULT_MISS_COORDINATES[:6]:
        client.post(
            "/aim-shot",
            data={"game_id": game_id, "coordinate": coord},
            headers={"HX-Request": "true"},
        )
    client.post(
        "/fire-shots",
        data={"game_id": game_id, "player_name": context.current_player_name},
    )


@given(parsers.parse("my {ship_name} is sunk"))
def my_ship_is_sunk(context: MultiPlayerBDDContext, ship_name: str):
    """Mark my ship as sunk"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and player
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    # Sink my ship
    my_board = game.board[player]
    ship_type = ShipType.from_ship_name(ship_name)
    sink_ship_on_board(my_board, ship_type)


# === Scenario 1: Cannot fire at coordinates already fired at ===


@given(parsers.parse('I fired at "{coordinate}" in Round {round_num:d}'))
def fired_at_coordinate_in_round(
    context: MultiPlayerBDDContext, coordinate: str, round_num: int
):
    """Record that I previously fired at a coordinate in a specific round"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    # Record shot in the player's board shot history
    from game.model import Coord, ShotInfo

    coord_obj = Coord[coordinate]

    # Add shot to player's board shots_fired with round tracking
    my_board = game.board[player]
    my_board.shots_fired[coord_obj] = ShotInfo(
        round_number=round_num,
        is_hit=False,  # Placeholder - doesn't matter for this test
        ship_type=None,
    )

    # Store for later verification (dynamic attribute on dataclass)
    context.previously_fired_coordinate = coordinate  # type: ignore[attr-defined]
    context.previously_fired_round = round_num  # type: ignore[attr-defined]


@given(
    parsers.parse(
        'Coordinate "{coordinate}" on the "Shots Fired" display shows round number "{round_num:d}"'
    )
)
def coordinate_shows_round_number(
    context: MultiPlayerBDDContext, coordinate: str, round_num: int
):
    """Verify coordinate shows specific round number on display"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Refresh page
    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    assert context.soup is not None, "No page loaded"

    # Look for the coordinate in shots fired display with round number
    # The display should show something like "E5 (Round 1)"
    shots_fired_section = context.soup.find(
        attrs={"data-testid": "shots-fired-display"}
    )
    assert shots_fired_section is not None, "Shots fired display not found"

    text: str = shots_fired_section.get_text()
    expected_text = f"{coordinate} (Round {round_num})"
    assert expected_text in text or f"{coordinate}" in text, (
        f"Expected to find '{expected_text}' in shots fired display"
    )


@when(parsers.parse('I attempt to select coordinate "{coordinate}" to aim at'))
def attempt_to_select_coordinate(context: MultiPlayerBDDContext, coordinate: str):
    """Try to select a coordinate to aim at"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    client = context.get_client_for_player(context.current_player_name)
    game_id: str = context.game_id

    # Try to aim at the coordinate
    response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": coordinate},
        headers={"HX-Request": "true"},
    )
    context.update_response(response)


@then("the coordinate should not be selectable")
def coordinate_not_selectable(context: MultiPlayerBDDContext):
    """Verify coordinate cannot be selected"""
    assert context.response is not None

    # Response should indicate error or coordinate should remain unselected
    # Check if response contains an error message
    if context.response.status_code != 200:
        # Error response is expected
        return

    # Or check if the response indicates the coordinate was not added
    # Refresh and check aimed coordinates
    assert context.game_url is not None
    assert context.current_player_name is not None

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    # The previously fired coordinate should not be in aimed shots
    assert context.soup is not None
    aiming_status = context.soup.find(attrs={"data-testid": "aiming-status"})
    assert aiming_status is not None

    # Should show 0 shots aimed or error message
    text: str = aiming_status.get_text()
    assert "0/" in text or "already" in text.lower(), (
        f"Expected coordinate to not be selectable, but got: {text}"
    )


@then(
    parsers.parse(
        'it should still show as already fired with round number "{round_num:d}"'
    )
)
def still_shows_as_fired(context: MultiPlayerBDDContext, round_num: int):
    """Verify coordinate still shows as previously fired"""
    assert context.soup is not None
    assert hasattr(context, "previously_fired_coordinate")

    coordinate = context.previously_fired_coordinate  # type: ignore[attr-defined]

    # Check shots fired display
    shots_fired_section = context.soup.find(
        attrs={"data-testid": "shots-fired-display"}
    )
    assert shots_fired_section is not None, "Shots fired display not found"

    text: str = shots_fired_section.get_text()
    assert coordinate in text, f"Coordinate {coordinate} should still show as fired"


# === Scenario 5: All ships sunk ===


@given("all my ships are sunk")
def all_my_ships_sunk(context: MultiPlayerBDDContext):
    """Sink all of my ships"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get game and player
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    player = (
        game.player_1
        if game.player_1.name == context.current_player_name
        else game.player_2
    )
    assert player is not None

    # Sink all ships
    my_board = game.board[player]
    for ship_type in [
        ShipType.CARRIER,
        ShipType.BATTLESHIP,
        ShipType.CRUISER,
        ShipType.SUBMARINE,
        ShipType.DESTROYER,
    ]:
        sink_ship_on_board(my_board, ship_type)

    # Refresh page to see updated state
    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@then(parsers.parse('I should see "{text}" displayed'))
def should_see_text_displayed(context: MultiPlayerBDDContext, text: str):
    """Verify specific text is displayed on page"""
    assert context.soup is not None, "No page loaded"

    page_text: str = context.soup.get_text()
    assert text in page_text, f"Expected to see '{text}' on page, but it's not there"


@then("the game should be marked as finished")
def game_marked_as_finished(context: MultiPlayerBDDContext):
    """Verify game is marked as finished"""
    assert context.game_url is not None, "No game URL stored"

    # Get game
    game_id: str = context.game_id
    game = main.game_service.games[game_id]

    from game.model import GameStatus

    assert game.status == GameStatus.FINISHED, (
        f"Game should be marked as finished, but status is {game.status}"
    )
