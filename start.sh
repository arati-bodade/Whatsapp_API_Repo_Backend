#!/bin/bash
set -e

echo "🚀 Starting WhatsApp Platform Backend..."

# Set default port if not set
export PORT=${PORT:-10000}

# Run the application
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
