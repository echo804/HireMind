#!/bin/bash
echo 'Stopping services...'
pkill -f uvicorn 2>/dev/null && echo '  Backend stopped' || echo '  Backend not running'
pkill -f vite 2>/dev/null && echo '  Frontend stopped' || echo '  Frontend not running'
echo 'Done'