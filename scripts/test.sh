#!/bin/bash
# Comprehensive testing script for Fox The Navy

set -e

echo "🧪 Running Fox The Navy Test Suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    print_status $YELLOW "📦 Installing dependencies..."
    uv sync --dev
fi

# Install Playwright browsers if needed for component tests
if [ ! -d "ms-playwright" ] && [[ "$*" == *"--component"* ]]; then
    print_status $YELLOW "🎭 Installing Playwright browsers..."
    uv run playwright install chromium
fi

# Parse command line arguments
RUN_UNIT=true
RUN_WEB_API=false
RUN_COMPONENT=false
RUN_INTEGRATION=false
RUN_ALL=false
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --web-api)
            RUN_WEB_API=true
            RUN_UNIT=false
            shift
            ;;
        --component)
            RUN_COMPONENT=true
            RUN_UNIT=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_UNIT=false
            shift
            ;;
        --all)
            RUN_ALL=true
            RUN_UNIT=false
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--web-api] [--component] [--integration] [--all] [--coverage]"
            exit 1
            ;;
    esac
done

# Test commands
PYTEST_CMD="uv run pytest"
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="uv run pytest --cov=game --cov=web --cov-report=html --cov-report=term"
fi

# Run tests based on arguments
if [ "$RUN_ALL" = true ]; then
    print_status $YELLOW "🎯 Running all tests..."
    
    print_status $YELLOW "1️⃣  Core game logic tests..."
    $PYTEST_CMD tests/test_models.py tests/test_board.py tests/test_player.py tests/test_game_state.py tests/test_computer_player.py -v
    
    print_status $YELLOW "2️⃣  Web API tests..."
    $PYTEST_CMD tests/test_web_api.py -v
    
    print_status $YELLOW "3️⃣  Integration tests..."
    $PYTEST_CMD tests/test_integration.py -v
    
    if command -v playwright &> /dev/null; then
        print_status $YELLOW "4️⃣  Component tests..."
        $PYTEST_CMD tests/test_web_components.py -v -s
    else
        print_status $YELLOW "⚠️  Skipping component tests (Playwright not available)"
    fi
    
elif [ "$RUN_UNIT" = true ]; then
    print_status $YELLOW "🎯 Running unit tests (core game logic)..."
    $PYTEST_CMD tests/test_models.py tests/test_board.py tests/test_player.py tests/test_game_state.py tests/test_computer_player.py -v
    
elif [ "$RUN_WEB_API" = true ]; then
    print_status $YELLOW "🎯 Running web API tests..."
    $PYTEST_CMD tests/test_web_api.py -v
    
elif [ "$RUN_COMPONENT" = true ]; then
    print_status $YELLOW "🎯 Running component tests..."
    if command -v playwright &> /dev/null; then
        $PYTEST_CMD tests/test_web_components.py -v -s
    else
        print_status $RED "❌ Playwright not available. Install with: uv run playwright install"
        exit 1
    fi
    
elif [ "$RUN_INTEGRATION" = true ]; then
    print_status $YELLOW "🎯 Running integration tests..."
    $PYTEST_CMD tests/test_integration.py -v
fi

# Check test results
if [ $? -eq 0 ]; then
    print_status $GREEN "✅ All tests passed!"
    
    if [ "$COVERAGE" = true ]; then
        print_status $GREEN "📊 Coverage report generated in htmlcov/index.html"
    fi
else
    print_status $RED "❌ Some tests failed!"
    exit 1
fi

# Optional: Run linting
if command -v ruff &> /dev/null; then
    print_status $YELLOW "🔍 Running linting..."
    uv run ruff check game web
    if [ $? -eq 0 ]; then
        print_status $GREEN "✅ Code style checks passed!"
    else
        print_status $YELLOW "⚠️  Code style issues found (not blocking)"
    fi
fi

print_status $GREEN "🎉 Test suite complete!"