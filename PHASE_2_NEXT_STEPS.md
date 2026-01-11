# Phase 2 Next Steps: Completing Shot Aiming UI Integration

## Current Status

✅ **Completed (Cycles 2.1-2.5)**:
- GameplayService with aim_shot(), get_aimed_shots(), clear_aimed_shot()
- JSON API endpoints working
- HTMX template components created
- 19 tests passing (8 unit + 11 integration)

🔄 **In Progress (Cycles 2.6-2.10)**:
- Integrate Shots Fired board with aiming functionality
- Implement cell state management
- Complete BDD scenarios

## Immediate Next Steps

### Step 1: Rename Component (Cycle 2.6)

```bash
# Rename the file
mv templates/components/opponent_board.html templates/components/shots_fired_board.html
```

**Update references in**:
- `templates/components/aiming_interface.html` (line 18)
- `templates/gameplay.html` (if referenced)

**Update template to show**:
- Past fired shots with round numbers (read-only)
- Currently aimed shots (highlighted, clickable to remove)
- Available cells (clickable to aim)
- Unavailable cells (disabled)

### Step 2: Implement Cell State Logic (Cycle 2.7)

**RED**: Write unit tests
```python
# tests/unit/test_gameplay_service.py

def test_get_cell_state_fired():
    """Cell that was fired in previous round should be FIRED"""
    service = GameplayService()
    # Setup: Cell A1 fired in round 1
    # ... setup code ...
    state = service.get_cell_state(game_id="g1", player_id="p1", coord=Coord.A1)
    assert state == CellState.FIRED

def test_get_cell_state_aimed():
    """Cell that is aimed in current round should be AIMED"""
    service = GameplayService()
    service.aim_shot(game_id="g1", player_id="p1", coord=Coord.A1)
    state = service.get_cell_state(game_id="g1", player_id="p1", coord=Coord.A1)
    assert state == CellState.AIMED

def test_get_cell_state_available():
    """Cell that is not fired or aimed should be AVAILABLE"""
    service = GameplayService()
    state = service.get_cell_state(game_id="g1", player_id="p1", coord=Coord.A1)
    assert state == CellState.AVAILABLE

def test_get_cell_state_unavailable_limit_reached():
    """Cell should be UNAVAILABLE when shot limit reached"""
    service = GameplayService()
    # Aim 6 shots
    for i in range(6):
        service.aim_shot(game_id="g1", player_id="p1", coord=...)
    state = service.get_cell_state(game_id="g1", player_id="p1", coord=Coord.G1)
    assert state == CellState.UNAVAILABLE
```

**GREEN**: Implement in `services/gameplay_service.py`
```python
from enum import StrEnum

class CellState(StrEnum):
    FIRED = "fired"
    AIMED = "aimed"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

class GameplayService:
    # ... existing methods ...
    
    def get_cell_state(self, game_id: str, player_id: str, coord: Coord) -> CellState:
        """Get the state of a cell for the player"""
        # 1. Check if already fired in previous round
        # 2. Check if currently aimed
        # 3. Check if shot limit reached
        # 4. Otherwise available
        pass
```

**REFACTOR**: Update template to use cell state
```html
{# templates/components/shots_fired_board.html #}
{% for row in rows %}
    {% for col in range(1, 11) %}
        {% set coord = row ~ col %}
        {% set cell_state = get_cell_state(game_id, player_id, coord) %}
        
        <td data-testid="shots-fired-cell-{{ coord }}"
            data-coord="{{ coord }}"
            data-state="{{ cell_state }}"
            class="ship-grid-cell cell--{{ cell_state }}"
            {% if cell_state == "available" %}
            hx-post="/game/{{ game_id }}/aim-shot"
            hx-vals='{"coord": "{{ coord }}"}'
            hx-target="#aiming-interface"
            hx-swap="innerHTML"
            role="button"
            {% elif cell_state == "aimed" %}
            hx-delete="/game/{{ game_id }}/aim-shot/{{ coord }}"
            hx-target="#aiming-interface"
            hx-swap="innerHTML"
            role="button"
            {% else %}
            aria-disabled="true"
            {% endif %}>
            
            {% if cell_state == "fired" %}
                <span class="cell-marker">{{ round_number }}</span>
            {% elif cell_state == "aimed" %}
                <span class="cell-marker cell-marker--aimed">●</span>
            {% endif %}
        </td>
    {% endfor %}
{% endfor %}
```

### Step 3: Write BDD Tests (Cycles 2.8-2.10)

**Create**: `tests/bdd/test_gameplay_steps.py`
```python
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('../features/two_player_gameplay.feature')

@when(parsers.parse('I click on cell "{coord}" on my Shots Fired board'))
def step_click_shots_fired_cell(page, coord):
    page.click(f'[data-testid="shots-fired-cell-{coord}"]')

@then(parsers.parse('I should see "{coord}" in the aimed shots list'))
def step_see_in_aimed_list(page, coord):
    assert page.locator(f'[data-testid="aimed-shot-{coord}"]').is_visible()

@then(parsers.parse('I should see {count:d} shots in the aimed shots list'))
def step_see_aimed_count(page, count):
    items = page.locator('[data-testid="aimed-shots-items"] li').count()
    assert items == count

@then(parsers.parse('I should see "Shots Aimed: {aimed:d}/{available:d}" displayed'))
def step_see_shot_counter(page, aimed, available):
    counter = page.locator('[data-testid="shot-counter-value"]').inner_text()
    assert str(aimed) in counter and str(available) in counter

@then('the "Fire Shots" button should be disabled')
def step_fire_button_disabled(page):
    button = page.locator('[data-testid="fire-shots-button"]')
    assert button.is_disabled()

@then('the "Fire Shots" button should be enabled')
def step_fire_button_enabled(page):
    button = page.locator('[data-testid="fire-shots-button"]')
    assert not button.is_disabled()
```

