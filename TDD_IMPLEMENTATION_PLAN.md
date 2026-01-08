# Comprehensive TDD Implementation Plan: Two-Player Simultaneous Multi-Shot Gameplay

## Executive Summary

This plan breaks down the 48 scenarios from `features/two_player_gameplay.feature` into **7 manageable phases**, following strict RED-GREEN-REFACTOR discipline. Each phase builds incrementally on the previous one, starting with core domain models and progressing through services, endpoints, and UI components.

**Estimated Timeline**: 7-10 development sessions (1-2 phases per session)

---

## Phase Breakdown Overview

| Phase | Focus Area | Scenarios | Complexity |
|-------|-----------|-----------|------------|
| **Phase 1** | Round & Shot Domain Models | 8 scenarios | Low |
| **Phase 2** | Shot Aiming & Validation | 10 scenarios | Medium |
| **Phase 3** | Simultaneous Shot Resolution | 8 scenarios | High |
| **Phase 4** | Hit Feedback & Tracking | 9 scenarios | Medium |
| **Phase 5** | Ship Sinking & Game End | 8 scenarios | Medium |
| **Phase 6** | Real-Time Updates & Long-Polling | 5 scenarios | High |
| **Phase 7** | Edge Cases & Error Handling | 10 scenarios | Medium |

---

## Domain Model Enhancements Needed

### New Classes Required

```python
# game/round.py
@dataclass
class Shot:
    """Represents a single shot fired at a coordinate"""
    coord: Coord
    round_number: int
    player_id: str
    
@dataclass  
class HitResult:
    """Result of a shot hitting a ship"""
    ship_type: ShipType
    coord: Coord
    is_sinking_hit: bool  # Was this the hit that sunk the ship?

@dataclass
class RoundResult:
    """Complete results for a round after both players fire"""
    round_number: int
    player_shots: dict[str, list[Shot]]  # player_id -> shots
    hits_made: dict[str, list[HitResult]]  # player_id -> hits they made
    ships_sunk: dict[str, list[ShipType]]  # player_id -> ships they sunk
    game_over: bool
    winner_id: str | None
    is_draw: bool

class Round:
    """Manages a single round of gameplay"""
    def __init__(self, round_number: int, game_id: str):
        self.round_number: int = round_number
        self.game_id: str = game_id
        self.aimed_shots: dict[str, list[Coord]] = {}  # player_id -> aimed coords
        self.submitted_players: set[str] = set()
        self.is_resolved: bool = False
        self.result: RoundResult | None = None
```

### Enhancements to Existing Classes

```python
# game/model.py - GameBoard enhancements
class GameBoard:
    def __init__(self) -> None:
        self.ships: list[Ship] = []
        # NEW: Track shots with round numbers
        self.shots_received: dict[Coord, int] = {}  # coord -> round_number
        self.shots_fired: dict[Coord, int] = {}  # coord -> round_number
        # NEW: Track hits on ships
        self.ship_hits: dict[ShipType, list[tuple[Coord, int]]] = {}  # ship -> [(coord, round)]
        
    def record_shot_received(self, coord: Coord, round_number: int) -> None:
        """Record a shot received from opponent"""
        
    def record_shot_fired(self, coord: Coord, round_number: int) -> None:
        """Record a shot fired at opponent"""
        
    def record_hit(self, ship_type: ShipType, coord: Coord, round_number: int) -> None:
        """Record a hit on a ship"""
        
    def is_ship_sunk(self, ship_type: ShipType) -> bool:
        """Check if a ship has been completely sunk"""
        
    def get_unsunk_ships(self) -> list[Ship]:
        """Get list of ships that haven't been sunk"""
        
    def calculate_shots_available(self) -> int:
        """Calculate shots available based on unsunk ships"""

# game/model.py - Ship enhancements  
@dataclass
class Ship:
    ship_type: ShipType
    positions: list[Coord] = field(default_factory=list)
    hits: list[tuple[Coord, int]] = field(default_factory=list)  # NEW: (coord, round)
    
    @property
    def is_sunk(self) -> bool:
        """Check if ship is completely sunk"""
        return len(self.hits) >= self.length

# game/game_service.py - Game enhancements
class Game:
    def __init__(self, player_1: Player, game_mode: GameMode, player_2: Player | None = None):
        # ... existing fields ...
        # NEW: Round tracking
        self.current_round: Round | None = None
        self.round_history: list[RoundResult] = []
        self.winner_id: str | None = None
        self.is_draw: bool = False
```

---

## Phase 1: Round & Shot Domain Models

**Goal**: Establish core domain models for rounds, shots, and hit tracking.

### RED-GREEN-REFACTOR Cycles

#### Cycle 1.1: Round Model Creation
**RED**: Write unit test for `Round` class initialization
```python
# tests/unit/test_round.py
def test_round_initialization():
    round = Round(round_number=1, game_id="game123")
    assert round.round_number == 1
    assert round.game_id == "game123"
    assert round.aimed_shots == {}
    assert round.submitted_players == set()
    assert round.is_resolved is False
```

**GREEN**: Create `game/round.py` with minimal `Round` class

**REFACTOR**: Add type hints, docstrings

#### Cycle 1.2: Shot Model Creation
**RED**: Write unit test for `Shot` dataclass
```python
def test_shot_creation():
    shot = Shot(coord=Coord.A1, round_number=1, player_id="p1")
    assert shot.coord == Coord.A1
    assert shot.round_number == 1
```

**GREEN**: Create `Shot` dataclass in `game/round.py`

**REFACTOR**: Ensure proper type hints

