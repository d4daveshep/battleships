# Agent Guidelines for Battleships Codebase

## Project Overview

Battleships game built using BDD/TDD practices for learning purposes. Supports single-player (vs computer) and multiplayer (vs human) with real-time updates via long-polling.

## Project Structure

### Core Application

```
battleships/
├── main.py                      # FastAPI entry point, all routes
├── game/                        # Domain models and game logic
│   ├── model.py                 # Ship, Board, Game models
│   ├── player.py                # Player entity
│   ├── lobby.py                 # Multiplayer lobby
│   └── game_service.py          # Game domain logic
├── services/                    # Business logic layer
│   ├── auth_service.py          # Authentication
│   └── lobby_service.py         # Lobby management
├── templates/                   # Jinja2 templates
│   ├── base.html                # Base layout
│   ├── login.html               # Full page templates
│   ├── lobby.html
│   ├── ship_placement.html
│   ├── gameplay.html
│   ├── start_game.html
│   ├── welcome.html
│   └── components/              # HTMX-swappable components
│       ├── lobby_dynamic_content.html
│       ├── opponent_status.html
│       ├── player_name_input.html
│       └── error_message.html
├── static/css/                  # CSS stylesheets
│   └── main.css                 # Main stylesheet
├── features/                    # Gherkin BDD feature files
│   ├── login.feature
│   ├── multiplayer_lobby.feature
│   ├── ship_placement.feature
│   ├── long_polling_updates.feature
│   ├── multiplayer_ship_placement.feature
│   ├── start_game_confirmation_page.feature
│   └── two_player_gameplay.feature
├── tests/
│   ├── unit/                    # Unit tests for models and services
│   ├── endpoint/                # FastAPI endpoint integration tests
│   └── bdd/                     # BDD step definitions
│       ├── conftest.py
│       ├── test_*_steps_fastapi.py  # HTTP-based BDD tests
│       └── test_*_steps_browser.py  # Playwright BDD tests
```

## Code Style

**Type Hints**: Required everywhere - params, returns, variables (especially `Response`, `Tag`, `dict`, `list`). Use modern syntax: `str | None` not `Optional[str]`, `dict[str, str]`, `list[int]`. Use `typing.Any` for **kwargs.

**Imports**: Separate standard library, third-party, local (game/, services/) with blank lines. Type-only imports from typing.

**Naming**: snake_case (functions/variables), PascalCase (classes), UPPER_CASE (constants). Descriptive names.

**Classes**: `@dataclass` for data classes, `NamedTuple` for immutable results, `StrEnum` for string enums.

**Comments**: Docstrings for classes/public methods only. No inline comments unless absolutely necessary.

**Error Handling**: Return validation objects (NamedTuple) for validation, raise exceptions for unexpected errors.

**Frontend**: HATEOAS principles, HTML/CSS/HTMX only - NO JavaScript.

**TDD/BDD**: Follow strict RED-GREEN-REFACTOR. Write/update BDD features first, then step definitions, then implementation.

## Domain Model Reference

### Player Statuses

| Status | Description |
|--------|-------------|
| `AVAILABLE` | Ready to play, can receive game requests |
| `REQUESTING_GAME` | Sent a game request, awaiting response |
| `PENDING_RESPONSE` | Received a game request, needs to accept/decline |
| `IN_GAME` | Currently playing a game |

### Ship Types

| Ship | Length | Code |
|------|--------|------|
| Carrier | 5 | A |
| Battleship | 4 | B |
| Cruiser | 3 | C |
| Submarine | 3 | S |
| Destroyer | 2 | D |

### Orientations

- `horizontal`
- `vertical`
- `diagonal up`
- `diagonal down`

### Game Modes

- `single player` - vs computer
- `two player` - vs human

### Coordinates

- 10x10 grid: A1 through J10
- Row index: 0-9 (A=0, J=9)
- Column index: 0-9 (1=0, 10=9)

## Development Commands

### Package Management

- `uv sync` - Install/sync dependencies
- `uv add <package>` - Add dependency
- `uv add --dev <package>` - Add dev dependency
- `uv remove <package>` - Remove dependency

### Test Commands

- `uv run pytest` - Run all tests (excludes WIP by default)
- `uv run pytest --cov` - Run with coverage
- `uv run pytest -v` - Verbose output
- `uv run pytest -k "test_name"` - Run tests matching pattern
- `uv run pytest features/` - Run BDD feature tests
- `uv run pytest -m wip` - Run ONLY work-in-progress tests
- `uv run pytest tests/unit/` - Unit tests only
- `uv run pytest tests/endpoint/` - Endpoint/integration tests only
- `uv run pytest tests/bdd/` - BDD step definitions

### Development Server

- `uv run uvicorn main:app --reload` - Start dev server with hot reload
- `uv run python main.py` - Alternative start

## Specialist Agents

### @tdd-workflow-guide (Primary workflow for new features)

**When to use**: Implementing any new feature or fixing bugs  
**Purpose**: Ensures strict RED-GREEN-REFACTOR discipline  
**Key**: This is a LEARNING project - always use TDD workflow for features

### @bdd-feature-writer

**When to use**: Creating or refining Gherkin feature files  
**Purpose**: Writes clear, executable BDD scenarios  
**Output**: Feature files in `features/` directory

### @dual-test-implementer

**When to use**: After creating a feature file, implementing test steps  
**Purpose**: Creates both FastAPI and Playwright test implementations  
**Output**: Test files in `tests/bdd/`

### @fastapi-service-builder

**When to use**: Creating new endpoints or refactoring route/service architecture  
**Purpose**: Ensures proper layering (Routes → Services → Models)  
**Output**: Code for `main.py` and `services/`

