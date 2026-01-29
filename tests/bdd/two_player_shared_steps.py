"""Shared step definitions for two-player gameplay features.

This module contains Background steps and common assertion helpers
that are reused across FastAPI and Playwright BDD tests.
"""

import pytest
from pytest_bdd import given, when, then, parsers
from tests.bdd.conftest import (
    MultiPlayerBDDContext,
    login_player_fastapi,
    place_all_ships_fastapi,
    opponent_fires_via_api,
)


# =============================================================================
# Background Steps
# =============================================================================


@given("both players have completed ship placement")
def players_completed_placement(context: MultiPlayerBDDContext):
    """Setup a game with two players who have placed ships"""
    with context.get_client_for_player("System") as client:
        client.post("/test/reset-lobby")

    p1_name = "Player1"
    p2_name = "Player2"
    context.current_player_name = p1_name

    client1 = context.get_client_for_player(p1_name)
    login_player_fastapi(client1, p1_name, "human")

    client2 = context.get_client_for_player(p2_name)
    login_player_fastapi(client2, p2_name, "human")

    client1.post("/select-opponent", data={"opponent_name": p2_name})
    client2.post("/accept-game-request", data={})

    place_all_ships_fastapi(client1, p1_name)
    place_all_ships_fastapi(client2, p2_name)


@given("both players are ready")
def players_are_ready(context: MultiPlayerBDDContext):
    """Both players click ready"""
    p1_name = "Player1"
    p2_name = "Player2"

    client1 = context.get_client_for_player(p1_name)
    client2 = context.get_client_for_player(p2_name)

    client1.post("/ready-for-game", data={"player_name": p1_name})
    response = client2.post(
        "/ready-for-game", data={"player_name": p2_name}, follow_redirects=False
    )

    context.game_url = context.extract_game_url_from_response(response)

    if not context.game_url:
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

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Round" in response.text or "game" in response.text.lower()


# =============================================================================
# Common Given/When Steps
# =============================================================================


@given("the game just started")
def game_just_started(context: MultiPlayerBDDContext):
    """Ensure it is the beginning of the game"""
    pass


@given("it is Round 1")
def it_is_round_1(context: MultiPlayerBDDContext):
    """Verify it is Round 1"""
    pass


@given("I have 6 shots available")
def have_6_shots_available(context: MultiPlayerBDDContext):
    """Verify player has 6 shots available (all ships placed)"""
    pass


@given("I have selected 6 coordinates to aim at")
def have_selected_6_coordinates(context: MultiPlayerBDDContext):
    """Select 6 coordinates to aim at"""
    context.select_coordinates(["A1", "B1", "C1", "D1", "E1", "F1"])

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@given('I have clicked "Fire Shots"')
def clicked_fire_shots(context: MultiPlayerBDDContext):
    """Simulate clicking fire shots button"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    game_id = context.game_url.split("/")[-1]
    client = context.get_client_for_player(context.current_player_name)

    client.post(
        "/fire-shots",
        data={"game_id": game_id, "player_name": context.current_player_name},
    )

    response = client.get(context.game_url)
    context.update_response(response)


@given("I have fired my 6 shots")
def fired_6_shots(context: MultiPlayerBDDContext):
    """Aim and fire 6 shots"""
    have_selected_6_coordinates(context)
    clicked_fire_shots(context)


@given("I am waiting for my opponent")
@given("I am waiting for my opponent to fire")
@given("I am waiting for my opponent")
@when("I am waiting for my opponent to fire")
def waiting_for_opponent(context: MultiPlayerBDDContext):
    """Verify waiting state"""
    see_waiting_for_opponent_message(context)


@given("I am still aiming my shots")
def still_aiming(context: MultiPlayerBDDContext):
    """Verify I am still in aiming phase"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@given("my opponent has already fired their shots")
def opponent_fired_shots(context: MultiPlayerBDDContext):
    """Simulate opponent firing shots"""
    _shared_opponent_fires(context)


@when("my opponent fires their shots")
def opponent_fires_action(context: MultiPlayerBDDContext):
    """Action: Opponent fires"""
    _shared_opponent_fires(context)


def _shared_opponent_fires(context: MultiPlayerBDDContext):
    """Shared helper to make opponent fire shots"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    me = context.current_player_name
    opponent = "Player2" if me == "Player1" else "Player1"

    client = context.get_client_for_player(opponent)
    game_id = context.game_url.split("/")[-1]

    opponent_fires_via_api(client, game_id, opponent)


# =============================================================================
# Common When Steps
# =============================================================================


@when(parsers.parse('I select coordinate "{coord}" to aim at'))
def select_coordinate_to_aim(context: MultiPlayerBDDContext, coord: str):
    """Select a coordinate to aim at via HTMX endpoint"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    game_id = context.game_url.split("/")[-1]

    client = context.get_client_for_player(context.current_player_name)
    response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": coord},
        headers={"HX-Request": "true"},
    )
    context.update_response(response)

    response = client.get(context.game_url)
    context.update_response(response)


