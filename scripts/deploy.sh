#!/bin/bash
# Deployment script for Fox The Navy

set -e

echo "🚢 Deploying Fox The Navy Web Application..."

# Build Docker image
echo "📦 Building Docker image..."
docker build -t fox-the-navy .

# Run tests
echo "🧪 Running tests..."
docker run --rm -v $(pwd):/app fox-the-navy uv run pytest -v

# Deploy with docker-compose
echo "🚀 Starting services..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for application to be ready..."
timeout 60s bash -c 'until curl -f http://localhost:8000/ > /dev/null 2>&1; do sleep 2; done'

echo "✅ Deployment complete!"
echo "🌐 Application is running at http://localhost:8000"

# Show status
docker-compose ps