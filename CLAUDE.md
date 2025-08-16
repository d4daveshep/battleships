# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a variation of the Battleships game. I want to use it to learn and practice BDD and TDD techniques.

## Technology Stack

- **Python**: 3.13+ (managed via uv package manager)
- **Backend**: FastAPI with Uvicorn server
- **Template Engine**: Jinja2 for HTML templating
- Frontend: HTML/CSS/HTMX. No javascript.
- **Testing**: pytest with BDD support (pytest-bdd likely), pytest-asyncio, pytest-cov
- **Browser Testing**: Playwright for end-to-end testing
- **Package Management**: UV (modern Python package manager)

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
uv run pytest                    # Run all tests
uv run pytest --cov             # Run tests with coverage
uv run pytest -v                # Run tests with verbose output
uv run pytest -k "test_name"    # Run specific test
uv run pytest features/         # Run BDD feature tests
```

### Development Server

```bash
uv run uvicorn <app_module>:<app_instance> --reload    # Start development server
```

## Project Structure

- `features/` - BDD feature files (Gherkin syntax)
  - `login.feature` - Player login and game mode selection scenarios
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions

## BDD/TDD Workflow

We are learning BDD and TDD techniques so we will be taking development very slowly. Strictly following TDD workflow starting with BDD. We should follow the RED, GREEN, REFACTOR flow.
The project follows behavior-driven development with Gherkin feature files. The login.feature file contains comprehensive scenarios for player authentication and game mode selection, including validation, error handling, and accessibility requirements.

## Architecture Notes

This appears to be a web-based battleship game with:

- Player login system with name validation
- Game mode selection (vs Computer / vs Human)
- FastAPI backend for game logic and API endpoints
- Frontend integration (likely HTML/HTMX/Jinja2 templates)
- Multi-player capability architecture

The codebase currently contains feature specifications but minimal implementation, suggesting active BDD/TDD development in progress.

