# Lobby Long-Polling System Documentation

## Overview

The lobby uses a **long-polling architecture** to provide real-time updates to players without requiring WebSockets or Server-Sent Events (SSE). This allows players to see instant updates when:
- New players join the lobby
- Players send/accept/decline game requests
- Players' statuses change
- Game pairings are formed

## Architecture Components

### 1. Core Data Model (`game/lobby.py`)

The `Lobby` class maintains versioned state with async change notification:

```python
class Lobby:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.game_requests: dict[str, GameRequest] = {}
        self.active_games: dict[str, str] = {}
        self.decline_notifications: dict[str, str] = {}
        self.version: int = 0                      # Increments on every state change
        self.change_event: asyncio.Event = asyncio.Event()  # For async notifications
```

**Key Methods:**
- `_notify_change()`: Increments `version` and sets `change_event` (lines 15-18)
- `get_version()`: Returns current version number (lines 162-164)
- `wait_for_change(since_version)`: Async method that blocks until version changes (lines 166-187)

All state-modifying operations call `_notify_change()`:
- `add_player()` (line 22)
- `remove_player()` (line 27)
- `update_player_status()` (line 51)
- `send_game_request()` (line 84)
- `accept_game_request()` (line 114)
- `decline_game_request()` (line 136)

### 2. Service Layer (`services/lobby_service.py`)

The `LobbyService` wraps the `Lobby` class and provides:

- **Validation**: `_validate_and_clean_player_name()` (lines 10-22)
- **Version Access**: `get_lobby_version()` (lines 131-133)
- **Async Waiting**: `wait_for_lobby_change(since_version)` (lines 135-137)
- **Business Logic**: Player management, game requests, notifications

### 3. FastAPI Endpoints (`main.py`)

#### Primary Long-Polling Endpoint

**`GET /lobby/status/{player_name}/long-poll`** (lines 247-287)

**Query Parameters:**
- `timeout`: Maximum wait time in seconds (default: 30)
- `version`: Client's current lobby version (optional)

**Behavior:**
1. **First Request** (`version=None`): Returns current state immediately
2. **Version Changed** (`current_version != version`): Returns new state immediately
3. **Version Matches**: Waits up to `timeout` seconds for changes, then returns

**Response:**
- On change: Returns updated HTML fragment with new lobby state
- On timeout: Returns current HTML fragment (triggers new poll)
- On player not found: Returns 404 error

```python
async def lobby_status_long_poll(
    request: Request, player_name: str, timeout: int = 30, version: int | None = None
) -> HTMLResponse | Response:
    # Validate player exists
    try:
        lobby_service.get_player_status(player_name)
    except ValueError:
        return Response(status_code=404, content=f"Player '{player_name}' not found")

    current_version = lobby_service.get_lobby_version()

    # Return immediately if first call or version changed
    if version is None or current_version != version:
        return await _render_lobby_status(request, player_name)

    # Wait for changes with timeout
    try:
        await asyncio.wait_for(
            lobby_service.wait_for_lobby_change(version), timeout=timeout
        )
        return await _render_lobby_status(request, player_name)
    except asyncio.TimeoutError:
        return await _render_lobby_status(request, player_name)
```

#### Helper Endpoint

**`GET /lobby/status/{player_name}`** (lines 239-244)

Simple endpoint that returns current lobby state without polling. Used for testing and initial page loads.

#### Rendering Helper

**`_render_lobby_status(request, player_name)`** (lines 290-380)

Builds template context with:
- Current lobby version (line 296)
- Player status (lines 312-313)
- Pending game requests (lines 350-363)
- Decline notifications (lines 344-348)
- Available players list (lines 365-372)
- Game pairing redirects (lines 316-338)

**Special Behavior:**
- If player status is `IN_GAME`, returns `HX-Redirect` response to game page (lines 316-338)
- Decline notifications are consumed/cleared on read (line 344)

#### Action Endpoints

These endpoints trigger state changes and return updated lobby fragments:

**`POST /select-opponent`** (lines 178-192)
- Sends game request
- Returns updated lobby status via `_render_lobby_status()`

**`POST /accept-game-request`** (lines 419-450)
- Accepts pending request
- Updates both players to `IN_GAME` status
- Returns `HX-Redirect` to game page

**`POST /decline-game-request`** (lines 383-416)
- Declines pending request
- Returns both players to `AVAILABLE` status
- Shows confirmation message

