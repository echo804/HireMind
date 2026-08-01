#!/bin/bash
# 冒烟测试：启动后端（真实代码 + hiremind_test 库 + 真实 AI 配置）
cd ~/HireMind || exit 1
pkill -f "uvicorn" 2>/dev/null
sleep 1
POSTGRES_DB=hiremind_test setsid .venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/hm_smoke_backend.log 2>&1 &
sleep 5
code=$(curl -s -m 5 -o /dev/null -w "%{http_code}" http://localhost:8000/api/health || echo 000)
echo "backend health: $code"
tail -3 /tmp/hm_smoke_backend.log
