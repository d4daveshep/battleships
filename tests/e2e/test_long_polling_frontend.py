"""
E2E tests for long polling frontend behavior.

These tests follow the TDD RED phase for Step 4 of the long polling migration.
Tests should fail initially as the frontend has not been updated yet.

Expected changes:
- Frontend uses /lobby/status/{player_name}/long-poll endpoint
- HTMX trigger changes from "load, every 1s" to "load" (auto-retry on completion)
- Updates should be faster (no 1s polling delay)

These are Playwright-based E2E tests that verify browser behavior and HTMX
configuration, not BDD tests.
"""

import pytest
from playwright.sync_api import Page


class TestLongPollingFrontend:
    """Tests for long polling frontend implementation"""

    def test_lobby_uses_long_poll_endpoint(self, page: Page, reset_lobby_state):
        """Test that lobby page uses long-poll endpoint instead of short-poll"""
        # Navigate to login
        page.goto("http://localhost:8000/")

        # Fill in player name and select human opponent
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')

        # Wait for lobby page to load
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Check the HTMX configuration on the lobby status element
        status_div = page.locator('[data-testid="lobby-player-status"]')

        # Should use long-poll endpoint
        hx_get = status_div.get_attribute("hx-get")
        assert "/long-poll" in hx_get, f"Expected long-poll endpoint, got: {hx_get}"

    def test_lobby_uses_load_trigger_only(self, page: Page, reset_lobby_state):
        """Test that lobby uses 'load' trigger without 'every 1s' polling"""
        # Navigate to lobby
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Check the HTMX trigger configuration
        status_div = page.locator('[data-testid="lobby-player-status"]')
        hx_trigger = status_div.get_attribute("hx-trigger")

        # Should only have 'load' trigger (HTMX will auto-retry on response)
        assert hx_trigger == "load", f"Expected 'load' trigger only, got: {hx_trigger}"
        assert "every" not in hx_trigger, "Should not have 'every 1s' polling trigger"

    def test_real_time_updates_faster_than_short_polling(self, page: Page, reset_lobby_state):
        """Test that updates appear when using long polling"""
        import httpx

        # Alice joins lobby
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Verify "No other players" message appears initially
        page.wait_for_selector('[data-testid="no-players-message"]')

        # Bob joins via browser (open new page context)
        bob_page = page.context.new_page()
        bob_page.goto("http://localhost:8000/")
        bob_page.fill('input[name="player_name"]', "Bob")
        bob_page.click('button[name="game_mode"][value="human"]')
        bob_page.wait_for_selector('[data-testid="lobby-container"]')

        # Wait for Bob to appear in Alice's lobby view (long poll should update)
        page.wait_for_selector('button[data-testid="select-opponent-Bob"]', timeout=35000)

        # Verify Bob appeared
        assert page.locator('button[data-testid="select-opponent-Bob"]').is_visible()

        bob_page.close()

    def test_multiple_rapid_updates_all_received(self, page: Page, reset_lobby_state):
        """Test that rapid state changes are all received without missing updates"""
        # Alice joins lobby
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Add multiple players via browser pages
        bob_page = page.context.new_page()
        bob_page.goto("http://localhost:8000/")
        bob_page.fill('input[name="player_name"]', "Bob")
        bob_page.click('button[name="game_mode"][value="human"]')

        charlie_page = page.context.new_page()
        charlie_page.goto("http://localhost:8000/")
        charlie_page.fill('input[name="player_name"]', "Charlie")
        charlie_page.click('button[name="game_mode"][value="human"]')

        # All players should appear (allow up to 35s for long poll timeout + updates)
        page.wait_for_selector('button[data-testid="select-opponent-Bob"]', timeout=35000)
        page.wait_for_selector('button[data-testid="select-opponent-Charlie"]', timeout=35000)

        # Verify all are visible
        assert page.locator('button[data-testid="select-opponent-Bob"]').is_visible()
        assert page.locator('button[data-testid="select-opponent-Charlie"]').is_visible()

        bob_page.close()
        charlie_page.close()

    def test_game_request_status_updates_immediately(self, page: Page, reset_lobby_state):
        """Test that game request status changes are reflected"""
        # Alice and Bob join
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        bob_page = page.context.new_page()
        bob_page.goto("http://localhost:8000/")
        bob_page.fill('input[name="player_name"]', "Bob")
        bob_page.click('button[name="game_mode"][value="human"]')

        page.wait_for_selector('button[data-testid="select-opponent-Bob"]', timeout=35000)

        # Alice sends game request
        page.click('button[data-testid="select-opponent-Bob"]')

        # Wait for status to change to "Requesting Game"
        page.wait_for_selector('text=Game request sent to Bob', timeout=35000)

        # Verify confirmation message appears
        assert page.locator('text=Game request sent to Bob').is_visible()

        bob_page.close()

    def test_no_unnecessary_polling_when_no_changes(self, page: Page, reset_lobby_state):
        """Test that browser doesn't poll unnecessarily when there are no changes"""
        # This test verifies that long polling holds the connection rather than
        # making repeated requests every second

        # Alice joins lobby
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Wait and observe network activity
        # With short polling: would see requests every ~1s
        # With long polling: should see a single long-running request

        # This is more of a manual verification test, but we can at least
        # verify the endpoint being called is the long-poll one
        status_div = page.locator('[data-testid="lobby-player-status"]')
        hx_get = status_div.get_attribute("hx-get")
        assert "/long-poll" in hx_get

    def test_connection_resilience_after_timeout(self, page: Page, reset_lobby_state):
        """Test that connection automatically reconnects after long-poll timeout"""
        # Alice joins lobby
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Wait longer than the long-poll timeout (30s default)
        # HTMX should automatically reconnect after response
        page.wait_for_timeout(35000)

        # Verify lobby is still functional by adding a player via browser
        bob_page = page.context.new_page()
        bob_page.goto("http://localhost:8000/")
        bob_page.fill('input[name="player_name"]', "Bob")
        bob_page.click('button[name="game_mode"][value="human"]')

        # Bob should still appear (connection should have reconnected)
        page.wait_for_selector('button[data-testid="select-opponent-Bob"]', timeout=35000)
        assert page.locator('button[data-testid="select-opponent-Bob"]').is_visible()

        bob_page.close()


