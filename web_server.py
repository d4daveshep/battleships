#!/usr/bin/env python3
"""
Web server entry point for Fox The Navy game.
"""

import uvicorn
import argparse
import os
from pathlib import Path


def main():
    """Main entry point for web server"""
    parser = argparse.ArgumentParser(description="Fox The Navy Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    # Ensure we're running from the correct directory
    if not Path("web").exists():
        print("Error: web directory not found. Please run from project root.")
        exit(1)
    
    # Configure uvicorn
    config = {
        "app": "web.app:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
    }
    
    # Development vs Production settings
    if args.reload:
        config["reload"] = True
        config["reload_dirs"] = ["web", "game"]
        print("🚀 Starting development server with auto-reload...")
    else:
        config["workers"] = args.workers
        print(f"🚀 Starting production server with {args.workers} workers...")
    
    print(f"🌐 Server will be available at: http://{args.host}:{args.port}")
    print("🚢 Ready to play Fox The Navy!")
    
    # Start the server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()