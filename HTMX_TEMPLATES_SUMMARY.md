# HTMX Templates for Shot Aiming - Summary

## Templates Created

### 1. Component Templates (templates/components/)

#### opponent_board.html
**Purpose**: Clickable 10x10 grid for aiming shots at opponent's board

**Features**:
- Interactive cells that POST to `/game/{game_id}/aim-shot` when clicked
- Visual states:
  - `.cell--aimed` - Shots currently aimed (marked with ●)
  - `.cell--fired` - Shots already fired in previous rounds (marked with ✕)
  - `.cell--available` - Cells available to aim at (clickable)
  - Disabled cells when shot limit reached
- HTMX attributes:
  - `hx-post="/game/{game_id}/aim-shot"`
  - `hx-vals='{"coord": "A1"}'` - Sends coordinate
  - `hx-target="#aiming-interface"` - Updates entire interface
  - `hx-swap="innerHTML"`
- Accessibility: ARIA labels, keyboard navigation support

**Context Variables**:
- `game_id`: str
- `aimed_shots`: list[str] - e.g., ["A1", "B2"]
- `shots_fired`: list[str]
- `shots_available`: int
- `aimed_count`: int

#### shot_counter.html
**Purpose**: Display shots aimed vs available with visual feedback

**Features**:
- Shows "X / Y available" format
- Visual indicator when limit reached (⚠️)
- Shows remaining shots when in progress
- Conditional styling based on aimed_count

**Context Variables**:
- `aimed_count`: int
- `shots_available`: int

#### aimed_shots_list.html
**Purpose**: List of currently aimed shots with remove buttons

**Features**:
- Shows each aimed coordinate (e.g., "A1", "B2")
- Remove button (✕) for each shot
- DELETE request to `/game/{game_id}/aim-shot/{coord}`
- Empty state message when no shots aimed
- HTMX attributes:
  - `hx-delete="/game/{game_id}/aim-shot/{coord}"`
  - `hx-target="#aiming-interface"`
  - `hx-swap="innerHTML"`

**Context Variables**:
- `game_id`: str
- `aimed_shots`: list[str]

#### fire_shots_button.html
**Purpose**: Button to fire all aimed shots

**Features**:
- Disabled when `aimed_count == 0`
- Shows count of shots to fire
- POST to `/game/{game_id}/fire-shots` (endpoint not yet implemented)
- Hint text when disabled
- HTMX attributes:
  - `hx-post="/game/{game_id}/fire-shots"`
  - `hx-target="#game-content"`
  - `hx-swap="innerHTML"`

**Context Variables**:
- `game_id`: str
- `aimed_count`: int

#### aiming_interface.html
**Purpose**: Wrapper component that combines all aiming components

**Features**:
- Error message display (if present)
- Includes all sub-components:
  - shot_counter.html
  - opponent_board.html
  - aimed_shots_list.html
  - fire_shots_button.html
- Single swap target for all aiming operations

**Context Variables**:
- All variables from sub-components
- `error_message`: str | None

#### aiming_error.html
**Purpose**: Standalone error component with dismiss button

**Features**:
- Alert-style error display
- Dismissible (reloads aiming interface)
- HTMX dismiss button

**Context Variables**:
- `game_id`: str
- `error_message`: str

### 2. Updated Templates

#### gameplay.html
**Changes**:
- Renamed opponent board to "opponent-board-readonly" (read-only view)
- Added aiming interface section
- HTMX loads aiming interface on page load:
  - `hx-get="/game/{game_id}/aiming-interface"`
  - `hx-trigger="load"`
- Removed placeholder "Take Shot" button
- Kept "Surrender" button for future implementation

## Key HTMX Patterns Used

### 1. Form-less POST Requests
```html
<td hx-post="/game/{game_id}/aim-shot"
    hx-vals='{"coord": "A1"}'
    hx-target="#aiming-interface"
    hx-swap="innerHTML">
```
Clicking a cell sends a POST request with coordinate data.

