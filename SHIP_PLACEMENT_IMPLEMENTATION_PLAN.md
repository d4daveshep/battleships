# Ship Placement Implementation Plan

## Overview

The ship placement feature is the first major gameplay feature after login/lobby. It requires implementing ship placement logic, validation rules, random placement, and preparing for game initialization.

## Key Components Needed

### 1. Data Models (in `game/` directory)

#### `game/ship.py` - Core ship data structures

```python
from dataclasses import dataclass
from enum import StrEnum

class ShipType(StrEnum):
    CARRIER = "Carrier"
    BATTLESHIP = "Battleship"
    CRUISER = "Cruiser"
    SUBMARINE = "Submarine"
    DESTROYER = "Destroyer"

@dataclass
class Ship:
    """Represents a ship in the game"""
    name: str
    length: int
    shots_available: int
    coordinates: list[str]  # e.g., ["A1", "A2", "A3"]
    orientation: str  # horizontal, vertical, diagonal
    is_placed: bool
```

**Ship Specifications:**

- Carrier: length 5, 2 shots
- Battleship: length 4, 1 shot
- Cruiser: length 3, 1 shot
- Submarine: length 3, 1 shot
- Destroyer: length 2, 1 shot

#### `game/board.py` - Board and placement logic

```python
from dataclasses import dataclass
from typing import NamedTuple

class CoordinateValidation(NamedTuple):
    is_valid: bool
    error_message: str
    row_index: int
    col_index: int

@dataclass
class Board:
    """Represents a 10x10 game board (A-J rows, 1-10 columns)"""
    grid: dict[str, str | None]  # coordinate -> ship_name or None

    def validate_coordinate(self, coord: str) -> CoordinateValidation
    def parse_coordinate(self, coord: str) -> tuple[int, int]
    def get_cells_between(self, start: str, end: str) -> list[str]
    def detect_orientation(self, start: str, end: str) -> str
    def is_within_bounds(self, cells: list[str]) -> bool
    def cells_overlap(self, cells1: list[str], cells2: list[str]) -> bool
    def cells_are_adjacent(self, cells1: list[str], cells2: list[str]) -> bool
    def validate_ship_length(self, cells: list[str], expected_length: int) -> bool
    def get_adjacent_cells(self, cell: str) -> list[str]
```

#### `game/game_state.py` - Game state management

```python
from dataclasses import dataclass, field
from game.board import Board
from game.ship import Ship

@dataclass
class GameState:
    """Maintains complete game state for a player"""
    player_name: str
    opponent_name: str | None
    game_mode: str  # "computer" or "human"
    player_board: Board
    opponent_board: Board
    player_ships: dict[str, Ship]  # ship_name -> Ship
    opponent_ships: dict[str, Ship]
    current_round: int = 1
    game_started: bool = False
    ships_placement_complete: bool = False
```

### 2. Service Layer (in `services/` directory)

#### `services/ship_placement_service.py`

```python
from typing import NamedTuple
from game.game_state import GameState
from game.ship import Ship
from game.board import Board

class PlacementValidation(NamedTuple):
    """Result of ship placement validation"""
    is_valid: bool
    error_message: str
    occupied_cells: list[str]

class ShipPlacementService:
    """Service for managing ship placement business logic"""

    def __init__(self, game_states: dict[str, GameState]):
        self.game_states = game_states

    def place_ship(
        self,
        player_name: str,
        ship_name: str,
        start_coord: str,
        end_coord: str,
        orientation: str | None = None
    ) -> PlacementValidation:
        """Place a ship with full validation"""
        pass

    def remove_ship(self, player_name: str, ship_name: str) -> None:
        """Remove a placed ship"""
        pass

    def reset_all_ships(self, player_name: str) -> None:
        """Clear all ships"""
        pass

    def random_placement(self, player_name: str) -> bool:
        """Randomly place all 5 ships following rules"""
        pass

    def get_placed_ships(self, player_name: str) -> dict[str, Ship]:
        """Retrieve current placement"""
        pass

    def get_placement_progress(self, player_name: str) -> tuple[int, int]:
        """Return (placed_count, total_count)"""
        pass

    def can_start_game(self, player_name: str) -> bool:
        """Check if all 5 ships placed"""
        pass

    def validate_placement(
        self,
        board: Board,
        ship: Ship,
        cells: list[str]
    ) -> PlacementValidation:
        """Centralized validation logic"""
        pass
```

