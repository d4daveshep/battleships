# Agent Conversion Summary

Successfully converted 8 Claude agents to OpenCode agents and created 1 primary agent.

## Conversion Date
2026-01-05

## Agents Created

### Primary Agent (1)
- **battleships-dev.md** - Main orchestrator for all development work
  - Mode: `primary`
  - Temperature: 0.3
  - Delegates to all 8 specialized subagents
  - Enforces TDD/BDD discipline
  - Manages task tracking and code quality

### Specialized Subagents (8)

1. **bdd-feature-writer.md**
   - Mode: `subagent`
   - Temperature: 0.3
   - Tools: read, edit, glob, grep
   - Purpose: Write Gherkin feature files

2. **css-theme-designer.md**
   - Mode: `subagent`
   - Temperature: 0.4
   - Tools: read, edit, write, glob
   - Purpose: UI/CSS design (NO JavaScript)

3. **dual-test-implementer.md**
   - Mode: `subagent`
   - Temperature: 0.2
   - Tools: read, edit, write, glob, grep, bash
   - Permissions: Allow pytest commands, ask for others
   - Purpose: Implement FastAPI + Playwright BDD tests

4. **endpoint-test-writer.md**
   - Mode: `subagent`
   - Temperature: 0.2
   - Tools: read, edit, write, glob, grep, bash
   - Permissions: Allow pytest commands, ask for others
   - Purpose: Integration tests for FastAPI endpoints

5. **fastapi-service-builder.md**
   - Mode: `subagent`
   - Temperature: 0.2
   - Tools: read, edit, grep, glob (no write/bash)
   - Purpose: Create layered FastAPI endpoints

6. **htmx-template-builder.md**
   - Mode: `subagent`
   - Temperature: 0.3
   - Tools: read, edit, write, glob
   - Purpose: HATEOAS-compliant HTMX templates

7. **tdd-workflow-guide.md**
   - Mode: `subagent`
   - Temperature: 0.1 (focused, deterministic)
   - Tools: read, edit, bash, grep, glob
   - Permissions: Allow pytest/python commands, ask for others
   - Purpose: Guide RED-GREEN-REFACTOR TDD cycles

8. **type-hint-enforcer.md**
   - Mode: `subagent`
   - Temperature: 0.1 (focused, deterministic)
   - Tools: read, edit, grep, glob (no write/bash)
   - Purpose: Ensure comprehensive type hints

## Key Changes from Claude Agents

### Structural Changes
1. **Location**: `.claude/agents/` → `.opencode/agent/`
2. **Naming**: Filename is now the agent name (no `name:` in frontmatter)
3. **Mode field**: Added `mode: subagent` or `mode: primary`
4. **Model inheritance**: Removed `model: inherit` (agents inherit from parent automatically)

### Tools Format
- **Before (Claude)**: `tools: Read, Edit, Glob, Grep`
- **After (OpenCode)**: 
  ```yaml
  tools:
    read: true
    edit: true
    glob: true
    grep: true
  ```

### Permissions Added
Granular bash permissions for agents that run commands:
```yaml
permission:
  bash:
    "uv run pytest*": allow
    "uv run python*": allow
    "*": ask
```

### Temperature Values
Added appropriate temperatures for each agent:
- **0.1**: Focused, deterministic (tdd-workflow-guide, type-hint-enforcer)
- **0.2**: Precise coding (dual-test-implementer, endpoint-test-writer, fastapi-service-builder)
- **0.3**: Balanced creativity (bdd-feature-writer, htmx-template-builder, battleships-dev)
- **0.4**: More creative (css-theme-designer)

## How to Use

### Switching Between Primary Agents
Use the **Tab** key to cycle between primary agents:
- `battleships-dev` (main development agent)
- Built-in `build` agent (if you want full manual control)
- Built-in `plan` agent (read-only analysis mode)

### Invoking Subagents
Subagents can be invoked in two ways:

1. **Automatically** - The primary agent will delegate when appropriate
2. **Manually** - Use `@agent-name` syntax:
   ```
   @bdd-feature-writer help me create a feature for ship placement
   @tdd-workflow-guide implement the delete ship feature
   @type-hint-enforcer review this file for missing type hints
   ```

## Recommended Workflow

1. **Start with primary agent** (`battleships-dev`)
2. **Let it delegate** to specialists automatically
3. **Manually invoke** specialists when you need specific expertise
4. **Before commits** - Ensure `@type-hint-enforcer` reviews your code
5. **For new features** - Let `@tdd-workflow-guide` enforce discipline

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

## Files Location

All agent files are in:
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

## Original Claude Agents

The original Claude agents remain in `.claude/agents/` for reference.
You can safely delete them once you've verified the OpenCode agents work as expected.

## Next Steps

1. ✅ Restart OpenCode to load the new agents
2. ✅ Test the primary agent (`battleships-dev`)
3. ✅ Try manually invoking subagents with `@agent-name`
4. ✅ Verify agent delegation works automatically
5. ✅ Consider removing original `.claude/agents/` files if satisfied

## Testing the Conversion

Try these commands:
```bash
# Start OpenCode
opencode

# In OpenCode TUI:
# Tab through primary agents to see battleships-dev
<Tab>

# Test manual delegation
@bdd-feature-writer can you help me understand the feature structure?

# Test automatic delegation
Help me implement a new feature to validate ship placement
```

The primary agent should automatically delegate to `@tdd-workflow-guide` for feature implementation.