#### Cycle 1.3: GameBoard Shot Recording
**RED**: Write unit test for recording shots received
```python
def test_record_shot_received():
    board = GameBoard()
    board.record_shot_received(Coord.A1, round_number=1)
    assert board.shots_received[Coord.A1] == 1
```

**GREEN**: Implement `record_shot_received()` method

**REFACTOR**: Extract common patterns

#### Cycle 1.4: Shots Available Calculation
**RED**: Write unit test for calculating shots available
```python
def test_calculate_shots_available_all_ships():
    board = GameBoard()
    # Place all 5 ships
    # ...
    assert board.calculate_shots_available() == 6
```

**GREEN**: Implement `calculate_shots_available()` method

**REFACTOR**: Clean up logic

### BDD Scenarios to Implement
- Scenario: Game starts at Round 1 with 6 shots available

### Delegation Strategy
- **@fastapi-service-builder**: Not needed yet (domain models only)
- **@type-hint-enforcer**: Review after all models created

### Success Criteria
- [ ] All unit tests pass for Round, Shot, HitResult, RoundResult
- [ ] GameBoard can track shots with round numbers
- [ ] Shots available calculation works correctly
- [ ] Type hints comprehensive and verified

---

## Phase 2: Shot Aiming & Validation

**Goal**: Implement shot aiming UI and validation logic.

### RED-GREEN-REFACTOR Cycles

#### Cycle 2.1: Aim Shot Service Method
**RED**: Write unit test for aiming a shot
```python
# tests/unit/test_gameplay_service.py
def test_aim_shot_valid():
    service = GameplayService()
    result = service.aim_shot(game_id="g1", player_id="p1", coord=Coord.A1)
    assert result.success is True
```

**GREEN**: Create `services/gameplay_service.py` with `aim_shot()` method

**REFACTOR**: Add validation logic

#### Cycle 2.2: Duplicate Shot Validation
**RED**: Write unit test for duplicate shot detection
```python
def test_aim_shot_duplicate_in_round():
    service = GameplayService()
    service.aim_shot(game_id="g1", player_id="p1", coord=Coord.A1)
    result = service.aim_shot(game_id="g1", player_id="p1", coord=Coord.A1)
    assert result.success is False
    assert "already selected" in result.error_message
```

**GREEN**: Add duplicate detection to `aim_shot()`

**REFACTOR**: Extract validation to separate method

#### Cycle 2.3: Shot Limit Validation
**RED**: Write unit test for shot limit
```python
def test_aim_shot_exceeds_limit():
    service = GameplayService()
    # Aim 6 shots
    for i in range(6):
        service.aim_shot(game_id="g1", player_id="p1", coord=...)
    # Try 7th shot
    result = service.aim_shot(game_id="g1", player_id="p1", coord=Coord.G1)
    assert result.success is False
```

**GREEN**: Add shot limit validation

**REFACTOR**: Clean up validation logic

#### Cycle 2.4: Aim Shot Endpoint
**RED**: Write integration test for `POST /game/{id}/aim-shot`
```python
# tests/endpoint/test_gameplay_endpoints.py
def test_aim_shot_endpoint(client):
    response = client.post("/game/g1/aim-shot", json={"coord": "A1"})
    assert response.status_code == 200
```

**GREEN**: Create endpoint in `main.py`

**REFACTOR**: Extract to service layer

#### Cycle 2.5: Aiming UI Component
**RED**: Write BDD test for aiming UI
```python
# tests/bdd/test_gameplay_steps.py
@when('I select coordinate "A1" to aim at')
def step_select_coordinate(page, coord):
    page.click(f'[data-coord="{coord}"]')
```

**GREEN**: Create HTMX template for aiming interface

**REFACTOR**: Extract reusable components

### BDD Scenarios to Implement
- Scenario: Selecting multiple shot coordinates for aiming
- Scenario: Cannot select the same coordinate twice in aiming phase
- Scenario: Cannot select more shots than available
- Scenario: Can fire fewer shots than available
- Scenario: Cannot fire at coordinates already fired at in previous rounds
- Scenario: Cannot fire at invalid coordinates
- Scenario: Must fire at unique coordinates within the same round

### Delegation Strategy
- **@fastapi-service-builder**: Create `GameplayService` with `aim_shot()`, `get_aimed_shots()`, `clear_aimed_shots()`
- **@htmx-template-builder**: Create aiming UI component (clickable opponent board)
- **@dual-test-implementer**: Implement BDD step definitions for aiming scenarios
- **@css-theme-designer**: Style aiming interface (selected shots, disabled cells)

### Success Criteria
- [ ] Unit tests pass for `GameplayService.aim_shot()`
- [ ] Integration tests pass for `/game/{id}/aim-shot` endpoint
- [ ] BDD scenarios pass (FastAPI + Playwright)
- [ ] UI allows selecting/deselecting shots
- [ ] Validation prevents invalid shots

---

## Phase 3: Simultaneous Shot Resolution

**Goal**: Implement simultaneous shot firing and round resolution.

### RED-GREEN-REFACTOR Cycles

#### Cycle 3.1: Fire Shots Service Method
**RED**: Write unit test for firing shots
```python
def test_fire_shots():
    service = GameplayService()
    # Aim 3 shots
    service.aim_shot(game_id="g1", player_id="p1", coord=Coord.A1)
    service.aim_shot(game_id="g1", player_id="p1", coord=Coord.B2)
    service.aim_shot(game_id="g1", player_id="p1", coord=Coord.C3)
    # Fire
    result = service.fire_shots(game_id="g1", player_id="p1")
    assert result.success is True
    assert result.waiting_for_opponent is True
```

