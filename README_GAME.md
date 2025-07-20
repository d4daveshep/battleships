# Fox The Navy - Terminal Game Instructions

## How to Play

### Starting the Game
```bash
# Run the game
uv run python play.py
# or
python play.py
```

### Game Setup
1. **Enter your name** when prompted
2. **Choose opponent**: Computer or another human player
3. **Place your ships**: Follow the prompts to place all 5 ships
   - Enter coordinates like `A1`, `B5`, `J10`
   - Choose direction: `h` (horizontal), `v` (vertical), `ne` (northeast diagonal), `se` (southeast diagonal)
   - Ships cannot touch each other (spacing rule)

### Ship Types
- **Carrier** (5 squares, 2 shots): The largest ship
- **Battleship** (4 squares, 1 shot): Heavy firepower
- **Cruiser** (3 squares, 1 shot): Fast and agile
- **Submarine** (3 squares, 1 shot): Stealth vessel
- **Destroyer** (2 squares, 1 shot): The smallest ship

### Playing the Game
1. **Each round** both players fire shots simultaneously
2. **Available shots** = Total shots from all your remaining (unsunk) ships
3. **Target selection**: Enter coordinates separated by spaces (e.g., `A1 B2 C3`)
4. **Hit feedback**: See what ships you hit after each round
5. **Win condition**: Sink all enemy ships first

### Game Display
- 🚢 = Your ships (green = afloat, red = sunk)
- 💥 = Hits (yellow = hit, red = sunk)
- 💧 = Misses
- ~ = Empty water

### Controls
- **Coordinates**: Use A-J for rows, 1-10 for columns
- **Directions**: h/horizontal, v/vertical, ne/northeast, se/southeast
- **Multiple shots**: Separate with spaces (A1 B2 C3)
- **Ctrl+C**: Exit game anytime

### Tips
- Remember the spacing rule: ships cannot touch
- Diagonal placement can be strategic
- Track your hits to deduce enemy ship positions
- The number of shots you have depends on your remaining fleet

## Game Rules Summary

From the original game rules:
- 10x10 grid with A-J rows and 1-10 columns
- Ships can be placed horizontally, vertically, or diagonally
- Ships cannot overlap or touch each other
- Each ship type has a specific length and shot capacity
- Game is played in rounds with simultaneous shooting
- First to sink all opponent ships wins
- If both players sink each other's last ships in the same round, it's a draw

## Troubleshooting

**Game won't start?**
- Make sure you have all dependencies: `uv sync`
- Try: `uv run python play.py`

**Display issues?**
- Ensure your terminal supports Unicode characters
- Try resizing your terminal window

**Input not working?**
- Use exact format: A1, B2, etc.
- Separate multiple coordinates with spaces
- Check for typos in coordinates

Enjoy playing Fox The Navy! 🚢