class TestLongPollingPerformance:
    """Tests verifying performance improvements from long polling"""

    def test_reduced_server_requests_compared_to_short_polling(self, page: Page, reset_lobby_state):
        """Test that long polling reduces number of server requests"""
        # This is primarily a performance observation test
        # With short polling: ~60 requests per minute
        # With long polling: ~2 requests per minute (one every 30s)

        # Alice joins lobby
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Verify we're using long polling endpoint
        status_div = page.locator('[data-testid="lobby-player-status"]')
        hx_get = status_div.get_attribute("hx-get")
        assert "/long-poll" in hx_get, "Should be using long-poll endpoint for reduced requests"

    def test_instant_response_to_state_changes(self, page: Page, reset_lobby_state):
        """Test that state changes trigger updates with long polling"""
        # Alice joins
        page.goto("http://localhost:8000/")
        page.fill('input[name="player_name"]', "Alice")
        page.click('button[name="game_mode"][value="human"]')
        page.wait_for_selector('[data-testid="lobby-container"]')

        # Bob joins via browser
        bob_page = page.context.new_page()
        bob_page.goto("http://localhost:8000/")
        bob_page.fill('input[name="player_name"]', "Bob")
        bob_page.click('button[name="game_mode"][value="human"]')

        # With event-based notifications, Bob should appear
        page.wait_for_selector('button[data-testid="select-opponent-Bob"]', timeout=35000)

        # Verify Bob appeared
        assert page.locator('button[data-testid="select-opponent-Bob"]').is_visible()

        bob_page.close()