**GREEN**: Implement `fire_shots()` method

**REFACTOR**: Extract submission logic

#### Cycle 3.2: Resolve Round Logic
**RED**: Write unit test for round resolution
```python
def test_resolve_round_both_players_fired():
    service = GameplayService()
    # Player 1 fires
    service.fire_shots(game_id="g1", player_id="p1")
    # Player 2 fires
    result = service.fire_shots(game_id="g1", player_id="p2")
    # Round should resolve
    assert result.round_resolved is True
    assert result.round_result is not None
```

**GREEN**: Implement `resolve_round()` method

**REFACTOR**: Extract hit detection logic

#### Cycle 3.3: Hit Detection Logic
**RED**: Write unit test for detecting hits
```python
def test_detect_hits():
    # Setup: Player 1 has Carrier at A1-A5
    # Player 2 fires at A1, A2, B1
    result = service.resolve_round(game_id="g1")
    hits = result.hits_made["p2"]
    assert len(hits) == 2  # A1 and A2 hit Carrier
    assert hits[0].ship_type == ShipType.CARRIER
```

**GREEN**: Implement hit detection in `resolve_round()`

**REFACTOR**: Extract to `_detect_hits()` helper

#### Cycle 3.4: Fire Shots Endpoint
**RED**: Write integration test for `POST /game/{id}/fire-shots`
```python
def test_fire_shots_endpoint(client):
    response = client.post("/game/g1/fire-shots")
    assert response.status_code == 200
    assert response.json()["waiting_for_opponent"] is True
```

**GREEN**: Create endpoint in `main.py`

**REFACTOR**: Move logic to service

#### Cycle 3.5: Waiting UI Component
**RED**: Write BDD test for waiting state
```python
@then('I should see "Waiting for opponent to fire..." displayed')
def step_see_waiting_message(page):
    assert page.locator('[data-testid="waiting-message"]').is_visible()
```

**GREEN**: Create waiting state template

**REFACTOR**: Extract loading indicator component

### BDD Scenarios to Implement
- Scenario: Both players fire shots simultaneously in the same round
- Scenario: Waiting for opponent to fire their shots
- Scenario: Opponent fires before me
- Scenario: Round number increments after both players fire
- Scenario: Round number stays same while waiting for opponent

### Delegation Strategy
- **@fastapi-service-builder**: Create `fire_shots()`, `resolve_round()`, `_detect_hits()` methods
- **@htmx-template-builder**: Create waiting state UI, round results display
- **@dual-test-implementer**: Implement BDD step definitions for firing scenarios
- **@css-theme-designer**: Style waiting indicator, round transition

### Success Criteria
- [ ] Unit tests pass for `fire_shots()` and `resolve_round()`
- [ ] Integration tests pass for `/game/{id}/fire-shots` endpoint
- [ ] BDD scenarios pass for simultaneous firing
- [ ] Round resolves correctly when both players fire
- [ ] UI shows waiting state appropriately

---

## Phase 4: Hit Feedback & Tracking

**Goal**: Implement ship-based hit feedback and Hits Made area.

### RED-GREEN-REFACTOR Cycles

#### Cycle 4.1: Hit Feedback Calculation
**RED**: Write unit test for hit feedback
```python
def test_calculate_hit_feedback():
    # Player fires at A1, A2, B1
    # A1 and A2 hit Carrier
    feedback = service.calculate_hit_feedback(game_id="g1", player_id="p1")
    assert feedback["Carrier"] == 2
    assert "Destroyer" not in feedback
```

**GREEN**: Implement `calculate_hit_feedback()` method

**REFACTOR**: Extract ship hit counting logic

#### Cycle 4.2: Hits Made Area Data Structure
**RED**: Write unit test for Hits Made tracking
```python
def test_hits_made_tracking():
    board = GameBoard()
    board.record_hit(ShipType.CARRIER, Coord.A1, round_number=1)
    board.record_hit(ShipType.CARRIER, Coord.A2, round_number=1)
    hits = board.get_hits_by_ship(ShipType.CARRIER)
    assert len(hits) == 2
    assert hits[0] == (Coord.A1, 1)
```

**GREEN**: Implement `record_hit()` and `get_hits_by_ship()` methods

**REFACTOR**: Clean up data structures

#### Cycle 4.3: Round Results Display
**RED**: Write integration test for round results endpoint
```python
def test_get_round_results(client):
    response = client.get("/game/g1/round-results/1")
    assert response.status_code == 200
    assert "hits_made" in response.json()
```

**GREEN**: Create `/game/{id}/round-results/{round}` endpoint

**REFACTOR**: Extract formatting logic

#### Cycle 4.4: Hits Made UI Component
**RED**: Write BDD test for Hits Made area
```python
@then('I should see "Carrier: 2 hits" in the hits summary')
def step_see_carrier_hits(page):
    assert page.locator('[data-ship="carrier"]').inner_text() == "2 hits"
```

**GREEN**: Create Hits Made area template component

**REFACTOR**: Extract ship hit display component

#### Cycle 4.5: Shots Fired Board Display
**RED**: Write BDD test for shots fired board
```python
@then('coordinates "A1", "B2", "C3" should be marked with "1" on my Shots Fired board')
def step_see_shots_marked(page):
    assert page.locator('[data-coord="A1"]').inner_text() == "1"
```

**GREEN**: Update shots fired board template

**REFACTOR**: Extract round number display logic

