"""
Unit tests for Lobby event-based notification system.

These tests follow the TDD RED phase for Step 3 of the long polling migration.
Tests should fail initially as the event system is not yet implemented.
"""

import asyncio
import pytest
from game.lobby import Lobby
from game.player import PlayerStatus


class TestLobbyEventNotifications:
    """Tests for asyncio.Event-based change notifications in Lobby"""

    def test_lobby_has_change_event(self):
        """Test that Lobby has an asyncio.Event for change notifications"""
        lobby = Lobby()
        assert hasattr(lobby, "change_event"), "Lobby should have a change_event attribute"
        assert isinstance(
            lobby.change_event, asyncio.Event
        ), "change_event should be an asyncio.Event"

    def test_change_event_initially_not_set(self):
        """Test that change_event is not set initially"""
        lobby = Lobby()
        assert not lobby.change_event.is_set(), "change_event should not be set initially"

    @pytest.mark.asyncio
    async def test_add_player_sets_change_event(self):
        """Test that adding a player sets the change event"""
        lobby = Lobby()
        lobby.change_event.clear()

        # Add player
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        # Event should be set
        assert lobby.change_event.is_set(), "change_event should be set after adding player"

    @pytest.mark.asyncio
    async def test_remove_player_sets_change_event(self):
        """Test that removing a player sets the change event"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.change_event.clear()

        # Remove player
        lobby.remove_player("Alice")

        # Event should be set
        assert lobby.change_event.is_set(), "change_event should be set after removing player"

    @pytest.mark.asyncio
    async def test_update_player_status_sets_change_event(self):
        """Test that updating player status sets the change event"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.change_event.clear()

        # Update status
        lobby.update_player_status("Alice", PlayerStatus.REQUESTING_GAME)

        # Event should be set
        assert (
            lobby.change_event.is_set()
        ), "change_event should be set after status update"

    @pytest.mark.asyncio
    async def test_send_game_request_sets_change_event(self):
        """Test that sending game request sets the change event"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.change_event.clear()

        # Send game request
        lobby.send_game_request("Alice", "Bob")

        # Event should be set
        assert (
            lobby.change_event.is_set()
        ), "change_event should be set after sending game request"

    @pytest.mark.asyncio
    async def test_accept_game_request_sets_change_event(self):
        """Test that accepting game request sets the change event"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")
        lobby.change_event.clear()

        # Accept game request
        lobby.accept_game_request("Bob")

        # Event should be set
        assert (
            lobby.change_event.is_set()
        ), "change_event should be set after accepting game request"

    @pytest.mark.asyncio
    async def test_decline_game_request_sets_change_event(self):
        """Test that declining game request sets the change event"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")
        lobby.change_event.clear()

        # Decline game request
        lobby.decline_game_request("Bob")

        # Event should be set
        assert (
            lobby.change_event.is_set()
        ), "change_event should be set after declining game request"

    @pytest.mark.asyncio
    async def test_wait_for_change_completes_when_event_set(self):
        """Test that wait_for_change() completes when event is set"""
        lobby = Lobby()
        initial_version = lobby.get_version()

        async def trigger_change():
            # Wait a bit then trigger a change
            await asyncio.sleep(0.1)
            lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        # Start waiting for change
        wait_task = asyncio.create_task(lobby.wait_for_change(initial_version))
        trigger_task = asyncio.create_task(trigger_change())

        # Wait for both tasks
        await asyncio.gather(wait_task, trigger_task)

        # wait_for_change should have completed successfully
        assert wait_task.done(), "wait_for_change should complete when change occurs"

    @pytest.mark.asyncio
    async def test_wait_for_change_returns_immediately_if_version_changed(self):
        """Test that wait_for_change returns immediately if version already changed"""
        lobby = Lobby()
        initial_version = lobby.get_version()

        # Make a change
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        # Wait for change with old version - should return immediately
        import time

        start = time.time()
        await lobby.wait_for_change(initial_version)
        elapsed = time.time() - start

        assert elapsed < 0.1, "wait_for_change should return immediately if version changed"

    @pytest.mark.asyncio
    async def test_wait_for_change_waits_if_version_unchanged(self):
        """Test that wait_for_change waits if version hasn't changed"""
        lobby = Lobby()
        current_version = lobby.get_version()

        # Try to wait for change with current version (should wait)
        wait_task = asyncio.create_task(lobby.wait_for_change(current_version))

        # Give it a moment to start waiting
        await asyncio.sleep(0.05)

        # Should still be waiting
        assert not wait_task.done(), "wait_for_change should wait if version unchanged"

        # Cancel the task to clean up
        wait_task.cancel()
        try:
            await wait_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_multiple_waiters_all_notified(self):
        """Test that all waiters are notified when change occurs"""
        lobby = Lobby()
        initial_version = lobby.get_version()

        # Create multiple waiting tasks
        wait_task1 = asyncio.create_task(lobby.wait_for_change(initial_version))
        wait_task2 = asyncio.create_task(lobby.wait_for_change(initial_version))
        wait_task3 = asyncio.create_task(lobby.wait_for_change(initial_version))

        # Give them time to start waiting
        await asyncio.sleep(0.05)

        # Trigger a change
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        # Give time for notification
        await asyncio.sleep(0.05)

        # All waiters should be notified
        assert wait_task1.done(), "First waiter should be notified"
        assert wait_task2.done(), "Second waiter should be notified"
        assert wait_task3.done(), "Third waiter should be notified"

    @pytest.mark.asyncio
    async def test_event_cleared_after_notification(self):
        """Test that event is cleared after notifying waiters (ready for next change)"""
        lobby = Lobby()
        initial_version = lobby.get_version()

        # Add player (triggers event)
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        # Event should be set
        assert lobby.change_event.is_set()

        # After waiting for change, event should be prepared for next change
        # (implementation detail: may be cleared automatically or manually)
        # Wait for the change
        await lobby.wait_for_change(initial_version)

        # Make another change
        lobby.get_version()
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)

        # Event should be set again for the new change
        assert lobby.change_event.is_set(), "Event should be set for new changes"
