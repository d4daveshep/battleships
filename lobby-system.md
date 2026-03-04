# Lobby System: How It Works

## Overview

The multiplayer lobby is the coordination layer between login and gameplay. After a player logs in and selects "Play against Another Player", they enter the lobby where they can see other online players, send and receive game requests, and transition into a game once a request is accepted.

The lobby is stateful and real-time: all connected clients receive live updates via long polling without any JavaScript.

---

## Domain Objects

### `Player` (`game/player.py`)

Represents a user in the system. Created at login time.

| Field    | Type           | Notes                                              |
|----------|----------------|----------------------------------------------------|
| `name`   | `str`          | Display name chosen at login                       |
| `id`     | `str`          | Auto-generated, URL-safe, cryptographically random (22 chars) |
| `status` | `PlayerStatus` | Current availability state (see below)             |

The `id` is read-only after creation — it cannot be changed.

### `PlayerStatus` (`game/player.py`)

A `StrEnum` with four states:

| Status             | String Value        | Meaning                                                   |
|--------------------|---------------------|-----------------------------------------------------------|
| `AVAILABLE`        | `"Available"`       | In the lobby, can send or receive game requests           |
| `REQUESTING_GAME`  | `"Requesting Game"` | Has sent a game request, waiting for the other to respond |
| `PENDING_RESPONSE` | `"Pending Response"`| Has received a game request, must accept or decline       |
| `IN_GAME`          | `"In Game"`         | Currently in an active game                               |

### `GameRequest` (`game/player.py`)

A dataclass representing a pending request between two players.

| Field         | Type       | Notes                              |
|---------------|------------|------------------------------------|
| `sender_id`   | `str`      | Player ID of who sent the request  |
| `receiver_id` | `str`      | Player ID of who received it       |
| `timestamp`   | `datetime` | When the request was created       |

---

## The `Lobby` Object (`game/lobby.py`)

A single global `Lobby` instance (created in `main.py`) holds all runtime state for the multiplayer system. It is **not** persisted — it resets on server restart.

### Internal Collections

| Attribute               | Type                    | Description                                           |
|-------------------------|-------------------------|-------------------------------------------------------|
| `players`               | `dict[str, Player]`     | All players currently in the lobby, keyed by player ID |
| `game_requests`         | `dict[str, GameRequest]`| Pending game requests, keyed by the **receiver's** ID  |
| `active_games`          | `dict[str, str]`        | Bidirectional map of player ID → opponent ID           |
| `decline_notifications` | `dict[str, str]`        | One-shot notices that a request was declined; keyed by the **sender's** ID |
| `version`               | `int`                   | Monotonically increasing integer; incremented on every state change |
| `change_event`          | `asyncio.Event`         | Used to wake up long-polling connections on state change |

### Key Behaviours

**Version tracking**: Every mutation calls `_notify_change()`, which increments `version` and fires the `asyncio.Event`. Long-polling clients hold open connections until the version changes or they time out.

**Decline notifications are consumed on read**: `get_decline_notification()` uses `dict.pop()` — once a sender reads the notification that their request was declined, it is removed. This prevents stale notifications.

**`active_games` is bidirectional**: Both `player_A → player_B` and `player_B → player_A` are stored, so either player can look up their opponent.

---

## State Machine: Player Status Transitions

```
              login
                │
                ▼
         ┌──────────────┐
         │  AVAILABLE   │◄──────────────────────────────┐
         └──────┬───────┘                               │
                │ send_game_request()                   │
         ┌──────▼───────┐                               │
         │ REQUESTING_  │                               │ decline_game_request()
         │    GAME      │                               │
         └──────────────┘   (other player's view)       │
                            ┌───────────────────┐       │
                            │ PENDING_RESPONSE  │───────┘
                            └────────┬──────────┘
                                     │ accept_game_request()
                            ┌────────▼──────────┐
                            │     IN_GAME        │
                            └────────────────────┘
```

When a game request is **sent**:
- Sender → `REQUESTING_GAME`
- Receiver → `PENDING_RESPONSE`

When the receiver **accepts**:
- Both players → `IN_GAME`
- An entry is added to `active_games` for both

When the receiver **declines**:
- Both players → `AVAILABLE`
- A decline notification is recorded for the sender

---

## Service Layer: `LobbyService` (`services/lobby_service.py`)

`LobbyService` is a thin facade over `Lobby`. Routes never touch `Lobby` directly — they go through `LobbyService`. The service adds:

- Input validation (e.g. player already in lobby)
- Convenience display helpers:
  - `get_player_name(player_id)` — resolves an ID to a display name
  - `get_opponent_name(player_id)` — finds and resolves the opponent's name
  - `get_pending_request_sender_name(player_id)` — name of who sent a request to this player
  - `get_decline_notification_name(player_id)` — name of who declined this player's request
  - `get_player_id_by_name(name)` — reverse lookup from name to ID

