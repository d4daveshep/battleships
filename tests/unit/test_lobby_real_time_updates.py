import pytest
from datetime import datetime, timedelta
from typing import List, Optional

from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus
from services.lobby_service import LobbyService


# FIXME: WTF is all this doing in a unit test file !!!
# Consider deleting this file entirely and letting the missing UI functionality drive what's needed entirely
#
class LobbyUpdateEvent:
    """Represents a lobby update event for testing real-time functionality"""

    def __init__(
        self, event_type: str, player_name: str, timestamp: Optional[datetime] = None
    ):
        self.event_type = (
            event_type  # "join", "leave", "status_change", "request_sent", etc.
        )
        self.player_name = player_name
        self.timestamp = timestamp or datetime.now()
        self.additional_data = {}


class LobbyEventTracker:
    """Tracks lobby events for testing real-time update functionality"""

    def __init__(self):
        self.events: List[LobbyUpdateEvent] = []

    def record_player_joined(self, player_name: str):
        event = LobbyUpdateEvent("player_joined", player_name)
        self.events.append(event)

    def record_player_left(self, player_name: str):
        event = LobbyUpdateEvent("player_left", player_name)
        self.events.append(event)

    def record_status_change(
        self, player_name: str, old_status: PlayerStatus, new_status: PlayerStatus
    ):
        event = LobbyUpdateEvent("status_change", player_name)
        event.additional_data = {"old_status": old_status, "new_status": new_status}
        self.events.append(event)

    def record_request_sent(self, sender: str, receiver: str):
        event = LobbyUpdateEvent("request_sent", sender)
        event.additional_data = {"receiver": receiver}
        self.events.append(event)

    def record_request_accepted(self, sender: str, receiver: str):
        event = LobbyUpdateEvent("request_accepted", receiver)
        event.additional_data = {"sender": sender}
        self.events.append(event)

    def record_request_declined(self, sender: str, receiver: str):
        event = LobbyUpdateEvent("request_declined", receiver)
        event.additional_data = {"sender": sender}
        self.events.append(event)

    def get_events_for_player(self, player_name: str) -> List[LobbyUpdateEvent]:
        """Get all events that would affect a specific player's lobby view"""
        relevant_events = []

        for event in self.events:
            # Events that affect everyone's view
            if event.event_type in ["player_joined", "player_left", "status_change"]:
                if event.player_name != player_name:  # Don't include own join/leave
                    relevant_events.append(event)

            # Events that affect specific players
            elif event.event_type == "request_sent":
                receiver = event.additional_data.get("receiver")
                if receiver == player_name or event.player_name == player_name:
                    relevant_events.append(event)

            elif event.event_type in ["request_accepted", "request_declined"]:
                sender = event.additional_data.get("sender")
                if sender == player_name or event.player_name == player_name:
                    relevant_events.append(event)

        return relevant_events

    def clear_events(self):
        self.events.clear()


class LobbyServiceWithTracking(LobbyService):
    """LobbyService with event tracking for testing real-time updates"""

    def __init__(self, lobby: Lobby, tracker: LobbyEventTracker):
        super().__init__(lobby)
        self.tracker = tracker

    def join_lobby(self, player_name: str) -> None:
        super().join_lobby(player_name)
        self.tracker.record_player_joined(player_name)

    def leave_lobby(self, player_name: str) -> None:
        super().leave_lobby(player_name)
        self.tracker.record_player_left(player_name)

    def update_player_status(self, player_name: str, status: PlayerStatus) -> None:
        old_status = self.get_player_status(player_name)
        super().update_player_status(player_name, status)
        self.tracker.record_status_change(player_name, old_status, status)

    def send_game_request(self, sender: str, receiver: str) -> None:
        super().send_game_request(sender, receiver)
        self.tracker.record_request_sent(sender, receiver)

    def accept_game_request(self, receiver: str) -> tuple[str, str]:
        request = self.get_pending_request_for_player(receiver)
        sender = request.sender if request else "Unknown"
        result = super().accept_game_request(receiver)
        self.tracker.record_request_accepted(sender, receiver)
        return result

    def decline_game_request(self, receiver: str) -> str:
        request = self.get_pending_request_for_player(receiver)
        sender = request.sender if request else "Unknown"
        result = super().decline_game_request(receiver)
        self.tracker.record_request_declined(sender, receiver)
        return result


