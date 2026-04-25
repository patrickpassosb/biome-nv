#!/bin/bash

# Start Biome Local Servers
echo "🚀 Starting Biome servers..."

# Start backend
cd backend
uv run python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 2

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Servers running!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:5177"
echo ""
echo "🌐 Now run a tunnel command to share with judges:"
echo "   ngrok http 5177"
echo "   or"
echo "   npx localtunnel --port 5177"
echo ""
echo "Press Ctrl+C to stop servers"

# Keep script running
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
