#!/bin/bash
# Development script for Fox The Navy

set -e

echo "🚢 Starting Fox The Navy Development Server..."

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    uv sync --dev
fi

# Install Playwright browsers if needed
if [ ! -d "ms-playwright" ]; then
    echo "🎭 Installing Playwright browsers..."
    uv run playwright install
fi

# Run tests first
echo "🧪 Running tests..."
uv run pytest tests/test_models.py tests/test_board.py tests/test_player.py tests/test_game_state.py -v

# Start development server with auto-reload
echo "🚀 Starting development server..."
echo "🌐 Server will be available at http://localhost:8000"
echo "💡 Use Ctrl+C to stop the server"

uv run python web_server.py --reload --log-level debug