---

## HTTP Routes (`routes/lobby.py`)

| Method | Path                         | Description                                                                 |
|--------|------------------------------|-----------------------------------------------------------------------------|
| `GET`  | `/lobby`                     | Renders the full lobby page (shell only, dynamic content loaded separately) |
| `GET`  | `/lobby/status`              | Returns the current `lobby_dynamic_content` component (non-polling)         |
| `GET`  | `/lobby/status/long-poll`    | Long-polling endpoint; holds connection until lobby state changes           |
| `POST` | `/select-opponent`           | Send a game request to the named opponent                                   |
| `POST` | `/accept-game-request`       | Accept an incoming game request, create a game, redirect to ship placement  |
| `POST` | `/decline-game-request`      | Decline an incoming game request, return both players to `AVAILABLE`        |
| `POST` | `/leave-lobby`               | Remove this player from the lobby and redirect to login                     |

---

## Real-Time Updates: Long Polling

The lobby uses **long polling** to deliver real-time updates to all connected clients without WebSockets or JavaScript.

### How It Works

1. The lobby shell page (`lobby.html`) loads and immediately triggers `GET /lobby/status/long-poll` (via HTMX `hx-trigger="load"`).
2. The server checks if `version` matches the client's `?version=` parameter:
   - If **different** (or first call): respond immediately with the current state.
   - If **same**: call `await asyncio.wait_for(lobby.wait_for_change(...), timeout=30)` to hold the connection.
3. When any player action changes lobby state, `_notify_change()` fires the `asyncio.Event`, waking all waiting coroutines simultaneously.
4. The server responds to all waiting clients with fresh HTML.
5. The rendered component includes the **new version number** in its own `hx-get` attribute, so HTMX immediately issues the next long-poll request upon swap.

### Timeout Behaviour

If no state change occurs within 30 seconds, the server responds anyway (with the current state), and the client immediately reconnects. This keeps connections alive through idle periods.

---

## UI Integration

### Page Structure

```
lobby.html (shell)
  └── #lobby-status-container
        hx-get="/lobby/status/long-poll"
        hx-trigger="load"
        hx-swap="innerHTML"
           │
           ▼ (replaced by)
      lobby_dynamic_content.html
        ├── Player status badge
        ├── Confirmation message (if request sent)
        ├── Decline notification (if request was declined)
        ├── Incoming game request alert + Accept/Decline buttons
        └── Available players list (with Select Opponent buttons)
```

### `lobby_dynamic_content.html` Component

This is the only part of the page that updates. It is:
- Rendered server-side with current lobby state
- Contains its own `hx-get` pointing at the next long-poll URL with the current `lobby_version`
- Replaces itself (`hx-swap="outerHTML"`) on each update

### What Gets Shown Based on Player Status

| Player Status      | Shown in UI                                                      |
|--------------------|------------------------------------------------------------------|
| `AVAILABLE`        | List of other players with "Select Opponent" buttons enabled     |
| `REQUESTING_GAME`  | Confirmation message that request was sent; buttons disabled     |
| `PENDING_RESPONSE` | Incoming request alert with Accept / Decline buttons             |
| `IN_GAME`          | Immediate redirect to `/place-ships` (server-side HTMX redirect) |

### Accept/Decline Flow (UI)

- **Accept** (`hx-post="/accept-game-request"`, `hx-target="body"`): On success, the server redirects both players to `/place-ships`. The acceptor gets the redirect from the accept response; the sender gets it on their next long-poll return.
- **Decline** (`hx-post="/decline-game-request"`, `hx-target="[data-testid='lobby-player-status']"`): Re-renders the dynamic content component in place, showing a decline confirmation message.

### "Select Opponent" Button Disabling

Buttons are disabled server-side in the template when either:
- The current player's status is `Requesting Game` or `Pending Response`
- The target player's status is not `Available`

This prevents double-requests and race conditions without any client-side JavaScript.

---

## Constraints and Edge Cases

- **One request per receiver**: `game_requests` is keyed by `receiver_id`, so a player can only hold one incoming request at a time.
- **Both parties must be `AVAILABLE`**: `send_game_request()` raises `ValueError` if either player is not available at the moment of the call.
- **Decline notifications are single-use**: They are consumed when read (`dict.pop`), so they display once and then disappear.
- **`IN_GAME` players are hidden from the available list**: The `_add_available_players` helper filters out `IN_GAME` players, though they remain in `lobby.players`.
- **No persistence**: All state is in-memory. A server restart clears the lobby.