class TestLobbyRealTimeUpdates:
    """Unit tests for real-time lobby update functionality"""

    def test_player_join_triggers_update_event(self, empty_lobby: Lobby):
        # Test that joining lobby triggers appropriate update events
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")

        # Verify event was recorded
        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "player_joined"
        assert event.player_name == "Alice"

    def test_player_leave_triggers_update_event(self, empty_lobby: Lobby):
        # Test that leaving lobby triggers appropriate update events
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        tracker.clear_events()  # Clear join event

        service.leave_lobby("Alice")

        # Verify leave event was recorded
        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "player_left"
        assert event.player_name == "Alice"

    def test_status_change_triggers_update_event(self, empty_lobby: Lobby):
        # Test that status changes trigger appropriate update events
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        tracker.clear_events()  # Clear join event

        service.update_player_status("Alice", PlayerStatus.REQUESTING_GAME)

        # Verify status change event was recorded
        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "status_change"
        assert event.player_name == "Alice"
        assert event.additional_data["old_status"] == PlayerStatus.AVAILABLE
        assert event.additional_data["new_status"] == PlayerStatus.REQUESTING_GAME

    def test_game_request_triggers_update_events(self, empty_lobby: Lobby):
        # Test that sending game request triggers appropriate update events
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        service.join_lobby("Bob")
        tracker.clear_events()  # Clear join events

        service.send_game_request("Alice", "Bob")

        # Should have request_sent event and status_change events
        events_by_type = {}
        for event in tracker.events:
            events_by_type[event.event_type] = event

        assert "request_sent" in events_by_type
        assert "status_change" in events_by_type

        request_event = events_by_type["request_sent"]
        assert request_event.player_name == "Alice"
        assert request_event.additional_data["receiver"] == "Bob"

    def test_accept_game_request_triggers_update_events(self, empty_lobby: Lobby):
        # Test that accepting game request triggers appropriate update events
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        service.join_lobby("Bob")
        service.send_game_request("Alice", "Bob")
        tracker.clear_events()  # Clear previous events

        service.accept_game_request("Bob")

        # Should have request_accepted event and status_change events
        events_by_type = {}
        for event in tracker.events:
            if event.event_type not in events_by_type:
                events_by_type[event.event_type] = []
            events_by_type[event.event_type].append(event)

        assert "request_accepted" in events_by_type
        assert "status_change" in events_by_type

        accept_event = events_by_type["request_accepted"][0]
        assert accept_event.player_name == "Bob"
        assert accept_event.additional_data["sender"] == "Alice"

    def test_decline_game_request_triggers_update_events(self, empty_lobby: Lobby):
        # Test that declining game request triggers appropriate update events
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        service.join_lobby("Bob")
        service.send_game_request("Alice", "Bob")
        tracker.clear_events()  # Clear previous events

        service.decline_game_request("Bob")

        # Should have request_declined event and status_change events
        events_by_type = {}
        for event in tracker.events:
            if event.event_type not in events_by_type:
                events_by_type[event.event_type] = []
            events_by_type[event.event_type].append(event)

        assert "request_declined" in events_by_type
        assert "status_change" in events_by_type

        decline_event = events_by_type["request_declined"][0]
        assert decline_event.player_name == "Bob"
        assert decline_event.additional_data["sender"] == "Alice"

    def test_get_events_for_player_filters_correctly(self, empty_lobby: Lobby):
        # Test that event filtering works correctly for specific players
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        # Setup scenario with multiple players and events
        service.join_lobby("Alice")
        service.join_lobby("Bob")
        service.join_lobby("Charlie")
        service.send_game_request("Alice", "Bob")

        # Get events relevant to Charlie (observer)
        charlie_events = tracker.get_events_for_player("Charlie")

        # Charlie should see Alice and Bob join, and their status changes
        event_types = [event.event_type for event in charlie_events]
        assert "player_joined" in event_types  # Should see Alice and Bob join
        assert "status_change" in event_types  # Should see status changes from request

        # Verify Charlie doesn't see their own join event
        join_events = [e for e in charlie_events if e.event_type == "player_joined"]
        join_player_names = [e.player_name for e in join_events]
        assert "Charlie" not in join_player_names

    def test_events_have_timestamps(self, empty_lobby: Lobby):
        # Test that all events have appropriate timestamps
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        before = datetime.now()
        service.join_lobby("Alice")
        after = datetime.now()

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert before <= event.timestamp <= after

    def test_multiple_concurrent_events_preserved_order(self, empty_lobby: Lobby):
        # Test that multiple events maintain chronological order
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        # Perform sequence of operations
        service.join_lobby("Alice")
        service.join_lobby("Bob")
        service.send_game_request("Alice", "Bob")
        service.decline_game_request("Bob")

        # Verify events are in chronological order
        for i in range(1, len(tracker.events)):
            assert tracker.events[i - 1].timestamp <= tracker.events[i].timestamp

    def test_event_tracker_clear_removes_all_events(self, empty_lobby: Lobby):
        # Test that clearing events works correctly
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        service.join_lobby("Bob")
        assert len(tracker.events) > 0

        tracker.clear_events()
        assert len(tracker.events) == 0

    def test_leave_lobby_events_affect_other_players(self, empty_lobby: Lobby):
        # Test that leave events properly affect other players' views
        tracker = LobbyEventTracker()
        service = LobbyServiceWithTracking(empty_lobby, tracker)

        service.join_lobby("Alice")
        service.join_lobby("Bob")
        service.join_lobby("Charlie")
        tracker.clear_events()

        service.leave_lobby("Alice")

        # Bob and Charlie should see Alice's leave event
        bob_events = tracker.get_events_for_player("Bob")
        charlie_events = tracker.get_events_for_player("Charlie")

        assert len(bob_events) == 1
        assert len(charlie_events) == 1
        assert bob_events[0].event_type == "player_left"
        assert charlie_events[0].event_type == "player_left"
        assert bob_events[0].player_name == "Alice"
        assert charlie_events[0].player_name == "Alice"


