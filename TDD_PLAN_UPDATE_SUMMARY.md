# TDD Implementation Plan Update Summary

**Date**: After Phase 1 and Phase 2 Cycles 2.1-2.5 completion
**Reason**: User feedback on UI interaction patterns after manual testing

---

## Key Changes Made

### 1. Updated UI Interaction Pattern

**Original Plan**:
- Separate "Aimed Shots" board for selecting shots
- "Shots Fired" board for viewing past shots only (read-only)

**Updated Plan**:
- **Single "Shots Fired" board** serves dual purpose:
  - Shows previously fired shots from past rounds (with round numbers)
  - Allows clicking cells to aim new shots for current round
- **Aimed shots list** component shows selected shots with remove buttons
- **Shot counter** component shows "Shots Aimed: X/Y available"
- **Fire Shots button** component submits all aimed shots together

### 2. Component Renaming

| Old Name | New Name | Reason |
|----------|----------|--------|
| `opponent_board.html` | `shots_fired_board.html` | Better reflects dual purpose (past shots + aiming) |

### 3. Cell State Management

Added comprehensive cell state system:

| State | Description | Visual | Clickable |
|-------|-------------|--------|-----------|
| **Fired** | Shot fired in previous round | Round number marker | ❌ No |
| **Aimed** | Shot aimed for current round | Highlighted/marked | ✅ Yes (to remove) |
| **Available** | Valid target for aiming | Default style | ✅ Yes (to aim) |
| **Unavailable** | Already fired or limit reached | Disabled style | ❌ No |

### 4. Phase 2 Expansion

**Before**: 10 scenarios, 5 cycles
**After**: 19 scenarios, 10 cycles

**New Cycles Added**:
- Cycle 2.6: Rename and Integrate Opponent Board with Shots Fired Board
- Cycle 2.7: Cell State Management
- Cycle 2.8: Aimed Shots List Integration
- Cycle 2.9: Shot Counter Updates
- Cycle 2.10: Fire Button State Management

### 5. New BDD Scenarios

Added 8 new scenarios to `features/two_player_gameplay.feature`:
1. Aimed shots list shows all aimed shots with remove buttons
2. Shot counter updates as shots are aimed
3. Fire Shots button is disabled when no shots aimed
4. Fire Shots button is enabled when shots are aimed
5. Clicking on fired cell shows error message
6. Clicking on aimed cell removes it from aimed list
7. Cell states are visually distinct
8. Shot limit enforcement prevents clicking when limit reached

### 6. Updated Scenario Count

**Total Scenarios**: 48 → **58 scenarios** (10 new scenarios added)

---

## Completion Status

### ✅ Completed Work

**Phase 1: Round & Shot Domain Models**
- ✅ Round, Shot, HitResult, RoundResult models
- ✅ GameBoard shot tracking
- ✅ Shots available calculation
- ✅ 20 unit tests passing

**Phase 2: Cycles 2.1-2.5**
- ✅ GameplayService with aim_shot(), get_aimed_shots(), clear_aimed_shot()
- ✅ JSON API endpoints (POST /aim-shot, DELETE /aim-shot/{coord}, GET /aimed-shots)
- ✅ HTMX templates created:
  - `opponent_board.html` (to be renamed)
  - `aimed_shots_list.html`
  - `shot_counter.html`
  - `fire_shots_button.html`
  - `aiming_interface.html`
- ✅ 19 tests passing (8 unit + 11 integration)

### 🔄 In Progress

**Phase 2: Cycles 2.6-2.10**
- ⏳ Rename opponent_board.html to shots_fired_board.html
- ⏳ Integrate board to show past shots + aiming interface
- ⏳ Implement cell state management (CellState enum, get_cell_state())
- ⏳ Write BDD tests for single-board interaction
- ⏳ Test component integration (list, counter, button)

### ⏳ Remaining Work

- Phase 2: Cycles 2.6-2.10 (UI integration)
- Phase 3: Simultaneous Shot Resolution (8 scenarios)
- Phase 4: Hit Feedback & Tracking (9 scenarios)
- Phase 5: Ship Sinking & Game End (11 scenarios)
- Phase 6: Real-Time Updates & Long-Polling (3 scenarios)
- Phase 7: Edge Cases & Error Handling (10 scenarios)