### 4. HTML Templates

#### Main Lobby Page (`templates/lobby.html`)

The lobby container with initial long-poll trigger:

```html
<div id="lobby-status-container"
     hx-get="/lobby/status/{{ player_name }}/long-poll"
     hx-trigger="load"
     hx-swap="innerHTML">
</div>
```

**HTMX Attributes:**
- `hx-get`: Initial endpoint URL (without version parameter)
- `hx-trigger="load"`: Fires when element loads
- `hx-swap="innerHTML"`: Replaces container content with response

#### Dynamic Content Fragment (`templates/components/lobby_dynamic_content.html`)

The fragment returned by long-polling endpoint:

```html
<div data-testid="lobby-player-status"
     hx-get="/lobby/status/{{ player_name }}/long-poll?version={{ lobby_version }}"
     hx-trigger="load delay:100ms"
     hx-swap="outerHTML">

    <!-- Player status, game requests, available players, etc. -->

</div>
```

**Key HTMX Attributes:**
- `hx-get`: Polling URL **with current version parameter** (line 2)
- `hx-trigger="load delay:100ms"`: Auto-triggers on load with 100ms delay
- `hx-swap="outerHTML"`: Replaces entire element (including itself)

**Important:** The fragment includes its own HTMX attributes, creating a self-renewing polling loop.

**Content Sections:**
1. **Player Status** (lines 6-8): Shows current player's status
2. **Confirmation Message** (lines 10-14): "Game request sent to X"
3. **Pending Request Notification** (lines 16-30): Accept/Decline buttons
4. **Decline Notification** (lines 32-36): "Game request from X declined"
5. **Available Players List** (lines 38-64): Other players with "Select Opponent" buttons

**Interactive Forms:**

All forms use HTMX for seamless updates:

```html
<!-- Accept game request -->
<form hx-post="/accept-game-request"
      hx-target="body"
      hx-swap="innerHTML">
    <button type="submit" data-testid="accept-game-request">Accept</button>
</form>

<!-- Decline game request -->
<form hx-post="/decline-game-request"
      hx-target="[data-testid='lobby-player-status']"
      hx-swap="outerHTML">
    <button type="submit" data-testid="decline-game-request">Decline</button>
</form>

<!-- Select opponent -->
<form hx-post="/select-opponent"
      hx-target="[data-testid='lobby-player-status']"
      hx-swap="outerHTML">
    <button type="submit"
            data-testid="select-opponent-{{ player.name }}"
            {% if player_status in ["Requesting Game", "Pending Response"]
               or player.status != "Available" %}disabled{% endif %}>
        Select Opponent
    </button>
</form>
```

## Long-Polling Flow

### Initial Page Load

1. Browser loads `/lobby?player_name=Alice`
2. Template renders with `lobby-status-container` div
3. HTMX triggers `GET /lobby/status/Alice/long-poll` (no version)
4. Server returns lobby fragment with `version=0`
5. Fragment replaces container content and includes new HTMX trigger

### Continuous Polling Loop

**Client Side (Alice):**
1. Fragment loads with `hx-trigger="load delay:100ms"`
2. After 100ms delay, HTMX fires `GET /lobby/status/Alice/long-poll?version=0`
3. Request hangs (waiting for state change)

**Server Side:**
```python
# Alice's request is waiting...
await lobby_service.wait_for_lobby_change(version=0)
```

**Another Player (Bob) Joins:**
1. Bob logs in with game mode "human"
2. `POST /` endpoint calls `lobby_service.join_lobby("Bob")`
3. `Lobby.add_player()` calls `_notify_change()`
4. Version increments: `0 → 1`
5. `change_event.set()` releases Alice's waiting request

**Alice's Request Completes:**
1. `wait_for_lobby_change()` returns immediately (version changed)
2. Server renders new fragment with `version=1` and Bob in player list
3. Response sent to Alice's browser
4. HTMX swaps content (outerHTML)
5. New fragment loads and triggers another poll with `version=1`

### Timeout Behavior

If no changes occur within 30 seconds:
1. `asyncio.wait_for()` raises `TimeoutError`
2. Server catches timeout and returns current state
3. Fragment re-renders with same version
4. Client immediately re-polls (restart waiting period)

This prevents connection timeouts while maintaining responsiveness.

### State Change Examples

