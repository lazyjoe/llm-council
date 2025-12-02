#!/bin/bash

# Stop running app
lsof -ti:8001 | xargs -r kill -9 2>/dev/null
lsof -ti:5173 | xargs -r kill -9 2>/dev/null

# LLM Council - Start script

echo "Starting LLM Council..."
echo ""

# Create logs directory
mkdir -p logs

# Start backend with logging
echo "Starting backend on http://localhost:8001..."
echo "Backend logs: logs/backend.log"
uv run python -m backend.main > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start! Check logs/backend.log for details"
    tail -20 logs/backend.log
    exit 1
fi

# Start frontend with logging
echo "Starting frontend on http://localhost:5173..."
echo "Frontend logs: logs/frontend.log"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✓ LLM Council is running!"
echo "  Backend:  http://localhost:8001"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers"

# Monitor processes and restart if they crash
monitor_processes() {
    while true; do
        sleep 5

        # Check backend
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo ""
            echo "⚠️  Backend process crashed! Last 20 lines of log:"
            tail -20 logs/backend.log
            echo ""
            echo "Restarting backend..."
            uv run python -m backend.main > logs/backend.log 2>&1 &
            BACKEND_PID=$!
            sleep 2
            if kill -0 $BACKEND_PID 2>/dev/null; then
                echo "✓ Backend restarted successfully"
            else
                echo "❌ Backend failed to restart"
            fi
        fi

        # Check frontend
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            echo ""
            echo "⚠️  Frontend process crashed! Last 20 lines of log:"
            tail -20 logs/frontend.log
            echo ""
            echo "Restarting frontend..."
            cd frontend
            npm run dev > ../logs/frontend.log 2>&1 &
            FRONTEND_PID=$!
            cd ..
            sleep 2
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                echo "✓ Frontend restarted successfully"
            else
                echo "❌ Frontend failed to restart"
            fi
        fi
    done
}

# Start monitoring in background
monitor_processes &
MONITOR_PID=$!

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID $MONITOR_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
