#!/bin/bash
# Start the Python API server for database search
# This server uses compatibility mappings and IN clauses for fast, accurate searches

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv ../venv
fi

# Activate virtual environment
source ../venv/bin/activate

# Install dependencies if needed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install flask flask-cors psycopg2-binary
fi

# Set default port
PORT=${PORT:-5000}

# Load environment variables from .env if it exists
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Start the server
echo "Starting database API server on port $PORT..."
echo "API endpoints:"
echo "  POST http://localhost:$PORT/search - Search by individual parameters"
echo "  POST http://localhost:$PORT/search/normalized - Search by normalized specs object"
echo "  GET  http://localhost:$PORT/health - Health check"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python database_api.py