### BDD Scenarios to Implement
- Scenario: Hitting opponent's ship shows which ship was hit, not coordinates
- Scenario: All shots miss in a round
- Scenario: Hits Made area tracks cumulative hits across rounds
- Scenario: Receiving hits shows which of my ships were hit
- Scenario: Shots fired are marked with round numbers on Shots Fired board
- Scenario: Shots fired in different rounds are shown on the Shots Fired board
- Scenario: Shots received are marked with round numbers on My Ships board
- Scenario: Hits Made area shows ship-level hit tracking
- Scenario: Both boards are visible simultaneously

### Delegation Strategy
- **@fastapi-service-builder**: Create `calculate_hit_feedback()`, `get_round_results()` methods
- **@htmx-template-builder**: Create Hits Made area component, update board displays
- **@dual-test-implementer**: Implement BDD step definitions for hit feedback scenarios
- **@css-theme-designer**: Style Hits Made area, round number markers

### Success Criteria
- [ ] Unit tests pass for hit feedback calculation
- [ ] Integration tests pass for round results endpoint
- [ ] BDD scenarios pass for hit feedback display
- [ ] Hits Made area shows ship-level tracking
- [ ] Boards show round numbers for shots

---

## Phase 5: Ship Sinking & Game End

**Goal**: Implement ship sinking detection and win/loss/draw conditions.

### RED-GREEN-REFACTOR Cycles

#### Cycle 5.1: Ship Sinking Detection
**RED**: Write unit test for ship sinking
```python
def test_detect_ship_sunk():
    board = GameBoard()
    # Place Destroyer at A1, A2
    ship = Ship(ShipType.DESTROYER)
    board.place_ship(ship, Coord.A1, Orientation.HORIZONTAL)
    # Record hits
    board.record_hit(ShipType.DESTROYER, Coord.A1, round_number=1)
    board.record_hit(ShipType.DESTROYER, Coord.A2, round_number=2)
    assert board.is_ship_sunk(ShipType.DESTROYER) is True
```

**GREEN**: Implement `is_ship_sunk()` method

**REFACTOR**: Extract hit counting logic

#### Cycle 5.2: Shots Available Update
**RED**: Write unit test for shots available after sinking
```python
def test_shots_available_after_sinking():
    board = GameBoard()
    # Place all ships
    # Sink Destroyer (1 shot)
    board.mark_ship_sunk(ShipType.DESTROYER)
    assert board.calculate_shots_available() == 5
```

**GREEN**: Update `calculate_shots_available()` to account for sunk ships

**REFACTOR**: Clean up logic

#### Cycle 5.3: Win Condition Detection
**RED**: Write unit test for win detection
```python
def test_detect_win():
    game = Game(player_1=p1, player_2=p2, game_mode=GameMode.TWO_PLAYER)
    # Sink all of player 2's ships
    for ship_type in ShipType:
        game.board[p2].mark_ship_sunk(ship_type)
    result = service.check_game_over(game_id=game.id)
    assert result.game_over is True
    assert result.winner_id == p1.id
```

**GREEN**: Implement `check_game_over()` method

**REFACTOR**: Extract win/loss/draw logic

#### Cycle 5.4: Draw Condition Detection
**RED**: Write unit test for draw detection
```python
def test_detect_draw():
    # Both players sink all ships in same round
    result = service.resolve_round(game_id="g1")
    assert result.is_draw is True
    assert result.winner_id is None
```

**GREEN**: Add draw detection to `resolve_round()`

**REFACTOR**: Clean up game over logic

#### Cycle 5.5: Game Over UI
**RED**: Write BDD test for game over display
```python
@then('I should see "You Win!" displayed')
def step_see_win_message(page):
    assert page.locator('[data-testid="game-result"]').inner_text() == "You Win!"
```

**GREEN**: Create game over template

**REFACTOR**: Extract result display component

### BDD Scenarios to Implement
- Scenario: Shots available decreases when opponent ship is sunk
- Scenario: Shots available decreases when my ship is sunk
- Scenario: Multiple ships sunk reduces shots proportionally
- Scenario: All ships sunk means zero shots available
- Scenario: Sinking an opponent's ship
- Scenario: Having my ship sunk by opponent
- Scenario: Multiple ships sunk in the same round
- Scenario: Both players sink ships in the same round
- Scenario: Winning the game by sinking all opponent ships
- Scenario: Losing the game when all my ships are sunk
- Scenario: Draw when both players sink all ships in the same round

### Delegation Strategy
- **@fastapi-service-builder**: Create `check_game_over()`, update `resolve_round()` with sinking logic
- **@htmx-template-builder**: Create game over display, ship sunk notifications
- **@dual-test-implementer**: Implement BDD step definitions for sinking scenarios
- **@css-theme-designer**: Style game over screen, sunk ship indicators

### Success Criteria
- [ ] Unit tests pass for ship sinking detection
- [ ] Unit tests pass for win/loss/draw detection
- [ ] Integration tests pass for game over conditions
- [ ] BDD scenarios pass for all end game conditions
- [ ] UI displays game results correctly

---

## Phase 6: Real-Time Updates & Long-Polling

**Goal**: Implement long-polling for real-time round completion updates.

### RED-GREEN-REFACTOR Cycles

#### Cycle 6.1: Round Version Tracking
**RED**: Write unit test for round version tracking
```python
def test_round_version_increments():
    game = Game(player_1=p1, player_2=p2, game_mode=GameMode.TWO_PLAYER)
    initial_version = game.get_round_version()
    # Resolve round
    service.resolve_round(game_id=game.id)
    assert game.get_round_version() > initial_version
```

**GREEN**: Add version tracking to `Game` class

**REFACTOR**: Extract version management

