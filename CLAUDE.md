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
uv run pytest                     # Run all tests
uv run pytest --cov              # Run tests with coverage
uv run pytest -v                 # Run tests with verbose output
uv run pytest -k "test_name"     # Run specific test
uv run pytest features/          # Run BDD feature tests
uv run pytest -m wip             # Run work-in-progress tests
uv run pytest tests/unit/        # Run unit tests only
uv run pytest tests/integration/ # Run integration tests only
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
  - `lobby.py` - Multiplayer lobby management
  - `player.py` - Player models and game requests
- `services/` - Business logic services
  - `auth_service.py` - Player authentication and validation
  - `lobby_service.py` - Lobby operations and real-time updates
- `templates/` - Jinja2 HTML templates and components

### Testing Structure
- `features/` - BDD feature files (Gherkin syntax)
  - `login.feature` - Player authentication scenarios
  - `ship_placement.feature` - Ship placement rules and validation
  - `multiplayer_lobby.feature` - Lobby functionality
  - `long_polling_updates.feature` - Real-time update scenarios
- `tests/bdd/` - BDD step definitions and test implementations
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for service interactions

## BDD/TDD Workflow

We are learning BDD and TDD techniques so we will be taking development very slowly. Strictly following TDD workflow starting with BDD. We should follow the RED, GREEN, REFACTOR flow.

The project follows behavior-driven development with comprehensive Gherkin feature files covering:
- Player authentication and validation
- Ship placement with complex positioning rules
- Multiplayer lobby with real-time updates
- Long-polling for live game state synchronization

## Architecture Notes

### Web Application Architecture
- **FastAPI Backend**: Single main.py file with all HTTP endpoints
- **Service Layer**: Separated business logic (auth_service, lobby_service)
- **Real-time Updates**: Long-polling implementation for lobby state changes
- **Template Rendering**: Server-side rendering with Jinja2 and HTMX for dynamic updates

### Game State Management
- **Global Lobby**: Centralized lobby instance for multiplayer coordination
- **Player Status Tracking**: Available, Busy, In-Game states with transitions
- **Game Requests**: Async request/accept/decline workflow for player matching
- **Version-based Updates**: Lobby versioning for efficient long-polling

### Frontend Architecture
- **HATEOAS Principles**: Hypermedia-driven navigation and state transitions
- **HTMX Integration**: Progressive enhancement for dynamic content updates
- **Component Templates**: Reusable template components for dynamic UI parts
- **Form Handling**: Both HTMX and standard form submission support

### Key Features
- Player login with comprehensive name validation
- Dual game modes: single-player vs computer, multiplayer vs humans
- Real-time multiplayer lobby with live player status updates
- Complex ship placement rules (horizontal, vertical, diagonal with spacing requirements)
- Long-polling for efficient real-time updates without WebSockets