---

## Recommended Next Steps

### Immediate Actions (Phase 2 Completion)

1. **Cycle 2.6: Rename and Integrate Board**
   ```bash
   # Rename the file
   mv templates/components/opponent_board.html templates/components/shots_fired_board.html
   
   # Update references in other templates
   # - templates/components/aiming_interface.html
   # - templates/gameplay.html
   ```

2. **Cycle 2.7: Implement Cell State Logic**
   - Create `CellState` enum in `services/gameplay_service.py`:
     ```python
     class CellState(StrEnum):
         FIRED = "fired"
         AIMED = "aimed"
         AVAILABLE = "available"
         UNAVAILABLE = "unavailable"
     ```
   - Implement `get_cell_state()` method with unit tests
   - Update template to use cell state for styling

3. **Cycle 2.8-2.10: Integration Testing**
   - Write BDD step definitions for single-board interaction
   - Test aimed shots list updates
   - Test shot counter updates
   - Test fire button state management

4. **Run Full Test Suite**
   ```bash
   # Unit tests
   uv run pytest tests/unit/test_gameplay_service.py -v
   
   # Integration tests
   uv run pytest tests/endpoint/test_gameplay_endpoints.py -v
   
   # BDD tests (when ready)
   uv run pytest tests/bdd/ -v
   ```

### Phase 2 Completion Checklist

- [ ] `opponent_board.html` renamed to `shots_fired_board.html`
- [ ] Board shows past fired shots with round numbers
- [ ] Board allows clicking to aim new shots
- [ ] Board shows aimed shots with highlighting
- [ ] Cell states properly managed (fired, aimed, available, unavailable)
- [ ] Aimed shots list updates correctly
- [ ] Shot counter updates correctly
- [ ] Fire button state management works
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All BDD scenarios for Phase 2 passing
- [ ] Manual UI testing confirms expected behavior
- [ ] Code reviewed and refactored

---

## Questions for User

1. **Template Structure**: Should we keep the current structure where `aiming_interface.html` wraps all components, or would you prefer a different layout?

2. **Cell Click Behavior**: When a user clicks an aimed cell, should it:
   - Remove the aim (current plan)
   - Show a confirmation dialog
   - Do nothing (require using the remove button in the list)

3. **Visual Design**: Do you have preferences for how the different cell states should look? (colors, icons, etc.)

4. **Error Messages**: Where should error messages appear?
   - Top of aiming interface (current plan)
   - Toast/notification
   - Inline near the board

5. **Testing Priority**: Should we focus on:
   - Unit tests first, then BDD
   - BDD first to validate UI behavior
   - Both in parallel

---

## Files Modified

### Updated Files
- `TDD_IMPLEMENTATION_PLAN.md` - Complete rewrite with updated approach

### Files to Modify Next
- `templates/components/opponent_board.html` → Rename to `shots_fired_board.html`
- `templates/components/aiming_interface.html` - Update to use renamed component
- `templates/gameplay.html` - Update to use renamed component
- `services/gameplay_service.py` - Add CellState enum and get_cell_state() method
- `tests/unit/test_gameplay_service.py` - Add tests for cell state logic
- `tests/bdd/test_gameplay_steps.py` - Add step definitions for single-board interaction

### New Files to Create
- `tests/bdd/test_gameplay_steps_fastapi.py` - FastAPI BDD step definitions
- `tests/bdd/test_gameplay_steps_playwright.py` - Playwright BDD step definitions

---

## Architecture Decisions

### 1. Single Board Approach
**Decision**: Use one board for both viewing past shots and aiming new shots
**Rationale**: More intuitive UX, reduces visual clutter, matches user's mental model
**Trade-offs**: Slightly more complex state management, but better user experience

### 2. Cell State Management
**Decision**: Implement explicit CellState enum with get_cell_state() method
**Rationale**: Clear separation of concerns, easier to test, maintainable
**Trade-offs**: Additional complexity, but worth it for clarity

### 3. Component Integration
**Decision**: Keep components separate but integrate via HTMX
**Rationale**: Maintains modularity, allows independent testing, follows HATEOAS principles
**Trade-offs**: More HTMX configuration, but better separation of concerns