#### Cycle 6.2: Wait for Round Completion
**RED**: Write unit test for waiting
```python
async def test_wait_for_round_completion():
    game = Game(player_1=p1, player_2=p2, game_mode=GameMode.TWO_PLAYER)
    version = game.get_round_version()
    # Start waiting in background
    wait_task = asyncio.create_task(game.wait_for_round_change(version))
    # Resolve round
    service.resolve_round(game_id=game.id)
    # Wait should complete
    await asyncio.wait_for(wait_task, timeout=1.0)
```

**GREEN**: Implement `wait_for_round_change()` method

**REFACTOR**: Clean up async logic

#### Cycle 6.3: Long-Polling Endpoint
**RED**: Write integration test for long-polling
```python
async def test_long_poll_endpoint(client):
    # Start long-poll request
    response_task = asyncio.create_task(
        client.get("/game/g1/long-poll?version=1")
    )
    # Trigger round resolution
    await client.post("/game/g1/fire-shots")
    # Long-poll should return
    response = await response_task
    assert response.status_code == 200
```

**GREEN**: Create `/game/{id}/long-poll` endpoint

**REFACTOR**: Extract timeout handling

#### Cycle 6.4: HTMX Long-Polling Integration
**RED**: Write BDD test for auto-update
```python
@when('my opponent fires their shots')
@then('I should see the round results within 5 seconds')
def step_see_results_auto(page):
    # Wait for HTMX to update
    page.wait_for_selector('[data-testid="round-results"]', timeout=5000)
```

**GREEN**: Add HTMX long-polling to template

**REFACTOR**: Extract polling component

#### Cycle 6.5: Connection Resilience
**RED**: Write unit test for connection timeout
```python
async def test_long_poll_timeout():
    response = await client.get("/game/g1/long-poll?version=1", timeout=31)
    assert response.status_code == 204  # No change
```

**GREEN**: Add timeout handling to long-poll endpoint

**REFACTOR**: Clean up error handling

### BDD Scenarios to Implement
- Scenario: Real-time update when opponent fires
- Scenario: Real-time update when both players fire simultaneously
- Scenario: Long polling connection resilience

### Delegation Strategy
- **@fastapi-service-builder**: Create `wait_for_round_change()`, long-poll endpoint
- **@htmx-template-builder**: Add HTMX long-polling attributes to templates
- **@dual-test-implementer**: Implement BDD step definitions for real-time scenarios

### Success Criteria
- [ ] Unit tests pass for version tracking
- [ ] Integration tests pass for long-polling endpoint
- [ ] BDD scenarios pass for real-time updates
- [ ] Long-polling works with 30s timeout
- [ ] Connection resilience tested

---

## Phase 7: Edge Cases & Error Handling

**Goal**: Handle edge cases, errors, and special scenarios.

### RED-GREEN-REFACTOR Cycles

#### Cycle 7.1: Game State Persistence
**RED**: Write unit test for game state retrieval
```python
def test_get_game_state():
    # Create game, play 3 rounds
    state = service.get_game_state(game_id="g1", player_id="p1")
    assert state.current_round == 4
    assert len(state.round_history) == 3
```

**GREEN**: Implement `get_game_state()` method

**REFACTOR**: Extract state serialization

#### Cycle 7.2: Network Error Handling
**RED**: Write integration test for network error
```python
def test_fire_shots_network_error(client, monkeypatch):
    # Simulate network failure
    monkeypatch.setattr(service, "fire_shots", lambda *args: raise_error())
    response = client.post("/game/g1/fire-shots")
    assert response.status_code == 500
    assert "Connection lost" in response.json()["detail"]
```

**GREEN**: Add error handling to endpoints

**REFACTOR**: Extract error response formatting

#### Cycle 7.3: Opponent Disconnect Handling
**RED**: Write unit test for disconnect detection
```python
def test_detect_opponent_disconnect():
    # Opponent hasn't fired in 5 minutes
    result = service.check_opponent_status(game_id="g1", player_id="p1")
    assert result.opponent_disconnected is True
```

**GREEN**: Implement disconnect detection

**REFACTOR**: Extract timeout logic

#### Cycle 7.4: Surrender Functionality
**RED**: Write unit test for surrender
```python
def test_surrender_game():
    result = service.surrender_game(game_id="g1", player_id="p1")
    assert result.game_over is True
    assert result.winner_id == "p2"  # Opponent wins
```

**GREEN**: Implement `surrender_game()` method

**REFACTOR**: Clean up game termination logic

#### Cycle 7.5: Page Refresh State Recovery
**RED**: Write BDD test for page refresh
```python
@when('I refresh the page')
@then('I should see "Round 5" displayed')
def step_refresh_maintains_state(page):
    page.reload()
    assert page.locator('[data-testid="round-indicator"]').inner_text() == "Round 5"
```

**GREEN**: Ensure state loaded on page load

**REFACTOR**: Extract state loading logic

### BDD Scenarios to Implement
- Scenario: Refreshing page maintains game state
- Scenario: Reconnecting to an in-progress game
- Scenario: First round of the game
- Scenario: Multiple hits on same ship in one round
- Scenario: Hitting multiple different ships in one round
- Scenario: Firing fewer shots than available
- Scenario: Handling network error during shot submission
- Scenario: Opponent disconnects during game
- Scenario: Opponent reconnects after disconnection
- Scenario: Player surrenders the game

### Delegation Strategy
- **@fastapi-service-builder**: Create `get_game_state()`, `surrender_game()`, disconnect detection
- **@htmx-template-builder**: Add error messages, surrender button, disconnect UI
- **@dual-test-implementer**: Implement BDD step definitions for edge cases
- **@css-theme-designer**: Style error messages, disconnect warnings

