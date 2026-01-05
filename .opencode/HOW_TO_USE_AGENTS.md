# How to Use OpenCode Agents

This guide explains how to use the converted OpenCode agents for the Battleships project.

## Quick Start

### 1. Start OpenCode

```bash
cd /home/david/dev/battleships
opencode
```

### 2. Switch to the Primary Agent

Press **Tab** to cycle through primary agents until you see `battleships-dev` in the lower-right corner.

The `battleships-dev` agent is your main development orchestrator that:
- Understands the full project context
- Automatically delegates to specialized agents
- Enforces TDD/BDD discipline
- Manages task tracking and code quality

### 3. Start Working

Just describe what you want to do, and the primary agent will handle delegation:

```
Help me implement a new feature to validate ship placement
```

The agent will automatically:
1. Create a todo list for complex tasks
2. Delegate to `@bdd-feature-writer` if BDD scenarios are needed
3. Use `@tdd-workflow-guide` to enforce RED-GREEN-REFACTOR
4. Call specialists like `@fastapi-service-builder` or `@htmx-template-builder` as needed
5. Run `@type-hint-enforcer` before completing

## Manual Agent Invocation

You can directly invoke any subagent using the `@agent-name` syntax:

### BDD Feature Writing
```
@bdd-feature-writer create a feature file for user registration
@bdd-feature-writer review the ship placement feature for completeness
```

### Test Implementation
```
@dual-test-implementer implement tests for the lobby feature
@endpoint-test-writer create integration tests for the login endpoint
```

### Code Development
```
@fastapi-service-builder help me create an endpoint for game moves
@htmx-template-builder build a component for displaying ships
@css-theme-designer style the lobby page with a naval theme
```

### Quality Assurance
```
@type-hint-enforcer review game/player.py for missing type hints
@type-hint-enforcer check all files in services/ directory
```

### TDD Workflow
```
@tdd-workflow-guide help me implement ship rotation using TDD
@tdd-workflow-guide guide me through fixing the validation bug
```

## Available Agents

### Primary Agent

**battleships-dev** (mode: primary)
- Main development orchestrator
- Automatically delegates to specialists
- Enforces TDD/BDD discipline
- Manages todos and code quality

### Specialized Subagents

1. **@bdd-feature-writer**
   - Creates Gherkin feature files
   - Temperature: 0.3 (balanced creativity)
   - Output: `features/*.feature`

2. **@dual-test-implementer**
   - Implements BDD test step definitions
   - Creates both FastAPI and Playwright tests
   - Temperature: 0.2 (precise)
   - Output: `tests/bdd/test_*_steps_*.py`

3. **@endpoint-test-writer**
   - Writes integration tests for FastAPI endpoints
   - Temperature: 0.2 (precise)
   - Output: `tests/endpoint/test_*_endpoints.py`

4. **@fastapi-service-builder**
   - Creates layered FastAPI endpoints and services
   - Ensures proper architecture (Routes → Services → Models)
   - Temperature: 0.2 (precise)
   - Output: Code for `main.py` and `services/`

5. **@htmx-template-builder**
   - Builds HATEOAS-compliant HTMX templates
   - NO JavaScript (HTML/CSS/HTMX only)
   - Temperature: 0.3 (balanced)
   - Output: `templates/*.html` and `templates/components/*.html`

6. **@css-theme-designer**
   - Creates CSS themes and styling
   - Pure CSS only (animations, transitions, etc.)
   - Temperature: 0.4 (creative)
   - Output: `static/css/*.css`

7. **@tdd-workflow-guide**
   - Guides through RED-GREEN-REFACTOR cycles
   - Enforces TDD discipline
   - Temperature: 0.1 (focused, deterministic)
   - Runs tests automatically (pytest commands allowed)

8. **@type-hint-enforcer**
   - Ensures comprehensive type hints
   - Reviews code before commits
   - Temperature: 0.1 (focused, deterministic)
   - Read-only (no file modifications)

## Agent Delegation Flow

```
User Request
    ↓
battleships-dev (primary)
    ↓
    ├→ New feature? → @tdd-workflow-guide
    │                     ├→ Need BDD? → @bdd-feature-writer
    │                     ├→ Need tests? → @dual-test-implementer
    │                     ├→ Need endpoints? → @fastapi-service-builder
    │                     └→ Need templates? → @htmx-template-builder
    │
    ├→ Styling work? → @htmx-template-builder → @css-theme-designer
    │
    ├→ Integration tests? → @endpoint-test-writer
    │
    └→ Before commit? → @type-hint-enforcer
```

## Common Workflows

### Implementing a New Feature

**What to say:**
```
I want to add a feature where players can chat in the lobby
```

**What happens:**
1. Primary agent creates a todo list
2. Delegates to `@bdd-feature-writer` for feature file
3. Delegates to `@tdd-workflow-guide` for TDD implementation
4. Within TDD, may use:
   - `@fastapi-service-builder` for chat endpoint
   - `@htmx-template-builder` for chat UI
   - `@dual-test-implementer` for BDD tests
5. Runs `@type-hint-enforcer` before completion
6. Marks todos complete

### Styling the UI

**What to say:**
```
The game board needs better visual design
```

**What happens:**
1. Delegates to `@htmx-template-builder` to review HTML structure
2. Delegates to `@css-theme-designer` to create/update styles
3. Ensures HTMX functionality is preserved (NO JavaScript)

### Fixing a Bug