**Player Sends Game Request:**
1. Alice clicks "Select Opponent" for Bob
2. `POST /select-opponent` with `player_name=Alice&opponent_name=Bob`
3. Server calls `lobby_service.send_game_request("Alice", "Bob")`
4. Version increments, `change_event` fires
5. **Both** Alice's and Bob's pending poll requests return immediately
6. Alice sees: "Game request sent to Bob" + status "Requesting Game"
7. Bob sees: "Game request from Alice" with Accept/Decline buttons

**Bob Accepts Request:**
1. Bob clicks "Accept"
2. `POST /accept-game-request` with `player_name=Bob`
3. Server updates both players to `IN_GAME` status
4. Version increments
5. Both pending polls return
6. Alice's response includes `HX-Redirect: /game?player_name=Alice&opponent_name=Bob`
7. Bob's response includes `HX-Redirect: /game?player_name=Bob&opponent_name=Alice`
8. Both browsers navigate to game page

## HTMX Controls Summary

| Attribute | Location | Purpose |
|-----------|----------|---------|
| `hx-get="/lobby/status/{player}/long-poll"` | Main container | Initial poll trigger |
| `hx-get="/lobby/status/{player}/long-poll?version={v}"` | Dynamic fragment | Subsequent polls with version |
| `hx-trigger="load"` | Main container | Fire on initial load |
| `hx-trigger="load delay:100ms"` | Dynamic fragment | Fire after brief delay (prevent rapid loops) |
| `hx-swap="innerHTML"` | Main container | Replace container content only |
| `hx-swap="outerHTML"` | Dynamic fragment | Replace entire fragment (including HTMX attrs) |
| `hx-post="/select-opponent"` | Select opponent form | Send game request |
| `hx-post="/accept-game-request"` | Accept button form | Accept pending request |
| `hx-post="/decline-game-request"` | Decline button form | Decline pending request |
| `hx-target="[data-testid='lobby-player-status']"` | Action forms | Target fragment for swap |
| `HX-Redirect` | Response header | Server-side redirect (game start, leave lobby) |

## Key Design Decisions

### Why Long-Polling vs WebSockets?

1. **Simplicity**: No WebSocket connection management
2. **HTTP Compatibility**: Works with standard HTTP infrastructure
3. **HATEOAS Alignment**: Follows project's hypermedia-driven architecture
4. **Stateless Server**: Each poll is independent (easier testing/debugging)

### Why 100ms Delay?

The `delay:100ms` in `hx-trigger="load delay:100ms"` prevents:
- Rapid-fire requests if rendering is fast
- Browser/server overload
- Race conditions during fragment swap

### Why `outerHTML` Swap?

Using `outerHTML` instead of `innerHTML` ensures:
- HTMX attributes are refreshed with new version number
- Fragment replaces itself completely (clean state)
- No stale attributes from previous renders

### Version-Based Change Detection

Using incrementing version numbers (vs. timestamps or ETags):
- Simple integer comparison
- No clock synchronization issues
- Easy to debug and test
- Monotonically increasing (no ambiguity)

## Testing Considerations

### Unit Tests
- `test_lobby.py`: Tests `Lobby` class state management
- `test_lobby_service.py`: Tests service layer validation/logic
- `test_lobby_events.py`: Tests version/change notification

### Integration Tests
- `test_long_polling.py`: Tests long-poll endpoint behavior
- `test_long_polling_events.py`: Tests event-driven updates
- `test_lobby_notifications_integration.py`: Tests cross-player notifications

### BDD Tests
- `features/long_polling_updates.feature`: User-facing scenarios
- `test_long_polling_steps.py`: Step implementations using Playwright

### Test Reset Endpoint

`POST /test/reset-lobby` (main.py:167-175) clears lobby state for test isolation:
```python
_game_lobby.players.clear()
_game_lobby.game_requests.clear()
_game_lobby.version = 0
_game_lobby.change_event = asyncio.Event()
```

## Performance Characteristics

- **Latency**: Near-instant updates (typically <100ms after state change)
- **Server Load**: One hanging connection per active lobby player
- **Timeout**: 30 seconds (configurable via `timeout` parameter)
- **Scalability**: Limited by max concurrent connections (fine for small lobbies)

## Future Enhancements

Potential improvements noted in code:
- Event-specific notifications (lines 97, 217, 394, 432 in main.py have TODO comments)
- More granular version tracking per player/resource
- Configurable timeout values
- Exponential backoff on errors
