# Fox The Navy - Naval Battle Game

A complete implementation of the naval battle game "Fox The Navy" with both terminal (TUI) and web interfaces.

## Overview

The point of this repo is to practice generating the code for a known game, in this case a version of Battleships, from a specification of the game rules, the interface, software architecture and deployment model.

This implementation features:
- **Terminal User Interface (TUI)** - Rich-based interactive terminal game
- **Web Interface** - FastAPI + HTML + HTMX browser-based game
- **Complete Game Logic** - Diagonal ship placement, spacing rules, simultaneous rounds
- **Computer AI** - Random ship placement and shooting strategies  
- **Comprehensive Testing** - Unit, integration, and component tests
- **Docker Deployment** - Containerized for easy deployment

## Game Documentation

- [Game Rules](Game_Rules.md) - Complete Fox The Navy rules and mechanics
- [Code Architecture](Code_Architecture.md) - Technical architecture and design decisions
- [Game Instructions](README_GAME.md) - How to play the terminal version

## Quick Start

### Web Interface (Recommended)

Start the web server for browser-based gameplay:

```bash
# Development mode with auto-reload
./scripts/dev.sh

# Or manually
uv run python web_server.py --reload
```

Then open http://localhost:8000 in your browser.

### Terminal Interface

For command-line gameplay:

```bash
uv run python play.py
```

### Run Tests

```bash
# All tests
./scripts/test.sh --all --coverage

# Just unit tests
./scripts/test.sh

# Web API tests
./scripts/test.sh --web-api

# Component tests (requires Playwright)
./scripts/test.sh --component

# Integration tests  
./scripts/test.sh --integration
```

## Web Interface Features

The web interface provides a modern, interactive gaming experience:

### Game Creation
- **Player vs Computer** - Battle against AI with random strategies
- **Player vs Player** - Local multiplayer on same device
- **Session-based** - Games persist across browser refreshes

### Ship Placement
- **Manual Placement** - Click and place each ship individually
  - Choose row (A-J) and column (1-10)
  - Select direction: Horizontal, Vertical, Diagonal NE, Diagonal SE
  - Real-time validation of placement rules
- **Auto-Placement** - Let the computer randomly place all ships
- **Visual Feedback** - See ships on the board as you place them

### Battle Phase
- **Dual Board View** - See your ships and track your shots side-by-side
- **Shot Input** - Enter coordinates like "A1,B2,C3" for multiple shots
- **Real-time Updates** - Boards update automatically via HTMX
- **Round Results** - Detailed feedback on hits, misses, and sunk ships
- **Color Coding** - Easy visual distinction between different cell states

### Game End
- **Winner Announcement** - Clear victory or draw declaration
- **Final Board Reveal** - See both players' complete ship positions
- **New Game** - Easily start another match

### Technical Features
- **Responsive Design** - Works on desktop and mobile devices
- **No JavaScript Framework** - Uses HTMX for interactivity
- **Session Management** - Secure server-side game state
- **Error Handling** - Graceful handling of invalid inputs
- **Auto-refresh** - Game state updates automatically

## Deployment

### Development
```bash
# Start development server
./scripts/dev.sh
```

### Docker
```bash
# Build and deploy with Docker Compose
./scripts/deploy.sh

# Or manually
docker-compose up -d
```

### Production
```bash
# Production server with multiple workers
uv run python web_server.py --workers 4

# Or with Docker
docker build -t fox-the-navy .
docker run -p 8000:8000 fox-the-navy
```

## Architecture

### Core Game Engine
- **Pure Python Logic** - Game rules implemented in `game/` package
- **Dataclass Models** - Type-safe ship, coordinate, and game state models
- **Validation Engine** - Comprehensive ship placement and move validation
- **AI System** - Pluggable computer player strategies

### Web Interface
- **FastAPI Backend** - Modern async Python web framework
- **HTMX Frontend** - Dynamic HTML without complex JavaScript
- **Jinja2 Templates** - Server-side rendered HTML components
- **Session Storage** - In-memory game state (Redis-ready for scaling)

### Testing Strategy
- **Unit Tests** - Core game logic with 98%+ coverage
- **Integration Tests** - Complete game flow testing
- **Component Tests** - Browser automation with Playwright
- **API Tests** - FastAPI endpoint testing with TestClient

## Game Rules Summary

Fox The Navy follows unique rules that distinguish it from standard Battleships:

### Ship Fleet
- **Carrier** (5 squares, 2 shots)
- **Battleship** (4 squares, 1 shot)  
- **Cruiser** (3 squares, 1 shot)
- **Submarine** (3 squares, 1 shot)
- **Destroyer** (2 squares, 1 shot)

### Unique Features
- **Diagonal Placement** - Ships can be placed diagonally (NE/SE)
- **Spacing Rules** - Ships cannot touch each other (not even diagonally)
- **Dynamic Shots** - Number of shots per round equals shots from remaining ships
- **Simultaneous Rounds** - Both players shoot simultaneously each round
- **Draw Conditions** - Game can end in a draw if both players eliminated simultaneously

### Victory Conditions
- **Standard Win** - Sink all opponent ships first
- **Draw** - Both players lose their last ships in the same round

## Development

### Project Structure
```
battleships/
├── game/                 # Core game logic
│   ├── models.py        # Data models
│   ├── board.py         # Game board
│   ├── player.py        # Player management  
│   ├── game_state.py    # Game flow control
│   └── computer_player.py # AI strategies
├── web/                 # Web interface
│   ├── app.py          # FastAPI application
│   ├── templates/      # HTML templates
│   └── static/         # CSS/JS assets
├── tui/                # Terminal interface
│   ├── display.py      # Rich-based display
│   ├── input_handler.py # Input parsing
│   └── game_controller.py # Game flow
├── tests/              # Test suite
├── scripts/            # Development scripts
└── docs/               # Documentation
```

### Adding Features
1. **Game Logic** - Extend classes in `game/` package
2. **Web Interface** - Add endpoints to `web/app.py` and templates
3. **Terminal Interface** - Modify `tui/` components
4. **Tests** - Add corresponding tests for new features

### Code Style
- **Type Hints** - All functions use type annotations
- **Dataclasses** - Immutable data structures where appropriate
- **Error Handling** - Comprehensive validation and error reporting
- **Documentation** - Docstrings for all public methods

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `./scripts/test.sh --all`
5. Submit a pull request

## License

This project is provided as-is for educational and demonstration purposes.

