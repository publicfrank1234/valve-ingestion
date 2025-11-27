#!/bin/bash
# Alternative: Run in background using screen (keeps running after disconnect)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    echo "Installing screen..."
    sudo apt-get update && sudo apt-get install -y screen
fi

# Load .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting batch processor in screen session..."
echo "You can detach with: Ctrl+A then D"
echo "Reattach with: screen -r valve-crawl"
echo ""

screen -S valve-crawl -dm bash -c "cd $PROJECT_DIR && source venv/bin/activate && python3 extraction/batch_processor.py product_urls.json --yes; exec bash"

echo "✓ Started in screen session 'valve-crawl'"
echo ""
echo "Commands:"
echo "  screen -r valve-crawl    # Reattach to see output"
echo "  screen -ls               # List all screen sessions"
echo "  screen -S valve-crawl -X quit  # Stop the session"

