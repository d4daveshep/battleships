#!/bin/bash

echo "Starting FastAPI server..."
uv run uvicorn main:app --port 8000 &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 2

echo "Running BDD tests..."
uv run pytest tests/ -v

echo "Stopping FastAPI server..."
kill $SERVER_PID

echo "Test run complete."