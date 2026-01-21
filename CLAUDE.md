# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a variation of the Battleships game used to learn and practice BDD and TDD techniques. The application supports both single-player (vs computer) and multiplayer (vs human) game modes with real-time updates.

## Technology Stack

- **Python**: 3.13+ (managed via uv package manager)
- **Backend**: FastAPI with Uvicorn server
- **Template Engine**: Jinja2 for HTML templating
- **Frontend**: Follow HATEOAS principles. Use only HTML, CSS, and HTMX. No javascript.
- **Testing**: pytest with BDD support (via pytest-bdd), pytest-asyncio, pytest-cov
- **Browser Testing**: Playwright for end-to-end testing
- **HTML Parsing**: BeautifulSoup4 (bs4) for test assertions
- **Linting**: ruff
- **HTTP Client**: httpx for test requests
- **Package Management**: UV (modern Python package manager)

## Code Style Requirements

### Type Hints
All Python code must include comprehensive type hints:
- All function parameters and return types
- Internal variables, especially for complex types (Response, Tag, dict, list, etc.)
- Class attributes and methods
- Fixture return types in tests
- Use modern Python 3.10+ union syntax: `str | None` instead of `Optional[str]`
- Use generic types: `dict[str, str]`, `list[int]`, etc.
- Use `typing.Any` for **kwargs and other dynamic types when needed

## Development Commands

### Package Management

```bash
uv sync                    # Install/sync all dependencies
uv add <package>          # Add new dependency
uv add --dev <package>    # Add development dependency
uv remove <package>       # Remove dependency
```

### Running Tests

```bash
uv run pytest                     # Run all tests (excludes WIP scenarios by default)
uv run pytest --cov              # Run tests with coverage
uv run pytest -v                 # Run tests with verbose output
uv run pytest -k "test_name"     # Run specific test by name pattern
uv run pytest features/          # Run BDD feature tests
uv run pytest -m wip             # Run ONLY work-in-progress tests (marked with `wip` marker)
uv run pytest tests/unit/        # Run unit tests only
uv run pytest tests/endpoint/    # Run endpoint/integration tests only
uv run pytest tests/bdd/         # Run BDD step definitions
```

### Development Server

```bash
uv run uvicorn main:app --reload           # Start development server
uv run python main.py                      # Alternative way to start server
```

## Project Structure

### Core Application Files
- `main.py` - FastAPI application entry point with all routes
- `game/` - Core game logic and models
  - `model.py` - Ship types, coordinates, game board, and placement rules
  - `player.py` - Player models, statuses, and game requests
  - `lobby.py` - Multiplayer lobby with version-based change tracking
  - `game_service.py` - Game creation and state management
- `services/` - Business logic services
  - `auth_service.py` - Player authentication and name validation
  - `lobby_service.py` - Lobby operations and real-time updates
- `templates/` - Jinja2 HTML templates
  - `components/` - Reusable HTMX-compatible components for dynamic updates
- `static/css/` - CSS stylesheets

### Testing Structure
- `features/` - BDD feature files (Gherkin syntax)
  - `login.feature` - Player authentication scenarios
  - `ship_placement.feature` - Ship placement rules and validation
  - `multiplayer_lobby.feature` - Lobby functionality
  - `multiplayer_ship_placement.feature` - Two-player ship placement coordination
  - `long_polling_updates.feature` - Real-time update scenarios
  - `start_game_confirmation_page.feature` - Game mode selection confirmation
  - `two_player_gameplay.feature` - Two-player battle phase gameplay
- `tests/bdd/` - BDD step definitions (both FastAPI and browser-based)
- `tests/unit/` - Unit tests for individual components (models, services, game logic)
- `tests/endpoint/` - Integration tests for FastAPI endpoints

## BDD/TDD Workflow

We are learning BDD and TDD techniques so we will be taking development very slowly. Strictly following TDD workflow starting with BDD. We should follow the RED, GREEN, REFACTOR flow.

The project follows behavior-driven development with comprehensive Gherkin feature files covering:
- Player authentication and validation
- Ship placement with complex positioning rules
- Multiplayer lobby with real-time updates
- Long-polling for live game state synchronization

### Test Infrastructure
- **Session-scoped FastAPI server**: BDD tests start a real server (port 8000) for the entire test session
- **Dual test approaches**: Each feature has both FastAPI-based (HTTP client) and browser-based (Playwright) test implementations
- **Automatic lobby reset**: The `reset_lobby` fixture ensures clean state before each scenario via `/test/reset-lobby` endpoint
- **Long-polling timeouts**: Page fixtures configured with 40s timeout to accommodate 35s long-poll operations

## Architecture Notes

### Web Application Architecture
- **FastAPI Backend**: Single main.py file with all HTTP endpoints
- **Service Layer**: Separated business logic (auth_service, lobby_service)
- **Real-time Updates**: Long-polling implementation for lobby state changes
- **Template Rendering**: Server-side rendering with Jinja2 and HTMX for dynamic updates

### Game State Management
- **Global Lobby**: Centralized lobby instance (`_game_lobby` in main.py) for multiplayer coordination
- **Player Status Tracking**: Four states: AVAILABLE, REQUESTING_GAME, PENDING_RESPONSE, IN_GAME
- **Game Requests**: Async request/accept/decline workflow for player matching
- **Version-based Updates**: Lobby versioning with `asyncio.Event` for efficient long-polling
- **Session-based Authentication**: Player IDs stored in session cookies (using Starlette SessionMiddleware)
- **Game Instances**: Tracked separately from lobby once players are matched

### Frontend Architecture
- **HATEOAS Principles**: Hypermedia-driven navigation and state transitions
- **HTMX Integration**: Progressive enhancement for dynamic content updates
- **Component Templates**: Reusable template components for dynamic UI parts
- **Form Handling**: Both HTMX and standard form submission support

### Domain Model
- **Coordinates**: Enum-based system (A1-J10) with row/column indexing
- **Ship Types**: Carrier (5), Battleship (4), Cruiser (3), Submarine (3), Destroyer (2)
- **Orientations**: Horizontal, Vertical, Diagonal Up, Diagonal Down
- **Placement Rules**:
  - Ships cannot overlap or be adjacent (must have at least 1 cell spacing)
  - Each ship type can only be placed once per board
  - Ships must stay within 10x10 grid boundaries

### Key Features
- Player login with comprehensive name validation (length, characters, profanity checks)
- Dual game modes: single-player vs computer, multiplayer vs humans
- Real-time multiplayer lobby with live player status updates
- Complex ship placement rules (horizontal, vertical, diagonal with spacing requirements)
- Long-polling for efficient real-time updates without WebSockets
- Auto-generated unique player IDs using cryptographic tokens
