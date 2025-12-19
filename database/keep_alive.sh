#!/bin/bash
# Keep API server alive - monitors and restarts if it crashes
# Run this script in the background or as a service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CHECK_INTERVAL=30  # Check every 30 seconds
LOG_FILE="${SCRIPT_DIR}/keep_alive.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "${GREEN}Starting keep-alive monitor for API server...${NC}"

while true; do
    # Check if server is running
    if ! "$SCRIPT_DIR/start_api_server.sh" status > /dev/null 2>&1; then
        log "${YELLOW}Server not running, restarting...${NC}"
        "$SCRIPT_DIR/start_api_server.sh" start
    fi
    
    sleep $CHECK_INTERVAL
done









