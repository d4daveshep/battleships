# Agent Guidelines for Battleships Codebase

## Project Overview
Battleships game for learning BDD/TDD. Supports single-player (vs computer) and multiplayer (vs human) with real-time updates.

## Technology Stack
- **Python**: 3.13+ (managed via uv)
- **Backend**: FastAPI with Uvicorn
- **Templates**: Jinja2
- **Frontend**: HATEOAS principles, HTML/CSS/HTMX only - NO JavaScript
- **Testing**: pytest, pytest-bdd, pytest-asyncio, pytest-cov, Playwright

## Development Commands

### Package Management
- `uv sync` - Install/sync dependencies
- `uv add <package>` - Add dependency
- `uv add --dev <package>` - Add dev dependency
- `uv remove <package>` - Remove dependency

### Test Commands
- `uv run pytest` - Run all tests
- `uv run pytest --cov` - Run with coverage
- `uv run pytest -v` - Verbose output
- `uv run pytest -k "test_name"` - Run tests matching pattern
- `uv run pytest features/` - Run BDD feature tests
- `uv run pytest -m wip` - Run work-in-progress tests
- `uv run pytest tests/unit/` - Unit tests only
- `uv run pytest tests/integration/` - Integration tests only
- `uv run pytest tests/bdd/` - BDD step definitions
- No separate lint/typecheck commands configured

### Development Server
- `uv run uvicorn main:app --reload` - Start dev server
- `uv run python main.py` - Alternative start

## Project Structure

### Core Application
- `main.py` - FastAPI entry point with all routes
- `game/` - Core game logic (lobby.py, player.py)
- `services/` - Business logic (auth_service.py, lobby_service.py)
- `templates/` - Jinja2 templates and components

### Testing
- `features/` - BDD feature files (Gherkin)
- `tests/bdd/` - BDD step definitions
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests

## Code Style

**Type Hints**: Required everywhere - params, returns, variables (especially `Response`, `Tag`, `dict`, `list`). Use modern syntax: `str | None` not `Optional[str]`, `dict[str, str]`, `list[int]`. Use `typing.Any` for **kwargs.

**Imports**: Separate standard library, third-party, local (game/, services/) with blank lines. Type-only imports from typing.

**Naming**: snake_case (functions/variables), PascalCase (classes), UPPER_CASE (constants). Descriptive names.

**Classes**: `@dataclass` for data classes, `NamedTuple` for immutable results, `StrEnum` for string enums.

**Comments**: Docstrings for classes/public methods only. No inline comments unless absolutely necessary.

**Error Handling**: Return validation objects (NamedTuple) for validation, raise exceptions for unexpected errors.

**Frontend**: HATEOAS principles, HTML/CSS/HTMX only - NO JavaScript.

**TDD/BDD**: Follow RED-GREEN-REFACTOR. Write/update BDD features first, then step definitions, then implementation.

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
