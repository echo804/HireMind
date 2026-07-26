#!/bin/bash
cd ~/HireMind
sudo service postgresql start 2>/dev/null
redis-cli ping 2>/dev/null || sudo service redis-server start
source .venv/bin/activate
pkill -f "uvicorn app.main" 2>/dev/null
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/hiremind_backend.log 2>&1 &
echo "Backend PID: $!"
cd frontend
pkill -f "node.*v¹te" 2>/dev/null
nohup ./node_modules/.bin/vite --host 0.0.0.0 --port 5173 > /tmp/vite_wsl.log 2>&1 &
echo "Frontend PID: $!"
cd ..
echo "Done"