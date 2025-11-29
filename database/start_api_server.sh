#!/bin/bash
# Start the Python Flask API server for database search
# This script ensures the server is running and restarts it if needed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PORT=${PORT:-6000}
LOG_FILE="${SCRIPT_DIR}/api_server.log"
PID_FILE="${SCRIPT_DIR}/api_server.pid"
PYTHON_CMD="python3"
API_SCRIPT="database_api.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if server is running
check_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            # Check if it's actually our server
            if ps -p "$PID" -o command= | grep -q "$API_SCRIPT"; then
                return 0  # Server is running
            else
                # PID file exists but process is not our server
                rm -f "$PID_FILE"
                return 1
            fi
        else
            # PID file exists but process is dead
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1  # No PID file, server not running
}

# Function to stop server
stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping API server (PID: $PID)...${NC}"
            kill "$PID"
            sleep 2
            # Force kill if still running
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
            fi
        fi
        rm -f "$PID_FILE"
        echo -e "${GREEN}Server stopped.${NC}"
    else
        echo -e "${YELLOW}No PID file found. Trying to find and kill process...${NC}"
        pkill -f "$API_SCRIPT" && echo -e "${GREEN}Server stopped.${NC}" || echo -e "${YELLOW}No server process found.${NC}"
    fi
}

# Function to start server
start_server() {
    local force_restart=${1:-false}
    
    # Check if already running
    if check_server; then
        if [ "$force_restart" = "true" ]; then
            PID=$(cat "$PID_FILE")
            echo -e "${YELLOW}Server already running (PID: $PID), restarting...${NC}"
            stop_server
            sleep 1
        else
            PID=$(cat "$PID_FILE")
            echo -e "${GREEN}API server is already running (PID: $PID)${NC}"
            echo -e "Health check: $(curl -s http://localhost:$PORT/health 2>/dev/null || echo 'not responding')"
            echo -e "${YELLOW}Use './start_api_server.sh restart' to restart, or './start_api_server.sh start --force' to force restart${NC}"
            return 0
        fi
    fi

    # Load environment variables from .env if it exists
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi

    echo -e "${YELLOW}Starting API server on port $PORT...${NC}"
    
    # Start server in background
    nohup "$PYTHON_CMD" "$API_SCRIPT" > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Save PID
    echo $SERVER_PID > "$PID_FILE"
    
    # Wait a moment and check if it started
    sleep 2
    
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API server started successfully (PID: $SERVER_PID)${NC}"
        echo -e "   Port: $PORT"
        echo -e "   Log: $LOG_FILE"
        echo -e "   PID: $PID_FILE"
        echo -e "   Health: http://localhost:$PORT/health"
        return 0
    else
        echo -e "${RED}❌ Failed to start API server${NC}"
        echo -e "   Check log file: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to restart server
restart_server() {
    echo -e "${YELLOW}Restarting API server...${NC}"
    stop_server
    sleep 1
    start_server
}

# Function to show status
show_status() {
    if check_server; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ API server is running${NC}"
        echo -e "   PID: $PID"
        echo -e "   Port: $PORT"
        echo -e "   Log: $LOG_FILE"
        
        # Test health endpoint
        HEALTH=$(curl -s http://localhost:$PORT/health 2>/dev/null)
        if [ -n "$HEALTH" ]; then
            echo -e "   Health: $HEALTH"
        else
            echo -e "   ${YELLOW}Health: Not responding${NC}"
        fi
    else
        echo -e "${RED}❌ API server is not running${NC}"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}Log file not found: $LOG_FILE${NC}"
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        if [ "${2}" = "--force" ]; then
            start_server true
        else
            start_server false
        fi
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start [--force]  - Start the API server (use --force to restart if already running)"
        echo "  stop             - Stop the API server"
        echo "  restart          - Stop and restart the API server"
        echo "  status           - Show server status"
        echo "  logs             - Show and follow log file"
        exit 1
        ;;
esac