class TestLobbyEventTracker:
    """Unit tests for LobbyEventTracker utility class"""

    def test_record_player_joined(self):
        # Test recording player join events
        tracker = LobbyEventTracker()

        tracker.record_player_joined("Alice")

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "player_joined"
        assert event.player_name == "Alice"

    def test_record_player_left(self):
        # Test recording player leave events
        tracker = LobbyEventTracker()

        tracker.record_player_left("Alice")

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "player_left"
        assert event.player_name == "Alice"

    def test_record_status_change(self):
        # Test recording status change events
        tracker = LobbyEventTracker()

        tracker.record_status_change(
            "Alice", PlayerStatus.AVAILABLE, PlayerStatus.REQUESTING_GAME
        )

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "status_change"
        assert event.player_name == "Alice"
        assert event.additional_data["old_status"] == PlayerStatus.AVAILABLE
        assert event.additional_data["new_status"] == PlayerStatus.REQUESTING_GAME

    def test_record_request_sent(self):
        # Test recording game request sent events
        tracker = LobbyEventTracker()

        tracker.record_request_sent("Alice", "Bob")

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "request_sent"
        assert event.player_name == "Alice"
        assert event.additional_data["receiver"] == "Bob"

    def test_record_request_accepted(self):
        # Test recording game request accepted events
        tracker = LobbyEventTracker()

        tracker.record_request_accepted("Alice", "Bob")

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "request_accepted"
        assert event.player_name == "Bob"
        assert event.additional_data["sender"] == "Alice"

    def test_record_request_declined(self):
        # Test recording game request declined events
        tracker = LobbyEventTracker()

        tracker.record_request_declined("Alice", "Bob")

        assert len(tracker.events) == 1
        event = tracker.events[0]
        assert event.event_type == "request_declined"
        assert event.player_name == "Bob"
        assert event.additional_data["sender"] == "Alice"

    def test_get_events_for_player_empty(self):
        # Test getting events for player when no events exist
        tracker = LobbyEventTracker()

        events = tracker.get_events_for_player("Alice")

        assert len(events) == 0

    def test_get_events_for_player_excludes_own_join_leave(self):
        # Test that player doesn't see their own join/leave events
        tracker = LobbyEventTracker()

        tracker.record_player_joined("Alice")
        tracker.record_player_left("Alice")

        alice_events = tracker.get_events_for_player("Alice")

        assert len(alice_events) == 0

    def test_get_events_for_player_includes_others_join_leave(self):
        # Test that player sees other players' join/leave events
        tracker = LobbyEventTracker()

        tracker.record_player_joined("Bob")
        tracker.record_player_left("Charlie")

        alice_events = tracker.get_events_for_player("Alice")

        assert len(alice_events) == 2
        event_types = [event.event_type for event in alice_events]
        assert "player_joined" in event_types
        assert "player_left" in event_types

    def test_get_events_for_player_includes_relevant_requests(self):
        # Test that player sees relevant game request events
        tracker = LobbyEventTracker()

        # Alice sends request to Bob
        tracker.record_request_sent("Alice", "Bob")
        # Charlie sends request to Diana (irrelevant to Alice/Bob)
        tracker.record_request_sent("Charlie", "Diana")

        # Alice should see the Alice->Bob request
        alice_events = tracker.get_events_for_player("Alice")
        assert len(alice_events) == 1
        assert alice_events[0].event_type == "request_sent"

        # Bob should see the Alice->Bob request
        bob_events = tracker.get_events_for_player("Bob")
        assert len(bob_events) == 1
        assert bob_events[0].event_type == "request_sent"

        # Eve should not see any request events
        eve_events = tracker.get_events_for_player("Eve")
        assert len(eve_events) == 0