### 3. State Management

Add to existing global state in `main.py`:

```python
# Game state storage (player_name -> GameState)
_game_states: dict[str, GameState] = {}

# Ship placement service
ship_placement_service: ShipPlacementService = ShipPlacementService(_game_states)
```

### 4. API Endpoints (in `main.py`)

#### New routes needed

**GET `/ship-placement`** - Ship placement screen

- Query param: `player_name`
- Returns: HTML template with ship placement interface
- Template context:
  - `player_name`
  - `board` (10x10 grid)
  - `ships` (5 ships with placement status)
  - `placed_count` (0-5)
  - `can_start` (boolean)
  - `game_mode` (computer/human)

**POST `/place-ship`** - Place a single ship

- Form data:
  - `player_name: str`
  - `ship_name: str`
  - `start_coordinate: str`
  - `end_coordinate: str`
  - `orientation: str` (optional - can auto-detect)
- Returns: Updated ship placement HTML (200 OK or 200/400 with error)
- Validates:
  - Coordinate format
  - Ship length
  - Orientation
  - Board boundaries
  - No overlap
  - No touching (with 1-cell spacing)

**POST `/remove-ship`** - Remove a placed ship

- Form data:
  - `player_name: str`
  - `ship_name: str`
- Returns: Updated board HTML

**POST `/reset-all-ships`** - Clear all ships

- Form data:
  - `player_name: str`
- Returns: Fresh board HTML with all ships removed

**POST `/random-ship-placement`** - Auto-place all ships

- Form data:
  - `player_name: str`
- Returns: Board HTML with all 5 ships placed
- Clears existing manual placements first

**POST `/start-game`** - Start game (single player)

- Form data:
  - `player_name: str`
- Computer opponent auto-places ships
- Redirects to game screen (303 SEE OTHER)

**POST `/ready-for-game`** - Ready for multiplayer

- Form data:
  - `player_name: str`
- Marks player as ready
- Returns: Waiting message or game redirect

### 5. Templates (in `templates/` directory)

#### `templates/ship_placement.html` - Main ship placement page

Required elements with `data-testid` attributes:

```html
<div data-testid="ship-placement-container">
  <h1>Ship Placement</h1>

  <!-- Placement Status -->
  <div data-testid="ship-placement-status">
    <span data-testid="ship-placement-count">0 of 5 ships placed</span>
  </div>

  <!-- Error Display -->
  <div data-testid="placement-error" style="display: none;">
    <!-- Error message here -->
  </div>

  <!-- Status Message -->
  <div data-testid="status-message" style="display: none;">
    <!-- General status messages -->
  </div>

  <!-- Ship Selector -->
  <div class="ship-selector">
    <button data-testid="select-ship-carrier">Carrier (5)</button>
    <button data-testid="select-ship-battleship">Battleship (4)</button>
    <button data-testid="select-ship-cruiser">Cruiser (3)</button>
    <button data-testid="select-ship-submarine">Submarine (3)</button>
    <button data-testid="select-ship-destroyer">Destroyer (2)</button>
  </div>

  <!-- Ship Status Indicators -->
  <div class="ship-status-list">
    <div data-testid="ship-status-carrier">Carrier: Not Placed</div>
    <div data-testid="ship-status-battleship">Battleship: Not Placed</div>
    <div data-testid="ship-status-cruiser">Cruiser: Not Placed</div>
    <div data-testid="ship-status-submarine">Submarine: Not Placed</div>
    <div data-testid="ship-status-destroyer">Destroyer: Not Placed</div>
  </div>

  <!-- Game Board -->
  <div data-testid="my-ships-board" class="game-board">
    <!-- 10x10 grid -->
    <!-- Each cell: data-testid="cell-{coordinate}" -->
    <!-- Occupied cells also have: data-ship="{ship_name}" -->
  </div>

  <!-- Placed Ships Markers -->
  <div class="placed-ships">
    <!-- When placed: -->
    <!-- <div data-testid="placed-ship-carrier">Carrier placed</div> -->
  </div>

  <!-- Action Buttons -->
  <button data-testid="random-placement">Random Placement</button>
  <button data-testid="reset-all-ships">Reset All Ships</button>
  <button data-testid="start-game-button" disabled>Start Game</button>
  <!-- For multiplayer: -->
  <button data-testid="ready-button" style="display: none;">Ready</button>
</div>
```