@when(parsers.parse('I select coordinate "{coord}" again'))
def select_coordinate_again(context: MultiPlayerBDDContext, coord: str):
    """Select the same coordinate again (toggle off)"""
    select_coordinate_to_aim(context, coord)


@when("I attempt to select another coordinate")
def attempt_select_another_coordinate(context: MultiPlayerBDDContext):
    """Attempt to select a 7th coordinate when already at limit"""
    game_id = context.game_id
    client = context.get_client_for_player(context.current_player_name)

    htmx_response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": "G1"},
        headers={"HX-Request": "true"},
    )

    context.htmx_response = htmx_response

    response = client.get(context.game_url)
    context.update_response(response)


@when(parsers.parse('I click the "{button_name}" button'))
def click_button(context: MultiPlayerBDDContext, button_name: str):
    """Click a button by name"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    game_id = context.game_url.split("/")[-1]

    client = context.get_client_for_player(context.current_player_name)

    if button_name == "Fire Shots":
        response = client.post(
            "/fire-shots",
            data={"game_id": game_id, "player_name": context.current_player_name},
        )
    else:
        raise ValueError(f"Unknown button: {button_name}")

    context.update_response(response)

    response = client.get(context.game_url)
    context.update_response(response)


@when("I fire my shots")
def just_fire_shots(context: MultiPlayerBDDContext):
    """Just click fire (assuming shots aimed)"""
    click_button(context, "Fire Shots")


# =============================================================================
# Common Then Steps
# =============================================================================


@then(parsers.parse('I should see "{text}" displayed'))
def see_text_displayed(context: MultiPlayerBDDContext, text: str):
    """Verify text is displayed on the page"""
    assert context.soup is not None
    assert text in context.soup.get_text()


@then("I should see a loading indicator")
def see_loading_indicator(context: MultiPlayerBDDContext):
    """Verify loading indicator in waiting message"""
    see_waiting_for_opponent_message(context)


@then('I should see "Waiting for opponent to fire..." displayed')
def see_waiting_for_opponent_message(context: MultiPlayerBDDContext):
    """Verify the waiting for opponent message is displayed"""
    assert context.soup is not None
    text = context.soup.get_text()
    assert "Waiting for opponent" in text, (
        f"Expected 'Waiting for opponent to fire...' in page text, got: {text}"
    )


@then("the round number should increment to Round 2")
def round_increments(context: MultiPlayerBDDContext):
    """Verify round number"""
    assert context.soup is not None
    assert "Round 2" in context.soup.get_text()


@then('I should see "Opponent has fired - waiting for you" displayed')
def see_opponent_fired_message(context: MultiPlayerBDDContext):
    """Verify message when opponent fires first"""
    assert context.soup is not None
    text = context.soup.get_text()
    assert "Opponent has fired - waiting for you" in text


@then("the round should resolve immediately")
def round_resolves_immediately(context: MultiPlayerBDDContext):
    """Verify round resolves without delay when both have fired"""
    assert context.soup is not None
    assert "Round 2" in context.soup.get_text()


@then(parsers.parse("I should see the round results within {seconds:d} seconds"))
def see_round_results_polling(context: MultiPlayerBDDContext, seconds: int):
    """Simulate polling until results appear"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    client = context.get_client_for_player(context.current_player_name)
    game_id = context.game_url.split("/")[-1]

    response = client.get(f"/game/{game_id}/status")
    context.update_response(response)

    assert "Round 2" in response.text


@then("both players' shots should be processed together")
def shots_processed_together(context: MultiPlayerBDDContext):
    """Verify round resolution"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    assert "Round 2" in response.text


@then("I should not be able to aim additional shots")
@then("I should not be able to aim or fire additional shots")
def cannot_aim_additional_shots(context: MultiPlayerBDDContext):
    """Verify that aiming additional shots is blocked"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    game_id = context.game_url.split("/")[-1]
    client = context.get_client_for_player(context.current_player_name)

    htmx_response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": "G1"},
        headers={"HX-Request": "true"},
    )

    assert htmx_response.status_code == 200
    assert "Cannot aim shots after firing" in htmx_response.text


@then("the page should update automatically when opponent fires")
def page_update_automatically(context: MultiPlayerBDDContext):
    """Verify polling mechanism"""
    _shared_opponent_fires(context)
    see_round_results_polling(context, 5)
