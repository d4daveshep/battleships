# Migration Plan: Short Polling → Long Polling

## Current Implementation Analysis

**Short Polling (Current):**
- Frontend: `hx-trigger="load, every 1s"` on lobby.html:16
- Endpoint: `/lobby/status/{player_name}` (main.py:250)
- Polls every 1 second for lobby updates
- Returns immediately with current state

## Long Polling Implementation Plan

### 1. **Backend Changes** (Application Layer)

**A. New Long Polling Endpoint**
- Create `/lobby/status/{player_name}/long-poll` endpoint
- Implement timeout mechanism (e.g., 30 seconds)
- Add change detection logic to return early when state changes
- Keep existing `/lobby/status/{player_name}` for backwards compatibility during transition

**B. State Change Detection**
- Add version/timestamp tracking to lobby state
- Implement efficient change detection (compare state hashes or version numbers)
- Create event-based notification system (in-memory for now)

**C. Timeout Configuration**
- Configurable long poll timeout (default: 30s)
- Immediate return on state change
- Graceful handling of client disconnections

### 2. **Frontend Changes** (Templates)

**A. Update Polling Trigger**
- Change `hx-trigger="load, every 1s"` to `hx-trigger="load"`
- Let HTMX automatically re-trigger on response completion (natural long polling behavior)
- Update endpoint URL to use new long-poll endpoint

**B. Error Handling**
- Add timeout recovery
- Network error handling

### 3. **Test Strategy** (BDD/TDD Approach)

**Phase 1: Unit Tests for Long Poll Logic**
- Test timeout behavior
- Test immediate return on state change
- Test concurrent long poll requests from different players

**Phase 2: Update Integration Tests**
- Modify `test_real_time_updates_integration.py` to handle async behavior
- Add tests for long poll timeout scenarios
- Test state change detection

**Phase 3: Update BDD Tests**
- Modify step implementations to handle async polling
- Add explicit waits for state changes in BDD steps
- Update timing expectations in feature scenarios

**Phase 4: Browser Tests (Playwright)**
- Test real-world polling behavior
- Verify UI updates occur promptly
- Test network interruption scenarios

### 4. **Implementation Sequence** (TDD RED→GREEN→REFACTOR)

**Step 1: Add State Change Detection (Infrastructure)**
- ✅ RED: Write unit tests for lobby version tracking
- ✅ GREEN: Implement version/change detection in Lobby class
- ✅ REFACTOR: Clean up implementation

**Step 2: Implement Long Poll Endpoint**
- ✅ RED: Write endpoint tests (should wait for changes)
- ✅ GREEN: Implement basic long poll with timeout
- ✅ REFACTOR: Extract common logic

**Step 3: Add Event Notification System**
- ✅ RED: Write tests for event-based wake-up
- ✅ GREEN: Implement asyncio.Event-based notifications
- ✅ REFACTOR: Clean up event handling

**Step 4: Update Frontend**
- ✅ RED: Update BDD tests expecting new behavior
- ✅ GREEN: Change HTMX configuration
- ✅ REFACTOR: Remove old polling code

**Step 5: Update Integration Tests**
- ✅ RED: Add long poll specific tests
- ✅ GREEN: Fix timing in existing tests
- ✅ REFACTOR: Extract test helpers

### 5. **Key Implementation Details**

**Backend (Python/FastAPI):**
```python
# Pseudo-code structure
@app.get("/lobby/status/{player_name}/long-poll")
async def lobby_status_long_poll(
    request: Request,
    player_name: str,
    timeout: int = 30
):
    start_version = lobby_service.get_lobby_version()
    end_time = time.time() + timeout

    while time.time() < end_time:
        # Wait for change event with timeout
        await asyncio.wait_for(
            lobby_service.wait_for_change(start_version),
            timeout=remaining_time
        )

        # State changed, return new state
        return render_lobby_status(...)

    # Timeout - return current state
    return render_lobby_status(...)
```

**State Tracking:**
- Add `_version: int` to Lobby class
- Increment on: player join, leave, status change, game request
- Add `asyncio.Event` for change notifications

**Frontend (HTMX):**
```html
<div hx-get="/lobby/status/{{ player_name }}/long-poll"
     hx-trigger="load"
     hx-swap="innerHTML">
</div>
```

### 6. **Benefits of Long Polling**

- ✅ Reduced server load (fewer requests)
- ✅ Lower network traffic
- ✅ Faster updates (no polling delay)
- ✅ Better user experience
- ✅ Easy migration path (can run both in parallel)

### 7. **Considerations**

- **Backwards compatibility**: Keep short polling endpoint during transition
- **Server resources**: Long polls consume server connections - monitor with multiple users
- **Testing complexity**: Async tests require careful timing
- **Future migration**: Long polling is stepping stone to SSE/WebSockets (noted in TODOs)

---

## Implementation Progress

This plan follows strict TDD/BDD principles with the RED→GREEN→REFACTOR cycle at each step. We'll update tests first to expect new behavior, then implement to make them pass.

### Current Status
- [ ] Step 1: Add State Change Detection (Infrastructure)
- [ ] Step 2: Implement Long Poll Endpoint
- [ ] Step 3: Add Event Notification System
- [ ] Step 4: Update Frontend
- [ ] Step 5: Update Integration Tests