### 2. DELETE Requests
```html
<button hx-delete="/game/{game_id}/aim-shot/A1"
        hx-target="#aiming-interface"
        hx-swap="innerHTML">
```
Remove button sends DELETE request.

### 3. Load Trigger
```html
<div hx-get="/game/{game_id}/aiming-interface"
     hx-trigger="load"
     hx-swap="innerHTML">
```
Loads content automatically when element appears.

### 4. Swap Entire Component
All actions target `#aiming-interface` and swap `innerHTML`, ensuring the entire interface updates atomically.

### 5. Progressive Enhancement
- Cells have `role="button"` and `tabindex="0"` for keyboard access
- Proper ARIA labels throughout
- Semantic HTML structure works without HTMX

## Assumptions Made

1. **Backend Returns HTML**: All endpoints must return HTML components, not JSON
2. **Shots Fired Tracking**: Assumed `shots_fired` list will be provided by backend (currently empty)
3. **Fire Shots Endpoint**: `/game/{game_id}/fire-shots` endpoint not yet implemented
4. **Error Handling**: Errors are displayed inline within the aiming interface
5. **Atomic Updates**: Entire aiming interface swaps on each action (not individual components)
6. **Session Management**: Player authentication handled by existing session middleware

## CSS Classes Added (for styling)

### Board States
- `.ship-grid--aiming` - Aiming-enabled board
- `.cell--aimed` - Cell with aimed shot
- `.cell--fired` - Cell with fired shot
- `.cell--available` - Cell available to aim at

### Shot Counter
- `.shot-counter`
- `.shot-counter__count--limit-reached`
- `.shot-counter__status--limit-reached`
- `.shot-counter__status--in-progress`

### Aimed Shots List
- `.aimed-shots-list`
- `.aimed-shots-list__items`
- `.aimed-shot-item`
- `.aimed-shot-item__remove-btn`
- `.aimed-shots-list__empty`

### Fire Button
- `.fire-shots-container`
- `.fire-shots-btn`
- `.fire-shots-hint`

### Aiming Interface
- `.aiming-interface`
- `.aiming-board-section`
- `.aiming-error`

## Next Steps

### 1. Backend Implementation
See `BACKEND_CHANGES_NEEDED.md` for detailed backend requirements:
- Implement GET `/game/{game_id}/aiming-interface`
- Modify POST `/game/{game_id}/aim-shot` to return HTML
- Modify DELETE `/game/{game_id}/aim-shot/{coord}` to return HTML
- Implement POST `/game/{game_id}/fire-shots` (Phase 3)
- Add `get_fired_shots()` to GameplayService

### 2. CSS Styling
Work with @css-theme-designer to style:
- Interactive board cells (hover, active, disabled states)
- Shot counter with visual feedback
- Aimed shots list with smooth remove animations
- Fire button with prominent call-to-action styling
- Error messages with appropriate alert styling

### 3. Testing
- Unit tests for backend endpoints
- Integration tests for HTMX interactions
- BDD scenarios for shot aiming workflow
- Playwright tests for UI interactions

### 4. Accessibility Review
- Keyboard navigation testing
- Screen reader testing
- Color contrast verification
- Focus management

## Files Created/Modified

### Created:
- `templates/components/opponent_board.html`
- `templates/components/shot_counter.html`
- `templates/components/aimed_shots_list.html`
- `templates/components/fire_shots_button.html`
- `templates/components/aiming_interface.html`
- `templates/components/aiming_error.html`
- `BACKEND_CHANGES_NEEDED.md`
- `HTMX_TEMPLATES_SUMMARY.md` (this file)

### Modified:
- `templates/gameplay.html`

## Integration Checklist

- [ ] Backend endpoints implemented (see BACKEND_CHANGES_NEEDED.md)
- [ ] CSS styling applied
- [ ] Manual testing in browser
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] BDD scenarios written
- [ ] Accessibility testing completed
- [ ] Documentation updated
