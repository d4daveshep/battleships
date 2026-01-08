# Backend Changes Needed for Shot Aiming HTMX Templates

## Overview
The HTMX templates for shot aiming have been created, but the backend endpoints need to be modified to return HTML components instead of JSON responses.

## Required Backend Endpoints

### 1. GET /game/{game_id}/aiming-interface
**Purpose**: Initial load of the aiming interface component

**Returns**: HTML (templates/components/aiming_interface.html)

**Context Data**:
```python
{
    "game_id": str,
    "aimed_shots": list[str],  # e.g., ["A1", "B2", "C3"]
    "shots_fired": list[str],  # Previously fired coordinates
    "shots_available": int,
    "aimed_count": int,
    "error_message": str | None
}
```

**Implementation**:
```python
@app.get("/game/{game_id}/aiming-interface")
async def get_aiming_interface(request: Request, game_id: str) -> HTMLResponse:
    player_id = _get_player_id(request)
    _ensure_gameplay_initialized(game_id, player_id)
    
    # Get aimed shots
    aimed_coords = gameplay_service.get_aimed_shots(game_id, player_id)
    aimed_shots = [coord.name for coord in aimed_coords]
    
    # Get shots available
    shots_available = gameplay_service._get_shots_available(game_id, player_id)
    
    # Get previously fired shots (from previous rounds)
    # TODO: Implement this in gameplay_service
    shots_fired = []  # gameplay_service.get_fired_shots(game_id, player_id)
    
    return templates.TemplateResponse(
        request,
        "components/aiming_interface.html",
        {
            "game_id": game_id,
            "aimed_shots": aimed_shots,
            "shots_fired": shots_fired,
            "shots_available": shots_available,
            "aimed_count": len(aimed_shots),
            "error_message": None,
        },
    )
```

### 2. POST /game/{game_id}/aim-shot (MODIFY EXISTING)
**Current**: Returns JSON
**Needed**: Return HTML component (aiming_interface.html)

**Changes**:
- Accept form data instead of JSON: `coord: str = Form()`
- On success: Return updated aiming_interface.html
- On error: Return aiming_interface.html with error_message set

**Implementation**:
```python
@app.post("/game/{game_id}/aim-shot")
async def aim_shot(
    request: Request, 
    game_id: str, 
    coord: str = Form()
) -> HTMLResponse:
    player_id = _get_player_id(request)
    _ensure_gameplay_initialized(game_id, player_id)
    
    # Parse coordinate
    try:
        coord_obj = Coord[coord.upper()]
    except KeyError:
        # Return with error
        return _render_aiming_interface_with_error(
            request, game_id, player_id, f"Invalid coordinate: {coord}"
        )
    
    # Aim the shot
    result = gameplay_service.aim_shot(game_id, player_id, coord_obj)
    
    if not result.success:
        return _render_aiming_interface_with_error(
            request, game_id, player_id, result.error_message
        )
    
    # Success - return updated interface
    return _render_aiming_interface(request, game_id, player_id)
```

### 3. DELETE /game/{game_id}/aim-shot/{coord} (MODIFY EXISTING)
**Current**: Returns JSON
**Needed**: Return HTML component (aiming_interface.html)

**Implementation**:
```python
@app.delete("/game/{game_id}/aim-shot/{coord}")
async def clear_aimed_shot(
    request: Request, 
    game_id: str, 
    coord: str
) -> HTMLResponse:
    player_id = _get_player_id(request)
    _ensure_gameplay_initialized(game_id, player_id)
    
    # Parse coordinate
    try:
        coord_obj = Coord[coord.upper()]
    except KeyError:
        return _render_aiming_interface_with_error(
            request, game_id, player_id, f"Invalid coordinate: {coord}"
        )
    
    # Remove the shot
    gameplay_service.clear_aimed_shot(game_id, player_id, coord_obj)
    
    # Return updated interface
    return _render_aiming_interface(request, game_id, player_id)
```

### 4. POST /game/{game_id}/fire-shots (NEW ENDPOINT)
**Purpose**: Fire all aimed shots and transition to next phase

**Returns**: HTML (full game page or next phase component)

**Implementation**: TBD - depends on Phase 3 (Shot Resolution) design

## Helper Functions Needed

```python
def _render_aiming_interface(
    request: Request, 
    game_id: str, 
    player_id: str
) -> HTMLResponse:
    """Render the aiming interface component."""
    aimed_coords = gameplay_service.get_aimed_shots(game_id, player_id)
    aimed_shots = [coord.name for coord in aimed_coords]
    shots_available = gameplay_service._get_shots_available(game_id, player_id)
    shots_fired = []  # TODO: Implement
    
    return templates.TemplateResponse(
        request,
        "components/aiming_interface.html",
        {
            "game_id": game_id,
            "aimed_shots": aimed_shots,
            "shots_fired": shots_fired,
            "shots_available": shots_available,
            "aimed_count": len(aimed_shots),
            "error_message": None,
        },
    )

def _render_aiming_interface_with_error(
    request: Request, 
    game_id: str, 
    player_id: str, 
    error_message: str
) -> HTMLResponse:
    """Render the aiming interface component with an error message."""
    aimed_coords = gameplay_service.get_aimed_shots(game_id, player_id)
    aimed_shots = [coord.name for coord in aimed_coords]
    shots_available = gameplay_service._get_shots_available(game_id, player_id)
    shots_fired = []  # TODO: Implement
    
    return templates.TemplateResponse(
        request,
        "components/aiming_interface.html",
        {
            "game_id": game_id,
            "aimed_shots": aimed_shots,
            "shots_fired": shots_fired,
            "shots_available": shots_available,
            "aimed_count": len(aimed_shots),
            "error_message": error_message,
        },
    )
```

## GameplayService Changes Needed

### Add method to get previously fired shots
```python
def get_fired_shots(self, game_id: str, player_id: str) -> list[Coord]:
    """Get all shots fired by player in previous rounds.
    
    This is needed to show which cells are no longer available for aiming.
    """
    # TODO: Implement - track fired shots across rounds
    return []
```

## Template Context Requirements

All aiming interface components expect these variables in context:
- `game_id`: str - The game ID
- `aimed_shots`: list[str] - Currently aimed coordinates (e.g., ["A1", "B2"])
- `shots_fired`: list[str] - Previously fired coordinates
- `shots_available`: int - Total shots available this round
- `aimed_count`: int - Number of shots currently aimed
- `error_message`: str | None - Error message to display (if any)

## Testing Checklist

After implementing backend changes:
- [ ] GET /game/{game_id}/aiming-interface loads correctly
- [ ] Clicking a cell POSTs to /game/{game_id}/aim-shot and updates interface
- [ ] Clicking remove button DELETEs and updates interface
- [ ] Error messages display when aiming fails (duplicate, limit exceeded)
- [ ] Fire button is disabled when no shots aimed
- [ ] Fire button is enabled when shots are aimed
- [ ] Shot counter updates correctly
- [ ] Aimed shots list updates correctly
- [ ] Board cells show correct states (available, aimed, fired)
