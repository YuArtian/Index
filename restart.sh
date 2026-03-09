#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_PORT=8000
WEB_PORT=5173

kill_port() {
  local port=$1
  local name=$2
  local pids=$(lsof -ti:"$port" 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "[$name] Killing processes on port $port (PIDs: $pids)"
    echo "$pids" | xargs kill -9
    sleep 1
  else
    echo "[$name] No existing process on port $port"
  fi
}

# Kill existing services
kill_port $API_PORT "API"
kill_port $WEB_PORT "Web"

# Start API
echo "[API] Starting on port $API_PORT..."
cd "$PROJECT_DIR/apps/api" && source .venv/bin/activate && python main.py &
API_PID=$!

# Start Web
echo "[Web] Starting on port $WEB_PORT..."
cd "$PROJECT_DIR/apps/web" && pnpm dev &
WEB_PID=$!

echo ""
echo "Services started:"
echo "  API: http://localhost:$API_PORT (PID: $API_PID)"
echo "  Web: http://localhost:$WEB_PORT (PID: $WEB_PID)"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to kill both
trap "echo ''; echo 'Stopping services...'; kill $API_PID $WEB_PID 2>/dev/null; exit 0" INT TERM

# Wait for both
wait
