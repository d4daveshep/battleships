#!/bin/bash
set -e

echo "Starting test environment..."

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up test environment..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Start server
echo "Starting FastAPI server..."
uv run uvicorn main:app --port 8000 --host 127.0.0.1 &
SERVER_PID=$!

# Wait for server with health check
echo "Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Server ready after ${i} seconds"
        break
    fi
    sleep 1
done

if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Server failed to start"
    exit 1
fi

# Run tests
echo "Running tests..."
uv run pytest tests/ -v --tb=short

echo "Test run complete."