### @htmx-template-builder

**When to use**: Building UI components or pages  
**Purpose**: Creates HATEOAS-compliant HTMX templates (NO JavaScript)  
**Output**: Templates in `templates/` and `templates/components/`

### @css-theme-designer

**When to use**: Adding visual design, styling pages, creating themes  
**Purpose**: CSS-only styling (animations, transitions, all pure CSS)  
**Output**: CSS files in `static/css/`

### @endpoint-test-writer

**When to use**: Writing integration tests for FastAPI endpoints  
**Purpose**: Tests HTML responses, session handling, HTMX interactions  
**Output**: Test files in `tests/endpoint/`

### @type-hint-enforcer

**When to use**: Before committing changes, during code review  
**Purpose**: Ensures comprehensive type hints across all Python code  
**Output**: Type-annotated code review and fixes

## Workflows

### New Feature (Standard Flow)

1. **Understand the requirement**
   - Clarify what the user wants
   - Break down into testable behaviors
   - Create a todo list using `todowrite`

2. **Create/Update BDD Feature** (if applicable)
   - Delegate to `@bdd-feature-writer`
   - Review the feature file for completeness

3. **Implement using TDD**
   - Delegate to `@tdd-workflow-guide` for RED-GREEN-REFACTOR cycle
   - Within TDD cycles, use specialists as needed:
     - Need endpoints? → `@fastapi-service-builder`
     - Need templates? → `@htmx-template-builder`
     - Need BDD step definitions? → `@dual-test-implementer`

4. **Verify Quality**
   - Delegate to `@type-hint-enforcer` to check type hints
   - Run all relevant tests (unit, integration, BDD)
   - Update todo list as tasks complete

5. **Style if needed**
   - If UI work was involved, optionally delegate to `@css-theme-designer`

### UI/Styling Work

1. **Structure first** → `@htmx-template-builder` for HTML
2. **Style second** → `@css-theme-designer` for CSS
3. **Test functionality** → Ensure HTMX features work
4. **Verify no JavaScript** → Strict requirement

### Bug Fix

1. **Write a failing test first** (TDD discipline!)
2. **Fix the bug** (minimal code)
3. **Refactor if needed** (while tests are green)
4. **Verify type hints** → `@type-hint-enforcer` before committing

## Decision Framework

For each user request, ask yourself:

1. **Is this a new feature?**
   - YES → Use `@tdd-workflow-guide` to enforce TDD discipline
   - Create todos if complex

2. **Does this need specialized expertise?**
   - BDD features → `@bdd-feature-writer`
   - Templates → `@htmx-template-builder`
   - Styling → `@css-theme-designer`
   - Endpoints → `@fastapi-service-builder`
   - BDD tests → `@dual-test-implementer`
   - Integration tests → `@endpoint-test-writer`

3. **Is this a simple change to existing code?**
   - Handle directly BUT write test first (TDD!)

4. **About to commit?**
   - Delegate to `@type-hint-enforcer` first

## Delegation vs Self-Handling

### Always Delegate:
- ✅ **New feature requests** → Start with `@tdd-workflow-guide`
- ✅ **BDD feature creation** → `@bdd-feature-writer`
- ✅ **BDD test implementation** → `@dual-test-implementer`
- ✅ **New endpoints/routes** → `@fastapi-service-builder`
- ✅ **Template/UI work** → `@htmx-template-builder`
- ✅ **Styling/theming** → `@css-theme-designer`
- ✅ **Endpoint integration tests** → `@endpoint-test-writer`
- ✅ **Before commits** → `@type-hint-enforcer` to verify type hints

### Handle Yourself:
- ⚡ Simple bug fixes in existing code (after writing a test first!)
- ⚡ Code review and analysis
- ⚡ Documentation updates (AGENTS.md, README.md)
- ⚡ Configuration changes (pyproject.toml, etc.)
- ⚡ Answering questions about the codebase
- ⚡ Running tests and interpreting results
- ⚡ Simple unit tests for straightforward functions

## Task Management

Use the todo system for complex tasks:

```
todowrite: Create todo list at start of complex features
todoread: Check current todos
todowrite: Update todos as work progresses
todowrite: Mark todos complete when finished
```

**When to use todos**:
- ✅ Features with 3+ distinct steps
- ✅ User provides multiple tasks
- ✅ Complex refactoring
- ✅ After receiving new instructions

**When NOT to use todos**:
- ❌ Single, straightforward tasks
- ❌ Trivial changes

## Architecture

### Web Application

- FastAPI backend (single main.py)
- Service layer (auth_service, lobby_service)
- Long-polling for real-time updates
- Server-side rendering with Jinja2 and HTMX

### Game State

- Global lobby for multiplayer coordination
- Player status tracking (Available, Busy, In-Game)
- Async request/accept/decline workflow
- Version-based updates for efficient long-polling

### Key Features

- Player login with name validation
- Dual modes: single-player vs computer, multiplayer vs humans
- Real-time lobby with live updates
- Complex ship placement rules
- Long-polling for real-time updates without WebSockets

## Testing Infrastructure

### Session-scoped FastAPI server

- BDD tests start a real server (port 8000) for the entire test session
- Use `/test/reset-lobby` endpoint to reset state before scenarios

### Dual test approaches

- Each feature has both FastAPI-based (HTTP client) and browser-based (Playwright) tests
- FastAPI tests: `test_*_steps_fastapi.py`
- Browser tests: `test_*_steps_browser.py`

### Long-polling timeouts

- Page fixtures configured with 40s timeout to accommodate 35s long-poll operations
