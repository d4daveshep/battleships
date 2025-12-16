# GEMINI.md

This file serves as a comprehensive context guide for AI agents working on the Battleships project.

## Project Overview

**Battleships** is a Python-based web application designed to implement the classic naval combat game. The project focuses on learning and practicing **Behavior-Driven Development (BDD)** and **Test-Driven Development (TDD)** techniques.

The application supports:
*   **Single Player:** Human vs. Computer.
*   **Multiplayer:** Human vs. Human (via a lobby system).

## Technology Stack

*   **Language:** Python 3.13+
*   **Package Manager:** `uv`
*   **Web Framework:** FastAPI (with Uvicorn)
*   **Templating:** Jinja2
*   **Frontend:** HTML, CSS, HTMX (No custom JavaScript allowed; strictly HATEOAS principles).
*   **CLI UI:** `Rich` library (for terminal interface).
*   **Testing:**
    *   `pytest`: Test runner.
    *   `pytest-bdd`: BDD framework (Gherkin feature files).
    *   `playwright`: End-to-end browser testing.
    *   `pytest-asyncio`: Async test support.
    *   `pytest-cov`: Code coverage.

## Architecture

The project follows a layered architecture separating concerns:

1.  **Presentation Layer (`main.py`, `templates/`)**:
    *   FastAPI endpoints handle HTTP requests.
    *   Returns HTML responses (full pages or HTMX partials).
    *   **Rule:** No game state management in the UI (HATEOAS).

2.  **Service Layer (`services/`)**:
    *   Contains business logic.
    *   `auth_service.py`: Validates player identities.
    *   `lobby_service.py`: Manages the multiplayer lobby, game requests, and long-polling for updates.

3.  **Domain/Model Layer (`game/`)**:
    *   `model.py`: Core game entities (`GameBoard`, `Ship`, `Coord`). Handles logic like ship placement validation (spacing, bounds).
    *   `lobby.py`: Manages the state of players and matchmaking requests.
    *   `player.py`: Player data structures.

## Development Workflow

This project strictly follows a **RED-GREEN-REFACTOR** loop, driven by BDD scenarios.

### 1. Build & Run
*   **Install Dependencies:** `uv sync`
*   **Start Server:** `uv run uvicorn main:app --reload --port 8000` (or `scripts/start.sh`)
*   **Access:** `http://localhost:8000`

### 2. Testing
*   **Run All Tests:** `uv run pytest` (or `scripts/test.sh`)
*   **Run BDD Features:** `uv run pytest features/`
*   **Run WIP Tests:** `uv run pytest -m wip`
*   **Unit Tests:** `uv run pytest tests/unit/`

### 3. Coding Conventions
*   **Type Hints:** Mandatory for all functions, arguments, and return types. Use modern syntax (e.g., `str | None` instead of `Optional[str]`).
*   **Style:** Follow existing patterns.
*   **TDD:** Do not write code without a failing test (feature file -> step definition -> implementation).

## Key Game Rules

*   **Grid:** 10x10 (A-J vertical, 1-10 horizontal).
*   **Ships:** Carrier (5), Battleship (4), Cruiser (3), Submarine (3), Destroyer (2).
*   **Placement:**
    *   Horizontal, Vertical, or Diagonal.
    *   Must be within bounds.
    *   **Spacing:** Must have at least one empty square around every ship (no touching/overlapping), except at board edges.

## Project Structure

*   `main.py`: Application entry point.
*   `features/`: Gherkin feature files describing behavior.
*   `game/`: Domain logic.
*   `services/`: Application services.
*   `templates/`: HTML templates.
*   `tests/`: Test suite (split into `bdd`, `endpoint`, `unit`).
*   `CLAUDE.md`: Additional guidelines for AI assistants.
*   `BDD_FEATURES_PLAN.md`: Roadmap of features.

## Current Status

*   **Implemented:**
    *   Player Login/Authentication.
    *   Multiplayer Lobby (Long-polling, Matchmaking).
    *   Basic Ship Placement (Model logic exists, UI in progress).
*   **Planned/In Progress:**
    *   Game Initialization.
    *   Firing Shots.
    *   Round Processing.
    *   Computer Opponent.
