#!/bin/bash

echo "Starting FastAPI development server..."
echo "Open http://localhost:8000 in your browser"
echo "Press Ctrl+C to stop the server"

uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