### Step 4: Run Tests

```bash
# Run unit tests
uv run pytest tests/unit/test_gameplay_service.py -v

# Run integration tests
uv run pytest tests/endpoint/test_gameplay_endpoints.py -v

# Run BDD tests (when ready)
uv run pytest tests/bdd/test_gameplay_steps.py -v

# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=services --cov=game -v
```

### Step 5: Manual Testing

1. Start the server:
   ```bash
   uv run uvicorn main:app --reload
   ```

2. Navigate to gameplay page

3. Test scenarios:
   - Click on available cell → should appear in aimed shots list
   - Click on aimed cell → should remove from aimed shots list
   - Aim 6 shots → should see "Shot limit reached" message
   - Fire button should be disabled when no shots aimed
   - Fire button should be enabled when shots aimed
   - Shot counter should update correctly

## Checklist

### Cycle 2.6: Rename and Integrate Board
- [ ] Rename `opponent_board.html` to `shots_fired_board.html`
- [ ] Update references in `aiming_interface.html`
- [ ] Update template to show past fired shots
- [ ] Update template to show aimed shots
- [ ] Update template to show available cells
- [ ] Update template to show unavailable cells
- [ ] Test board rendering with mixed states

### Cycle 2.7: Cell State Management
- [ ] Create `CellState` enum
- [ ] Write unit test: `test_get_cell_state_fired()`
- [ ] Write unit test: `test_get_cell_state_aimed()`
- [ ] Write unit test: `test_get_cell_state_available()`
- [ ] Write unit test: `test_get_cell_state_unavailable_limit_reached()`
- [ ] Implement `get_cell_state()` method
- [ ] Update template to use cell state
- [ ] Add CSS classes for each state
- [ ] Run unit tests

### Cycle 2.8: Aimed Shots List Integration
- [ ] Write BDD test: clicking cell adds to list
- [ ] Write BDD test: removing shot updates list
- [ ] Write BDD test: list shows correct count
- [ ] Test HTMX updates
- [ ] Run BDD tests

### Cycle 2.9: Shot Counter Updates
- [ ] Write BDD test: counter shows correct values
- [ ] Write BDD test: counter shows limit reached message
- [ ] Write BDD test: counter shows remaining shots
- [ ] Test counter updates dynamically
- [ ] Run BDD tests

### Cycle 2.10: Fire Button State Management
- [ ] Write BDD test: button disabled when no shots
- [ ] Write BDD test: button enabled when shots aimed
- [ ] Write BDD test: button shows correct shot count
- [ ] Test button state changes
- [ ] Run BDD tests

### Final Phase 2 Checklist
- [ ] All unit tests passing (~15 tests)
- [ ] All integration tests passing (~20 tests)
- [ ] All BDD scenarios for Phase 2 passing (19 scenarios)
- [ ] Manual UI testing confirms expected behavior
- [ ] Code reviewed and refactored
- [ ] CSS styling complete
- [ ] Documentation updated
- [ ] Ready to move to Phase 3

## Expected Test Counts

After Phase 2 completion:
- **Unit tests**: ~15 tests (currently 8)
- **Integration tests**: ~20 tests (currently 11)
- **BDD tests**: 19 scenarios (currently 0)
- **Total**: ~54 tests

## Common Issues & Solutions

### Issue 1: HTMX not updating components
**Solution**: Check `hx-target` and `hx-swap` attributes, ensure endpoint returns correct HTML

### Issue 2: Cell state not updating
**Solution**: Verify `get_cell_state()` logic, check that shots_fired and aimed_shots are tracked correctly

### Issue 3: BDD tests failing
**Solution**: Check data-testid attributes match, verify page selectors, ensure server is running

### Issue 4: CSS classes not applying
**Solution**: Check class names in template match CSS file, verify cell state is set correctly

## Resources

- **TDD Implementation Plan**: `TDD_IMPLEMENTATION_PLAN.md`
- **Update Summary**: `TDD_PLAN_UPDATE_SUMMARY.md`
- **BDD Feature File**: `features/two_player_gameplay.feature`
- **Current Tests**: 
  - `tests/unit/test_gameplay_service.py`
  - `tests/endpoint/test_gameplay_endpoints.py`

## Questions?

If you have questions or need clarification on any step, refer to:
1. `TDD_PLAN_UPDATE_SUMMARY.md` - Overview of changes
2. `TDD_IMPLEMENTATION_PLAN.md` - Detailed implementation plan
3. `features/two_player_gameplay.feature` - BDD scenarios

Good luck with Phase 2 completion! 🚀
