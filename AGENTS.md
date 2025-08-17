# AGENTS.md - Agent Coding Guidelines

## Build/Test Commands
- `uv run pytest` - Run all tests
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

## Architecture
- FastAPI backend with Jinja2 templates, no JavaScript
- BDD-first development with Gherkin features
- Strict TDD workflow: RED → GREEN → REFACTOR