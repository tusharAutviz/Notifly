#!/bin/bash
# Get PORT from environment or use 10000 as fallback
PORT="${PORT:-10000}"

# Start the application using the PORT environment variable
uvicorn app.main:app --host 0.0.0.0 --port $PORT