### Success Criteria
- [ ] Unit tests pass for all edge cases
- [ ] Integration tests pass for error handling
- [ ] BDD scenarios pass for special cases
- [ ] Page refresh maintains state
- [ ] Surrender works correctly

---

## Service Layer Architecture

### New Service: `services/gameplay_service.py`

```python
class GameplayService:
    def __init__(self, game_service: GameService):
        self.game_service = game_service
        self.active_rounds: dict[str, Round] = {}  # game_id -> Round
        
    # Phase 2: Aiming
    def aim_shot(self, game_id: str, player_id: str, coord: Coord) -> AimShotResult:
        """Add a shot to the aiming queue for current round"""
        
    def get_aimed_shots(self, game_id: str, player_id: str) -> list[Coord]:
        """Get currently aimed shots for player"""
        
    def clear_aimed_shot(self, game_id: str, player_id: str, coord: Coord) -> bool:
        """Remove a shot from aiming queue"""
        
    # Phase 3: Firing
    def fire_shots(self, game_id: str, player_id: str) -> FireShotsResult:
        """Submit aimed shots and wait for opponent"""
        
    def resolve_round(self, game_id: str) -> RoundResult:
        """Process both players' shots and determine hits/sinks"""
        
    def _detect_hits(self, game_id: str, player_id: str, shots: list[Coord]) -> list[HitResult]:
        """Detect which shots hit which ships"""
        
    # Phase 4: Feedback
    def calculate_hit_feedback(self, game_id: str, player_id: str, round_number: int) -> dict[str, int]:
        """Calculate ship-level hit feedback for a round"""
        
    def get_round_results(self, game_id: str, round_number: int) -> RoundResult:
        """Get results for a specific round"""
        
    # Phase 5: Game End
    def check_game_over(self, game_id: str) -> GameOverResult:
        """Check if game is over and determine winner"""
        
    def surrender_game(self, game_id: str, player_id: str) -> GameOverResult:
        """Surrender the game"""
        
    # Phase 6: Real-Time
    async def wait_for_round_change(self, game_id: str, since_version: int) -> None:
        """Wait for round to resolve (long-polling)"""
        
    def get_round_version(self, game_id: str) -> int:
        """Get current round version for change detection"""
        
    # Phase 7: State
    def get_game_state(self, game_id: str, player_id: str) -> GameState:
        """Get complete game state for player"""
```

---

## API Endpoints

### Phase 2: Aiming
- `POST /game/{game_id}/aim-shot` - Add shot to aiming queue
  - Body: `{"coord": "A1"}`
  - Returns: `{"success": true, "aimed_count": 3, "shots_available": 6}`

- `DELETE /game/{game_id}/aim-shot/{coord}` - Remove shot from aiming queue
  - Returns: `{"success": true, "aimed_count": 2}`

- `GET /game/{game_id}/aimed-shots` - Get currently aimed shots
  - Returns: `{"coords": ["A1", "B2", "C3"], "count": 3}`

### Phase 3: Firing
- `POST /game/{game_id}/fire-shots` - Submit aimed shots
  - Returns: `{"success": true, "waiting_for_opponent": true, "round_number": 1}`

- `GET /game/{game_id}/round-status` - Check if round resolved
  - Returns: `{"resolved": false, "waiting_for": ["player2_id"]}`

### Phase 4: Feedback
- `GET /game/{game_id}/round-results/{round_number}` - Get round results
  - Returns: `{"hits_made": {"Carrier": 2}, "ships_sunk": ["Destroyer"], ...}`

### Phase 5: Game End
- `POST /game/{game_id}/surrender` - Surrender the game
  - Returns: `{"game_over": true, "winner_id": "opponent_id"}`

### Phase 6: Real-Time
- `GET /game/{game_id}/long-poll?version={version}` - Wait for round change
  - Returns: `{"version": 2, "round_resolved": true}` or 204 No Content after timeout

### Phase 7: State
- `GET /game/{game_id}/state` - Get complete game state
  - Returns: Full game state including boards, rounds, history

---

## HTMX/Template Components

### Phase 2: Aiming UI
**Component**: `templates/components/aiming_board.html`
- Clickable opponent board cells
- Visual feedback for selected shots
- Shots aimed counter: "Shots Aimed: 3/6"
- Fire Shots button (enabled when shots aimed)

### Phase 3: Firing UI
**Component**: `templates/components/waiting_state.html`
- "Waiting for opponent to fire..." message
- Loading spinner/indicator
- Disabled aiming interface

**Component**: `templates/components/round_results.html`
- Round number display
- Hits made summary
- Ships sunk notifications
- Transition to next round

### Phase 4: Hit Feedback UI
**Component**: `templates/components/hits_made_area.html`
- 5 ship rows (Carrier, Battleship, Cruiser, Submarine, Destroyer)
- Round number markers for each hit
- "SUNK" indicator for sunk ships
- Total hits counter per ship

**Component**: `templates/components/shots_fired_board.html`
- 10x10 grid with round numbers
- Hit/miss indicators
- Color coding by round

**Component**: `templates/components/my_ships_board.html`
- Ship positions visible
- Shots received with round numbers
- Hit/miss indicators on ships
- Sunk ship highlighting

### Phase 5: Game End UI
**Component**: `templates/components/game_over.html`
- Win/Loss/Draw message
- Final statistics
- "Return to Lobby" button

### Phase 6: Real-Time UI
**HTMX Attributes**: Add to waiting state component
```html
<div hx-get="/game/{game_id}/long-poll?version={version}"
     hx-trigger="load"
     hx-swap="outerHTML"
     hx-target="#game-container">
```

