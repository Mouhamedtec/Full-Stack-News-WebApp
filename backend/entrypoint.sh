#!/bin/bash
set -e

# Start the application
echo "Starting uvicorn..."
exec uvicorn base.asgi:application \
    --host 0.0.0.0 \
    --port 8282 \
    --workers 4 \
    --log-level info \
    --timeout-keep-alive 5 \
    --reload \
    --proxy-headers