### 4. HTMX Swap Strategy
**Decision**: Swap entire `#aiming-interface` container on updates
**Rationale**: Simplest approach, ensures all components stay in sync
**Trade-offs**: More HTML transferred, but acceptable for this use case

---

## Testing Strategy Updates

### Unit Tests
- **Focus**: Service layer logic (aim_shot, get_cell_state, validation)
- **Coverage**: All business rules, edge cases, error conditions
- **Current**: 8 tests passing
- **Target**: ~15 tests after Phase 2 completion

### Integration Tests
- **Focus**: API endpoints, request/response validation
- **Coverage**: All endpoints, error responses, HTMX responses
- **Current**: 11 tests passing
- **Target**: ~20 tests after Phase 2 completion

### BDD Tests
- **Focus**: End-to-end user scenarios, UI interaction
- **Coverage**: All 58 scenarios from feature file
- **Current**: 0 tests (not yet implemented)
- **Target**: 19 scenarios passing after Phase 2 completion

---

## Risk Assessment

### Low Risk
- ✅ Domain models (already complete and tested)
- ✅ Service layer aiming logic (already complete and tested)
- ✅ JSON API endpoints (already complete and tested)

### Medium Risk
- 🔄 Cell state management (new complexity, needs careful testing)
- 🔄 HTMX integration (multiple components need to stay in sync)
- 🔄 BDD test implementation (new test suite to create)

### High Risk
- ⏳ Simultaneous shot resolution (Phase 3 - race conditions possible)
- ⏳ Long-polling implementation (Phase 6 - async complexity)
- ⏳ Real-time updates (Phase 6 - connection resilience)

---

## Success Metrics

### Phase 2 Completion
- [ ] All 19 BDD scenarios passing
- [ ] ~15 unit tests passing
- [ ] ~20 integration tests passing
- [ ] Manual UI testing confirms expected behavior
- [ ] Code coverage > 80% for gameplay_service.py
- [ ] No known bugs or issues

### Overall Project
- [ ] All 58 BDD scenarios passing
- [ ] ~100+ unit tests passing
- [ ] ~50+ integration tests passing
- [ ] Code coverage > 85% overall
- [ ] Performance: Round resolution < 100ms
- [ ] Performance: Long-polling timeout = 30s

---

## Timeline Estimate

### Phase 2 Completion (Cycles 2.6-2.10)
- **Estimated Time**: 1-2 development sessions (4-8 hours)
- **Complexity**: Medium
- **Blockers**: None identified

### Phase 3: Simultaneous Shot Resolution
- **Estimated Time**: 2 development sessions (6-10 hours)
- **Complexity**: High
- **Blockers**: Phase 2 must be complete

### Phase 4: Hit Feedback & Tracking
- **Estimated Time**: 2 development sessions (6-10 hours)
- **Complexity**: Medium
- **Blockers**: Phase 3 must be complete

### Phase 5: Ship Sinking & Game End
- **Estimated Time**: 1-2 development sessions (4-8 hours)
- **Complexity**: Medium
- **Blockers**: Phase 4 must be complete

### Phase 6: Real-Time Updates & Long-Polling
- **Estimated Time**: 2 development sessions (6-10 hours)
- **Complexity**: High
- **Blockers**: Phase 5 must be complete

### Phase 7: Edge Cases & Error Handling
- **Estimated Time**: 1-2 development sessions (4-8 hours)
- **Complexity**: Medium
- **Blockers**: Phase 6 must be complete

**Total Estimated Time**: 9-13 development sessions (30-54 hours)

---

## Conclusion

The TDD implementation plan has been successfully updated to reflect user feedback on UI interaction patterns. The single-board approach is more intuitive and aligns with user expectations. The plan maintains strict TDD discipline while accommodating the improved UX.

**Current Status**: Phase 1 complete ✅, Phase 2 Cycles 2.1-2.5 complete ✅, Phase 2 Cycles 2.6-2.10 in progress 🔄

**Next Milestone**: Complete Phase 2 by integrating the Shots Fired board with aiming functionality and passing all 19 BDD scenarios.

**Backup**: Original plan saved as `TDD_IMPLEMENTATION_PLAN.md.backup`