### Phase 7: Error Handling UI
**Component**: `templates/components/error_message.html`
- Network error display
- Opponent disconnect warning
- Retry button

**Component**: `templates/components/surrender_button.html`
- Surrender button with confirmation
- Warning message

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
**Phase 1**: 
- `test_round.py` - Round, Shot, HitResult, RoundResult models
- `test_game_board.py` - Shot recording, hit tracking, shots available

**Phase 2**:
- `test_gameplay_service.py` - Aiming logic, validation

**Phase 3**:
- `test_gameplay_service.py` - Firing, round resolution, hit detection

**Phase 4**:
- `test_gameplay_service.py` - Hit feedback calculation
- `test_game_board.py` - Hits Made tracking

**Phase 5**:
- `test_gameplay_service.py` - Ship sinking, game over detection

**Phase 6**:
- `test_gameplay_service.py` - Version tracking, async waiting

**Phase 7**:
- `test_gameplay_service.py` - State management, error handling

### Integration Tests (`tests/endpoint/`)
**Phase 2**:
- `test_gameplay_endpoints.py` - Aiming endpoints

**Phase 3**:
- `test_gameplay_endpoints.py` - Firing endpoints

**Phase 4**:
- `test_gameplay_endpoints.py` - Round results endpoints

**Phase 5**:
- `test_gameplay_endpoints.py` - Surrender endpoint

**Phase 6**:
- `test_gameplay_endpoints.py` - Long-polling endpoint

**Phase 7**:
- `test_gameplay_endpoints.py` - State endpoint, error scenarios

### BDD Tests (`tests/bdd/`)
**All Phases**: Implement scenarios from `features/two_player_gameplay.feature`
- `test_gameplay_steps_fastapi.py` - FastAPI step definitions
- `test_gameplay_steps_playwright.py` - Playwright step definitions

---

## Implementation Order (Step-by-Step)

### Session 1: Phase 1 (Foundation)
1. Create `game/round.py` with domain models
2. Write unit tests for Round, Shot, HitResult, RoundResult
3. Enhance GameBoard with shot tracking methods
4. Write unit tests for shot recording
5. Implement shots available calculation
6. Run all tests, refactor
7. **Delegate to @type-hint-enforcer** for verification

### Session 2: Phase 2 (Aiming - Part 1)
1. Create `services/gameplay_service.py`
2. Write unit tests for `aim_shot()` method
3. Implement `aim_shot()` with basic validation
4. Write unit tests for duplicate detection
5. Implement duplicate validation
6. Run all tests, refactor
7. **Delegate to @fastapi-service-builder** for service review

### Session 3: Phase 2 (Aiming - Part 2)
1. Write integration tests for `/game/{id}/aim-shot` endpoint
2. Create endpoint in `main.py`
3. Write BDD step definitions for aiming scenarios
4. **Delegate to @dual-test-implementer** for BDD implementation
5. **Delegate to @htmx-template-builder** for aiming UI
6. **Delegate to @css-theme-designer** for styling
7. Run all tests (unit + integration + BDD)

### Session 4: Phase 3 (Firing - Part 1)
1. Write unit tests for `fire_shots()` method
2. Implement `fire_shots()` method
3. Write unit tests for `resolve_round()` method
4. Implement basic round resolution
5. Run all tests, refactor
6. **Delegate to @fastapi-service-builder** for service review

### Session 5: Phase 3 (Firing - Part 2)
1. Write unit tests for hit detection
2. Implement `_detect_hits()` helper method
3. Write integration tests for firing endpoint
4. Create `/game/{id}/fire-shots` endpoint
5. Write BDD step definitions for firing scenarios
6. **Delegate to @dual-test-implementer** for BDD implementation
7. **Delegate to @htmx-template-builder** for waiting UI
8. Run all tests

### Session 6: Phase 4 (Hit Feedback - Part 1)
1. Write unit tests for hit feedback calculation
2. Implement `calculate_hit_feedback()` method
3. Write unit tests for Hits Made tracking
4. Enhance GameBoard with hit tracking methods
5. Run all tests, refactor
6. **Delegate to @fastapi-service-builder** for service review

### Session 7: Phase 4 (Hit Feedback - Part 2)
1. Write integration tests for round results endpoint
2. Create `/game/{id}/round-results/{round}` endpoint
3. Write BDD step definitions for hit feedback scenarios
4. **Delegate to @dual-test-implementer** for BDD implementation
5. **Delegate to @htmx-template-builder** for Hits Made area UI
6. **Delegate to @css-theme-designer** for styling
7. Run all tests

### Session 8: Phase 5 (Ship Sinking & Game End)
1. Write unit tests for ship sinking detection
2. Implement `is_ship_sunk()` method
3. Write unit tests for game over detection
4. Implement `check_game_over()` method
5. Update `resolve_round()` with sinking logic
6. Write BDD step definitions for sinking scenarios
7. **Delegate to @dual-test-implementer** for BDD implementation
8. **Delegate to @htmx-template-builder** for game over UI
9. Run all tests

### Session 9: Phase 6 (Real-Time Updates)
1. Write unit tests for version tracking
2. Implement version tracking in Game class
3. Write unit tests for `wait_for_round_change()`
4. Implement async waiting logic
5. Write integration tests for long-polling endpoint
6. Create `/game/{id}/long-poll` endpoint
7. **Delegate to @htmx-template-builder** for HTMX integration
8. Write BDD step definitions for real-time scenarios
9. **Delegate to @dual-test-implementer** for BDD implementation
10. Run all tests

