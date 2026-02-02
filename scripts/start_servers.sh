#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root directory (parent of scripts)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Function to prefix output lines
prefix_output() {
    local prefix=$1
    local color=$2
    while IFS= read -r line; do
        echo -e "${color}[${prefix}]${NC} $line"
    done
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check if servers are already running
echo -e "${YELLOW}Checking if servers are already running...${NC}"
if check_port 3000; then
    echo -e "${RED}Error: Frontend server is already running on port 3000${NC}"
    exit 1
fi

if check_port 8000; then
    echo -e "${RED}Error: Backend server is already running on port 8000${NC}"
    exit 1
fi

echo -e "${GREEN}Ports 3000 and 8000 are free${NC}"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: UV is not installed. Please install it first:${NC}"
    echo -e "${YELLOW}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

# Check and install backend dependencies with UV
echo -e "${YELLOW}Checking backend dependencies...${NC}"
cd "$BACKEND_DIR"

# Sync dependencies with UV from pyproject.toml
echo -e "${YELLOW}Syncing backend dependencies with UV...${NC}"
uv sync

# Check and install frontend dependencies
echo -e "${YELLOW}Checking frontend dependencies...${NC}"
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
else
    echo -e "${GREEN}Frontend dependencies are installed${NC}"
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    # Kill process groups to ensure all child processes are terminated
    if [ ! -z "$BACKEND_PID" ]; then
        kill -TERM -$BACKEND_PID 2>/dev/null
        echo -e "${GREEN}Backend server stopped${NC}"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill -TERM -$FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}Frontend server stopped${NC}"
    fi
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Starting One Night Werewolf Servers${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Start backend server with UV
cd "$BACKEND_DIR"
(uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1 | prefix_output "BACKEND" "$CYAN") &
BACKEND_PID=$!

# Start frontend server
cd "$FRONTEND_DIR"
(npm run dev 2>&1 | prefix_output "FRONTEND" "$BLUE") &
FRONTEND_PID=$!

# Wait for both processes
wait

