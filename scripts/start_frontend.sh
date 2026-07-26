#!/bin/bash
setsid bash -c "cd /mnt/d/codexproject/codexproject/HireMind/frontend && ./node_modules/.bin/vite --host 0.0.0.0 --port 5173 &>/tmp/vite.log &"
echo "Frontend started"