# AGENTS.md - Agent Coding Guidelines

## Technology Stack

- **Python**: 3.13+ (managed via uv package manager)
- **Backend**: FastAPI with Uvicorn server
- **Template Engine**: Jinja2 for HTML templating
- **Frontend**: Follow HATEOAS principles. Use only HTML, CSS, and HTMX. No javascript.
- **Testing**: pytest with BDD support (via pytest-bdd ), pytest-asyncio, pytest-cov
- **Browser Testing**: Playwright for end-to-end testing
- **Package Management**: UV (modern Python package manager)

## Build/Test Commands

- `uv run pytest tests/` - Run all tests
- `uv run pytest tests/features/` - Run BDD feature tests only
- `uv run pytest -k "test_name"` - Run specific test
- `uv run pytest --cov` - Run tests with coverage
- `uv run uvicorn main:app --reload` - Start development server
- `./scripts/test.sh` - Full test suite with server startup/shutdown

## Code Style

- **Type Hints**: Use full type annotations (FastAPI, NamedTuple pattern)
- **Imports**: Group stdlib, third-party, local imports separately
- **Functions**: Use descriptive names, return type annotations required
- **Variables**: Use snake_case, explicit types with colon syntax (`app: FastAPI`)
- **Error Handling**: Return validation objects with structured error messages
- **Testing**: Follow BDD with pytest-bdd, use descriptive step functions
- **Naming**: Use clear, domain-specific names (`PlayerNameValidation`)

## BDD/TDD Workflow

We are following strict BDD and TDD techniques so we will be taking development very slowly. Strictly following TDD workflow starting with BDD features, tests, and then implementation. We should follow the RED, GREEN, REFACTOR flow.
The project follows behavior-driven development with Gherkin feature files. 

## Architecture

- FastAPI backend with Jinja2 templates, no JavaScript
- BDD-first development with Gherkin features
- Strict TDD workflow: RED → GREEN → REFACTOR

