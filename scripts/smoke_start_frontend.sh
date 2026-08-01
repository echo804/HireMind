#!/bin/bash
# 冒烟测试：启动前端 dev server（WSL）
cd ~/HireMind/frontend || exit 1
pkill -f "vite" 2>/dev/null
sleep 1
setsid bash -c './node_modules/.bin/vite --host 0.0.0.0 --port 5173 > /tmp/hm_smoke_frontend.log 2>&1' &
sleep 4
code=$(curl -s -m 5 -o /dev/null -w "%{http_code}" http://localhost:5173 || echo 000)
echo "frontend: $code"
tail -3 /tmp/hm_smoke_frontend.log