#### `templates/components/ship_board.html` - Reusable board component

10x10 grid with proper data attributes for testing.

### 6. Placement Validation Logic

#### Coordinate Parsing

- **Format:** Letter (A-J) + Number (1-10)
- **Example:** "A1", "J10", "E5"
- **Parse to:** (row_index, col_index) where A=0, B=1, ..., J=9 and 1=0, 2=1, ..., 10=9

#### Orientation Detection

- **Horizontal:** Same row, different columns (e.g., "E3" to "E7")
- **Vertical:** Same column, different rows (e.g., "B2" to "E2")
- **Diagonal:** Row and column both change by same amount
  - Down-right: row++, col++ (e.g., "A1" to "C3")
  - Down-left: row++, col-- (e.g., "A10" to "B9")
  - Up-right: row--, col++ (e.g., "H3" to "F5")
  - Up-left: row--, col-- (e.g., "E7" to "C5")
- **Invalid:** Anything else (e.g., "A1" to "B3")

#### Cell Calculation

Given start and end coordinates:

1. Parse both to (row, col)
2. Detect orientation
3. Calculate intermediate cells:
   - **Horizontal:** Increment column only
   - **Vertical:** Increment row only
   - **Diagonal:** Increment both row and column (with proper direction)
4. Verify length matches ship length

#### Validation Rules (in order)

1. **Coordinate format validation**

   - Must match pattern: `[A-J][1-9]|10`
   - Error: "Invalid coordinate format"

2. **Ship length validation**

   - Distance between start/end must match ship length
   - Error: "Ship placement does not match {ship_name} length of {length}"

3. **Orientation validation**

   - Must be horizontal, vertical, or diagonal at 45°
   - Error: "Ship must be placed horizontally, vertically, or diagonally"

4. **Board boundaries validation**

   - All cells must be within A1-J10
   - Error: "Ship placement goes outside the board"

5. **No overlap validation**

   - No cell can be occupied by another ship
   - Error: "Ships cannot overlap"

6. **No touching validation (spacing)**
   - No adjacent cells (including diagonals) can be occupied by another ship
   - Edge cells at board boundary are exempt
   - Error: "Ships must have empty space around them"

#### Adjacent Cell Calculation

For each ship cell at (row, col), check 8 surrounding cells:

- (row-1, col-1), (row-1, col), (row-1, col+1)
- (row, col-1), (row, col+1)
- (row+1, col-1), (row+1, col), (row+1, col+1)

Ignore cells outside board boundaries (at edges).

### 7. Random Placement Algorithm

#### Strategy

1. **Ship order:** Largest to smallest (Carrier → Battleship → Cruiser → Submarine → Destroyer)
2. **For each ship:**
   - Max attempts: 1000 per ship
   - Random orientation: horizontal, vertical, or diagonal
   - Random start coordinate
   - Calculate end coordinate based on length and orientation
   - Validate placement (all rules)
   - If valid: place and continue to next ship
   - If invalid: try again
3. **Full board retry:** If unable to place a ship after max attempts, clear board and restart
4. **Max full retries:** 10 (prevents infinite loops)

#### Pseudocode

```python
def random_placement(player_name: str) -> bool:
    max_full_retries = 10
    ships = [CARRIER, BATTLESHIP, CRUISER, SUBMARINE, DESTROYER]

    for full_retry in range(max_full_retries):
        reset_all_ships(player_name)
        success = True

        for ship in ships:
            placed = False
            for attempt in range(1000):
                orientation = random.choice(['horizontal', 'vertical', 'diagonal'])
                start_coord = random_coordinate()
                end_coord = calculate_end_coord(start_coord, ship.length, orientation)

                validation = validate_placement(ship, start_coord, end_coord)
                if validation.is_valid:
                    place_ship(player_name, ship.name, start_coord, end_coord)
                    placed = True
                    break

            if not placed:
                success = False
                break  # Retry full board

        if success:
            return True

    return False  # Failed after max retries
```

### 8. Login Flow Update

Update the login POST endpoint (`/` POST handler):

**Current flow:**

