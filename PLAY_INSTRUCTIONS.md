# 🚢 Fox The Navy - Ready to Play!

## Quick Start

```bash
# Start playing immediately
uv run python play.py
```

## What You Get

### ✅ Complete TUI (Terminal User Interface)
- Beautiful Rich-based interface with colors and emojis
- Interactive ship placement with visual feedback
- Dual-board display (your ships + shots fired)
- Real-time game status and fleet information
- Round-by-round results display

### ✅ Computer Player
- Intelligent random ship placement following all game rules
- Computer opponent with random shot selection
- Automatic setup - computer places its own ships

### ✅ Full Game Implementation
- All 5 ship types with correct properties
- Diagonal ship placement support
- Proper spacing rules (ships cannot touch)
- Round-based simultaneous gameplay
- Dynamic shot allocation based on remaining fleet
- Win/lose/draw detection
- Game state persistence

## Game Features

### Ship Types & Shot Capacity
- **Carrier** (5 squares, 2 shots) 🚢🚢🚢🚢🚢
- **Battleship** (4 squares, 1 shot) 🚢🚢🚢🚢
- **Cruiser** (3 squares, 1 shot) 🚢🚢🚢
- **Submarine** (3 squares, 1 shot) 🚢🚢🚢
- **Destroyer** (2 squares, 1 shot) 🚢🚢

### Visual Elements
- 🚢 = Ships (green=afloat, red=sunk)
- 💥 = Hits (yellow=hit, red=sunk ship)
- 💧 = Misses
- ~ = Empty water
- ⭐ = Position preview during placement

### Controls
- **Coordinates**: A1, B5, J10, etc.
- **Directions**: h/horizontal, v/vertical, ne/northeast, se/southeast
- **Multiple shots**: Space-separated (A1 B2 C3)

## Testing

```bash
# Run all tests (113 tests)
uv run pytest

# View demo interface
uv run python demo.py

# Test individual components
uv run python test_tui.py
```

## Architecture

- **Core Game Logic**: Fully tested business logic
- **Computer Player**: AI with random placement and shooting
- **TUI Interface**: Rich-based terminal interface
- **Input Handling**: Robust coordinate and command parsing
- **Display System**: Beautiful game board visualization

## Ready to Battle!

The game is complete and ready for you to test against the computer player. The implementation follows all the original game rules from `Game_Rules.md` and provides an engaging terminal experience.

Have fun sinking ships! ⚓