**What to say:**
```
Fix the bug where ship placement allows overlapping ships
```

**What happens:**
1. Writes a failing test first (TDD discipline!)
2. Implements the fix (minimal code)
3. Refactors if needed (while tests are green)
4. Runs `@type-hint-enforcer` to verify type hints
5. Ready to commit

### Reviewing Code Quality

**Before committing:**
```
@type-hint-enforcer review all changes in game/ directory
```

**For architecture review:**
```
@fastapi-service-builder review the lobby service for proper layering
```

## Temperature Values Explained

Agents have different temperature settings for optimal output:

- **0.1** (Most focused) - TDD guide, type enforcer
  - Deterministic, precise
  - Consistent guidance
  
- **0.2** (Precise) - Test writers, endpoint builder
  - Accurate code generation
  - Follows patterns exactly
  
- **0.3** (Balanced) - BDD writer, HTMX builder, primary agent
  - Mix of creativity and precision
  - Good for planning and structure
  
- **0.4** (Creative) - CSS designer
  - More design freedom
  - Varied styling approaches

## Permissions

Agents have granular bash command permissions:

### Allowed Automatically
- `uv run pytest*` - Running tests
- `uv run python*` - Running Python scripts
- `uv sync` - Syncing dependencies
- `git status`, `git diff*`, `git log*` - Read-only git commands

### Ask Before Running
- `git add*`, `git commit*`, `git push*` - Modifying git state
- Any other bash commands

This prevents accidental changes while allowing safe operations.

## Tips for Best Results

### 1. Be Specific About What You Want
✅ Good: "Create a BDD feature for validating ship placement rules"
❌ Vague: "Help with ships"

### 2. Let the Primary Agent Delegate
The `battleships-dev` agent knows when to use specialists. Trust its judgment.

### 3. Use Manual Invocation for Direct Tasks
When you know exactly which specialist you need:
```
@css-theme-designer create a dark theme for the game
```

### 4. Always Review Before Committing
```
@type-hint-enforcer review all modified files
```

### 5. Embrace TDD Discipline
This is a learning project. Let `@tdd-workflow-guide` enforce RED-GREEN-REFACTOR.

### 6. No JavaScript Ever
Agents are configured to enforce HTMX-only frontends. This is non-negotiable.

## Switching Between Primary Agents

You have access to multiple primary agents:

1. **battleships-dev** (Custom)
   - Project-aware, orchestrates specialists
   - Best for feature development
   
2. **build** (Built-in)
   - Full manual control
   - Use when you want complete freedom
   
3. **plan** (Built-in)
   - Read-only mode
   - Use for analysis without changes

Press **Tab** to cycle between them.

## Navigating Agent Sessions

When subagents create child sessions:
- **Leader+Right** - Cycle forward through sessions
- **Leader+Left** - Cycle backward through sessions

This lets you switch between the main conversation and specialist work.

## Example Conversations

### Starting a New Feature
```
You: Help me implement a feature to undo ship placements

Agent: I'll help you implement this feature using TDD. Let me create a todo list:
1. Create/update BDD feature file
2. Implement using RED-GREEN-REFACTOR
3. Add endpoint for undo action
4. Create UI button
5. Verify type hints

Let me start by delegating to @bdd-feature-writer...
```

### Getting Quick Help
```
You: @bdd-feature-writer show me an example of a good scenario

Agent: Here's an example from this project:

Scenario: Player places ship successfully
  Given I am logged in as "Alice"
  And I am on the ship placement page
  When I place a Carrier at A1 facing horizontal
  Then the ship should be placed on the board
  And I should see the ship at coordinates A1-A5
```

### Code Review
```
You: @type-hint-enforcer check game/player.py

Agent: ## Type Hint Review: game/player.py

### Issues Found:
- Line 15: Missing parameter type for `status`
- Line 23: Using old Optional[str] syntax
- Line 30: Variable `players` not typed

### Fixed Code:
[Shows corrected version]

### Summary:
✅ Fixed 3 type hint issues
```

## Troubleshooting

### Agent Not Responding as Expected
1. Make sure you're using the right agent (check lower-right corner)
2. Try manual invocation: `@agent-name your request`
3. Be more specific about what you want

### Want More Control
Switch to the built-in `build` agent (press Tab)

### Want to Analyze Without Changes
Switch to the built-in `plan` agent (press Tab)

### Agent Asks Permission Too Much
This is intentional for safety. Approve with `y` or deny with `n`.

## File Locations

All agents are in:
```
.opencode/agent/
├── battleships-dev.md           (PRIMARY)
├── bdd-feature-writer.md         (subagent)
├── css-theme-designer.md         (subagent)
├── dual-test-implementer.md      (subagent)
├── endpoint-test-writer.md       (subagent)
├── fastapi-service-builder.md    (subagent)
├── htmx-template-builder.md      (subagent)
├── tdd-workflow-guide.md         (subagent)
└── type-hint-enforcer.md         (subagent)
```

## Getting Help

If you're unsure which agent to use, just ask the primary agent:
```
Which agent should I use to create CSS animations?
```

The `battleships-dev` agent will explain and delegate appropriately.

## Remember

- **Trust the orchestration** - The primary agent knows when to delegate
- **Embrace TDD** - This is a learning project about test-driven development
- **No JavaScript** - Agents enforce HTMX-only frontends
- **Type hints everywhere** - Quality gate before commits
- **Manual invocation available** - Use `@agent-name` when you need direct access

Happy coding! 🚢