```python
if game_mode == "computer":
    redirect_url = _build_game_url(player_name)
```

**New flow:**

```python
if game_mode == "computer":
    redirect_url = f"/ship-placement?player_name={player_name}"
```

Multiplayer mode keeps existing lobby flow, but after pairing (in future), redirect to ship placement instead of game.

### 9. Implementation Order (TDD RED-GREEN-REFACTOR)

#### Phase 1: Core Data Models

1. Create `game/ship.py` with `Ship` and `ShipType`
2. Create `game/board.py` with coordinate parsing and basic validation
3. Create `game/game_state.py` with `GameState` dataclass
4. **Run tests:** Expect failures (endpoints don't exist yet)

#### Phase 2: Basic Placement

1. Implement `services/ship_placement_service.py` with placement validation
2. Add `/ship-placement` GET endpoint
3. Create `ship_placement.html` template with basic board
4. Add `/place-ship` POST endpoint for horizontal placement only
5. **Run tests:** Expect failures for missing validation and vertical/diagonal

#### Phase 3: Validation Rules

1. Implement coordinate validation in `Board` class
2. Implement ship length validation
3. Implement board boundary validation
4. Implement overlap detection
5. Implement touching/spacing detection (adjacent cells)
6. Add vertical placement support to `/place-ship`
7. Add diagonal placement support to `/place-ship`
8. **Run tests:** Most placement scenarios should pass

#### Phase 4: Ship Management

1. Add `/remove-ship` POST endpoint
2. Add `/reset-all-ships` POST endpoint
3. Implement placement progress tracking in service
4. Add Start Game button enable/disable logic (client-side check)
5. Update template to show ship status
6. **Run tests:** Ship management scenarios should pass

#### Phase 5: Random Placement

1. Implement random placement algorithm in service
2. Add `/random-ship-placement` POST endpoint
3. Test all placement rules with random generation
4. **Run tests:** Random placement scenarios should pass

#### Phase 6: Game Flow Integration

1. Add `/start-game` POST endpoint for single player
2. Implement computer opponent random placement
3. Add `/ready-for-game` POST endpoint for multiplayer
4. Update login redirect to ship placement
5. Update game state initialization
6. **Run tests:** Game start scenarios should pass

#### Phase 7: Polish & Error Handling

1. Add comprehensive error messages for all validation failures
2. Ensure all `data-testid` attributes present in templates
3. Add CSS styling for ship placement UI
4. Handle edge cases (invalid player, concurrent requests)
5. Add proper HTMX integration for dynamic updates
6. **Run full test suite:** All scenarios should pass ✅

### 10. Test Endpoints Summary

Based on `test_ship_placement_steps_fastapi.py`:

| Endpoint                 | Method | Purpose                   | Status Codes        |
| ------------------------ | ------ | ------------------------- | ------------------- |
| `/`                      | POST   | Login (existing)          | 302/303 redirect    |
| `/ship-placement`        | GET    | Get ship placement screen | 200                 |
| `/place-ship`            | POST   | Place a single ship       | 200 (success/error) |
| `/remove-ship`           | POST   | Remove a placed ship      | 200                 |
| `/reset-all-ships`       | POST   | Clear all ships           | 200                 |
| `/random-ship-placement` | POST   | Auto-place all ships      | 200                 |
| `/start-game`            | POST   | Start single player game  | 303 redirect        |
| `/ready-for-game`        | POST   | Ready for multiplayer     | 200                 |

### 11. Expected HTML Elements (from test assertions)

All elements must have proper `data-testid` attributes:

| Test ID                     | Element Type | Purpose                                          |
| --------------------------- | ------------ | ------------------------------------------------ |
| `ship-placement-container`  | `<div>`      | Main container                                   |
| `my-ships-board`            | `<div>`      | Board grid                                       |
| `cell-{coordinate}`         | `<div>`      | Grid cell (e.g., `cell-A1`)                      |
| (with `data-ship="{name}"`) | attribute    | Ship occupying cell                              |
| `placed-ship-{ship_name}`   | `<div>`      | Placed ship marker (e.g., `placed-ship-carrier`) |
| `ship-status-{ship_name}`   | `<div>`      | Ship status text (e.g., `ship-status-destroyer`) |
| `select-ship-{ship_name}`   | `<button>`   | Ship selection button                            |
| `placement-error`           | `<div>`      | Error message display                            |
| `ship-placement-status`     | `<div>`      | Status text area                                 |
| `ship-placement-count`      | `<span>`     | Count display ("X of 5 ships placed")            |
| `start-game-button`         | `<button>`   | Start game button                                |
| `status-message`            | `<div>`      | General status messages                          |

### 12. Key Design Decisions

1. **State storage:** Use in-memory dict keyed by `player_name` (matches existing lobby pattern)
2. **Validation approach:** Return `NamedTuple` with validation results (matches `auth_service` pattern)
3. **Service layer:** Separate business logic from routes (follows existing pattern)
4. **Template approach:** Server-side rendering with Jinja2, HTMX for dynamic updates
5. **No JavaScript:** Pure HTML/HTMX following HATEOAS principles
6. **Type hints:** Required everywhere following project code style
7. **Error handling:** Return 200 with error message in HTML (not 400) for validation errors during placement
8. **Coordinate system:** Internal use 0-based indices, external display A-J, 1-10
9. **Ship names:** Case-insensitive storage, but display with proper capitalization

### 13. Testing Strategy

Following BDD/TDD principles:

1. **RED Phase:** Run tests first - all should fail
2. **GREEN Phase:** Implement minimal code to make tests pass
3. **REFACTOR Phase:** Clean up code, extract common logic, optimize

**Test categories covered:**

- ✅ Horizontal ship placement
- ✅ Vertical ship placement
- ✅ Diagonal ship placement (3 directions)
- ✅ Edge placement (valid - ships touching board edges)
- ✅ Invalid placement - outside board boundaries
- ✅ Invalid placement - ships overlapping
- ✅ Invalid placement - ships touching (no spacing)
- ✅ Valid placement - ships with proper spacing
- ✅ Random placement
- ✅ Ship placement progress tracking
- ✅ Ship removal
- ✅ Reset all ships
- ✅ Start game button state
- ✅ Computer opponent ship placement
- ✅ Multiplayer waiting/ready states
- ✅ Invalid ship patterns (wrong angle, wrong length)

### 14. Future Considerations

**Not in current scope but should be designed for:**

- Ship placement persistence (database storage)
- Multiple concurrent games per player
- Ship placement timeout for multiplayer
- Undo/redo functionality
- Drag-and-drop ship placement (would require JavaScript - future enhancement)
- Ship rotation UI
- Visual feedback during placement (hover states)

### 15. Dependencies

**No new external dependencies required.** All functionality can be implemented with:

- Python standard library (`random`, `dataclasses`, `enum`, etc.)
- FastAPI (already installed)
- Jinja2 (already installed)
- pytest/pytest-bdd (already installed for testing)

### 16. Success Criteria

Implementation is complete when:

1. ✅ All tests in `test_ship_placement_steps_fastapi.py` pass
2. ✅ All scenarios in `features/ship_placement.feature` pass
3. ✅ Code follows project style guidelines (type hints, naming conventions)
4. ✅ No JavaScript used (HATEOAS/HTMX only)
5. ✅ Proper error messages for all validation failures
6. ✅ Ships can be placed, removed, and randomly generated
7. ✅ Game can start after all ships placed
8. ✅ Computer opponent places ships automatically

---

## Quick Reference: Ship Specifications

| Ship       | Length | Shots Available |
| ---------- | ------ | --------------- |
| Carrier    | 5      | 2               |
| Battleship | 4      | 1               |
| Cruiser    | 3      | 1               |
| Submarine  | 3      | 1               |
| Destroyer  | 2      | 1               |

**Total shots at game start:** 6 shots per round

---

## Quick Reference: Validation Error Messages

| Error Condition | Error Message                                                  |
| --------------- | -------------------------------------------------------------- |
| Outside board   | "Ship placement goes outside the board"                        |
| Ships overlap   | "Ships cannot overlap"                                         |
| Ships touching  | "Ships must have empty space around them"                      |
| Invalid angle   | "Ship must be placed horizontally, vertically, or diagonally"  |
| Wrong length    | "Ship placement does not match {ship_name} length of {length}" |

---

This plan provides a comprehensive roadmap to implement ship placement following TDD principles, starting with RED (failing tests), then GREEN (minimal implementation), then REFACTOR (optimize and clean up).
