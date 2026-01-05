# OpenCode Agents - Quick Reference

## Starting OpenCode

```bash
cd /home/david/dev/battleships
opencode
```

Press **Tab** to switch to `battleships-dev` primary agent.

## Agent Quick Reference

| Agent | Invoke With | Use For |
|-------|------------|---------|
| **battleships-dev** | (primary) | Everything - orchestrates all others |
| **bdd-feature-writer** | `@bdd-feature-writer` | Gherkin feature files |
| **dual-test-implementer** | `@dual-test-implementer` | BDD test step definitions |
| **endpoint-test-writer** | `@endpoint-test-writer` | FastAPI integration tests |
| **fastapi-service-builder** | `@fastapi-service-builder` | Endpoints and services |
| **htmx-template-builder** | `@htmx-template-builder` | HTMX templates (NO JS) |
| **css-theme-designer** | `@css-theme-designer` | CSS styling |
| **tdd-workflow-guide** | `@tdd-workflow-guide` | RED-GREEN-REFACTOR cycles |
| **type-hint-enforcer** | `@type-hint-enforcer` | Type hint review |

## Common Commands

### Feature Development
```
Implement a feature to [description]
# Primary agent auto-delegates to specialists

@tdd-workflow-guide implement [feature] using TDD
# Manual TDD workflow
```

### Testing
```
@dual-test-implementer create tests for [feature]
@endpoint-test-writer add integration tests for [endpoint]
```

### UI Work
```
@htmx-template-builder create a page for [feature]
@css-theme-designer style the [component]
```

### Code Quality
```
@type-hint-enforcer review [file]
@type-hint-enforcer check all changes
```

### Planning
```
@bdd-feature-writer create a feature for [behavior]
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Tab** | Switch between primary agents |
| **Leader+Right** | Cycle to child session |
| **Leader+Left** | Cycle to parent session |

## Temperature Guide

| Temp | Agents | Purpose |
|------|--------|---------|
| 0.1 | TDD guide, Type enforcer | Focused, deterministic |
| 0.2 | Test writers, Endpoint builder | Precise coding |
| 0.3 | BDD writer, HTMX builder, Primary | Balanced |
| 0.4 | CSS designer | Creative |

## Typical Workflows

### New Feature Flow
```
1. Request → battleships-dev
2. Auto-delegates to:
   - @bdd-feature-writer (feature file)
   - @tdd-workflow-guide (RED-GREEN-REFACTOR)
     - @fastapi-service-builder (endpoints)
     - @htmx-template-builder (templates)
     - @dual-test-implementer (BDD tests)
   - @type-hint-enforcer (quality check)
3. Done!
```

### Bug Fix Flow
```
1. Write failing test (TDD!)
2. Fix bug (minimal code)
3. Refactor (while green)
4. @type-hint-enforcer review
5. Commit
```

### Styling Flow
```
1. @htmx-template-builder (HTML structure)
2. @css-theme-designer (CSS styling)
3. Test HTMX functionality
```

## Bash Permissions

### Auto-Allowed
- `uv run pytest*`
- `uv run python*`
- `uv sync`
- `git status/diff/log`

### Requires Approval
- `git add/commit/push`
- Other commands

## Project Constraints

❌ **NO JavaScript** - HTMX and CSS only
✅ **TDD/BDD** - Test first, always
✅ **Type hints** - Everywhere, modern syntax
✅ **HATEOAS** - Server-driven navigation
✅ **Layered** - Routes → Services → Models

## File Outputs

| Agent | Outputs |
|-------|---------|
| bdd-feature-writer | `features/*.feature` |
| dual-test-implementer | `tests/bdd/test_*_steps_*.py` |
| endpoint-test-writer | `tests/endpoint/test_*.py` |
| fastapi-service-builder | `main.py`, `services/*.py` |
| htmx-template-builder | `templates/*.html` |
| css-theme-designer | `static/css/*.css` |

## Quick Tips

✅ **Let primary agent delegate** - It knows best
✅ **Be specific** - "Create login endpoint" not "help with login"
✅ **Use @mentions** - When you know which specialist you need
✅ **Review before commit** - `@type-hint-enforcer` is your friend
✅ **Embrace TDD** - This is a learning project

❌ **Don't skip tests** - TDD is non-negotiable
❌ **Don't add JavaScript** - Agents will reject it
❌ **Don't bypass type hints** - Required everywhere

## Example Requests

```
# Feature development
Implement ship rotation feature

# Specific agent work
@css-theme-designer create a naval-themed color scheme
@bdd-feature-writer add scenarios for error handling
@type-hint-enforcer review all services

# Bug fixing
Fix the validation bug in ship placement

# UI work
Create a lobby page with live player updates

# Testing
@endpoint-test-writer test the login flow
@dual-test-implementer implement the lobby feature tests
```

## Getting More Help

See full guide: `.opencode/HOW_TO_USE_AGENTS.md`
See conversion details: `.opencode/AGENT_CONVERSION.md`

Or just ask:
```
How do I [task]?
Which agent handles [topic]?
```

The primary agent will guide you!