### Session 10: Phase 7 (Edge Cases & Polish)
1. Write unit tests for state management
2. Implement `get_game_state()` method
3. Write unit tests for surrender
4. Implement `surrender_game()` method
5. Write integration tests for error handling
6. Add error handling to all endpoints
7. Write BDD step definitions for edge cases
8. **Delegate to @dual-test-implementer** for BDD implementation
9. **Delegate to @htmx-template-builder** for error UI
10. **Delegate to @type-hint-enforcer** for final verification
11. Run all tests, final refactor

---

## Potential Challenges & Solutions

### Challenge 1: Simultaneous Shot Resolution (Race Conditions)
**Problem**: Both players might fire at exactly the same time, causing race conditions.

**Solution**:
- Use a lock/mutex when resolving rounds
- Ensure only one `resolve_round()` call processes at a time
- Use atomic operations for updating game state

```python
import asyncio

class GameplayService:
    def __init__(self):
        self._round_locks: dict[str, asyncio.Lock] = {}
        
    async def fire_shots(self, game_id: str, player_id: str):
        if game_id not in self._round_locks:
            self._round_locks[game_id] = asyncio.Lock()
            
        async with self._round_locks[game_id]:
            # Safe to resolve round here
            if self._both_players_fired(game_id):
                await self.resolve_round(game_id)
```

### Challenge 2: Long-Polling Timeout Management
**Problem**: Long-polling connections might timeout or disconnect.

**Solution**:
- Set reasonable timeout (30 seconds)
- Return 204 No Content if no change
- Client automatically retries with new version
- Use asyncio.wait_for() with timeout

```python
@app.get("/game/{game_id}/long-poll")
async def long_poll(game_id: str, version: int):
    try:
        await asyncio.wait_for(
            gameplay_service.wait_for_round_change(game_id, version),
            timeout=30.0
        )
        return {"version": gameplay_service.get_round_version(game_id)}
    except asyncio.TimeoutError:
        return Response(status_code=204)  # No change
```

### Challenge 3: Ship-Based Hit Feedback (Not Coordinate-Based)
**Problem**: Players learn which ship was hit, but not exact coordinates.

**Solution**:
- Store hits by ship type, not by coordinate
- Return hit feedback as `{"Carrier": 2, "Destroyer": 1}`
- Only show coordinates on player's own board
- Hits Made area shows round numbers, not coordinates

```python
def calculate_hit_feedback(self, shots: list[Coord], opponent_board: GameBoard) -> dict[str, int]:
    hits_by_ship: dict[str, int] = {}
    for shot in shots:
        ship_type = opponent_board.ship_type_at(shot)
        if ship_type:
            ship_name = ship_type.ship_name
            hits_by_ship[ship_name] = hits_by_ship.get(ship_name, 0) + 1
    return hits_by_ship
```

### Challenge 4: Hits Made Area Tracking
**Problem**: Need to track which ships were hit in which rounds, cumulatively.

**Solution**:
- Store hits as list of (coord, round_number) tuples per ship
- Display round numbers in Hits Made area
- Show cumulative total hits per ship

```python
@dataclass
class Ship:
    ship_type: ShipType
    positions: list[Coord]
    hits: list[tuple[Coord, int]] = field(default_factory=list)  # (coord, round)
    
    def get_hits_by_round(self) -> dict[int, int]:
        """Return {round_number: hit_count}"""
        hits_by_round: dict[int, int] = {}
        for coord, round_num in self.hits:
            hits_by_round[round_num] = hits_by_round.get(round_num, 0) + 1
        return hits_by_round
```

### Challenge 5: Draw Condition Detection
**Problem**: Both players might sink all ships in the same round.

**Solution**:
- Check both players' boards after round resolution
- If both have all ships sunk, mark as draw
- Set `is_draw = True` and `winner_id = None`

```python
def check_game_over(self, game: Game) -> GameOverResult:
    p1_all_sunk = all(ship.is_sunk for ship in game.board[game.player_1].ships)
    p2_all_sunk = all(ship.is_sunk for ship in game.board[game.player_2].ships)
    
    if p1_all_sunk and p2_all_sunk:
        return GameOverResult(game_over=True, is_draw=True, winner_id=None)
    elif p1_all_sunk:
        return GameOverResult(game_over=True, is_draw=False, winner_id=game.player_2.id)
    elif p2_all_sunk:
        return GameOverResult(game_over=True, is_draw=False, winner_id=game.player_1.id)
    else:
        return GameOverResult(game_over=False, is_draw=False, winner_id=None)
```

### Challenge 6: State Synchronization Between Players
**Problem**: Both players need to see consistent game state.

**Solution**:
- Use version numbers for change detection
- Long-polling ensures both players get updates
- Store authoritative state on server
- Never trust client-side state

```python
class Game:
    def __init__(self):
        self._round_version: int = 0
        self._round_change_event: asyncio.Event = asyncio.Event()
        
    def _notify_round_change(self):
        self._round_version += 1
        self._round_change_event.set()
        
    async def wait_for_round_change(self, since_version: int):
        if self._round_version != since_version:
            return  # Already changed
        self._round_change_event.clear()
        await self._round_change_event.wait()
```

---

## Key Principles

1. **One cycle at a time** - Don't rush ahead
2. **RED before GREEN** - Always write failing test first
3. **GREEN before REFACTOR** - Make it work, then make it good
4. **Run tests constantly** - After every small change
5. **Commit frequently** - After each successful cycle

---

## When to Move to Next Phase

Only move to the next phase when:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All BDD scenarios pass (FastAPI + Playwright)
- [ ] Code has been refactored
- [ ] Type hints verified
- [ ] No known bugs
