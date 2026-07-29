#!/bin/bash
set -e
cd ~/HireMind

echo "=== HireMind 一键启动 ==="

# 1. PostgreSQL（已运行就跳过，避免 sudo 卡住）
if systemctl is-active --quiet postgresql 2>/dev/null; then
  echo "[OK] PostgreSQL 已在运行"
else
  echo 23031171 | sudo -S service postgresql start 2>/dev/null && echo "[OK] PostgreSQL 已启动"
fi

# 2. Redis
if systemctl is-active --quiet redis-server 2>/dev/null; then
  echo "[OK] Redis 已在运行"
else
  echo 23031171 | sudo -S service redis-server start 2>/dev/null && echo "[OK] Redis 已启动"
fi

# 3. 激活 venv
source .venv/bin/activate

# 4. 后端
pkill -f "uvicorn app.main" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/hiremind_backend.log 2>&1 &
echo "[OK] 后端已启动 (PID: $!)"
sleep 2

# 5. 前端
cd frontend
pkill -f "node.*vite" 2>/dev/null || true
setsid bash -c './node_modules/.bin/vite --host 0.0.0.0 --port 5173 &>/tmp/vite.log &' &
sleep 3
echo "[OK] 前端已启动"

# 6. 验证
echo ""
echo "--- 访问地址 ---"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000/docs"
echo ""

# 检查是否真的在监听
curl -s -o /dev/null -w "  后端状态: %{http_code}\n" http://localhost:8000/docs 2>/dev/null || echo "  后端状态: 启动中..."
curl -s -o /dev/null -w "  前端状态: %{http_code}\n" http://localhost:5173 2>/dev/null || echo "  前端状态: 启动中..."

echo ""
echo "=== 完成 ==="
