# OpenCode Agents for Battleships

This directory contains the OpenCode agent configuration for the Battleships project.

## Contents

### Agent Files

**Primary Agent:**
- `agent/battleships-dev.md` - Main development orchestrator

**Subagents:**
- `agent/bdd-feature-writer.md` - Gherkin feature file writer
- `agent/css-theme-designer.md` - CSS theming specialist
- `agent/dual-test-implementer.md` - BDD test implementer (FastAPI + Playwright)
- `agent/endpoint-test-writer.md` - FastAPI integration test writer
- `agent/fastapi-service-builder.md` - Layered endpoint/service builder
- `agent/htmx-template-builder.md` - HATEOAS HTMX template builder
- `agent/tdd-workflow-guide.md` - TDD cycle coach
- `agent/type-hint-enforcer.md` - Type hint quality enforcer

### Documentation

- `HOW_TO_USE_AGENTS.md` - Comprehensive usage guide
- `QUICK_REFERENCE.md` - Quick reference card
- `AGENT_CONVERSION.md` - Conversion details from Claude agents
- `README.md` - This file

## Quick Start

1. Start OpenCode in the project directory:
   ```bash
   opencode
   ```

2. Press **Tab** to switch to the `battleships-dev` primary agent

3. Start working:
   ```
   Help me implement a feature to validate ship placement
   ```

## Documentation

- **New to these agents?** Start with `HOW_TO_USE_AGENTS.md`
- **Need quick lookup?** See `QUICK_REFERENCE.md`
- **Want conversion details?** Check `AGENT_CONVERSION.md`

## Agent Philosophy

This project uses a **primary agent + specialist subagents** architecture:

- **battleships-dev** (primary) orchestrates everything
- **8 specialist subagents** handle specific domains
- **Automatic delegation** based on task type
- **Manual invocation** available via `@agent-name`

## Key Features

✅ **TDD/BDD Discipline** - Enforced through workflow
✅ **Type Hint Quality** - Comprehensive coverage required
✅ **No JavaScript** - HTMX-only frontend (strict)
✅ **Granular Permissions** - Safe bash command execution
✅ **Temperature Optimization** - Tuned per agent (0.1-0.4)

## Support

Questions? Just ask the primary agent:
```
How do I [task]?
Which agent should I use for [topic]?
```

The `battleships-dev` agent is designed to help you navigate the system.
