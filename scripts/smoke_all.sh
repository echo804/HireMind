#!/bin/bash
# 端到端冒烟：启动后端+前端 -> 运行冒烟脚本 -> 清理进程（单次 WSL 调用内完成）
set -u
cd ~/HireMind || exit 1

echo "===== [1/3] 启动后端 ====="
bash scripts/smoke_start_backend.sh

echo "===== [2/3] 启动前端 ====="
bash scripts/smoke_start_frontend.sh

echo "===== [3/3] 运行冒烟测试 ====="
.venv/bin/python3 scripts/smoke_test.py
rc=$?

echo "===== 清理进程 ====="
pkill -f uvicorn 2>/dev/null
pkill -f vite 2>/dev/null
# 保存日志（WSL VM 关闭会清空 /tmp）
cp /tmp/hm_smoke_backend.log ~/HireMind/smoke_backend.log 2>/dev/null
cp /tmp/hm_smoke_frontend.log ~/HireMind/smoke_frontend.log 2>/dev/null
exit $rc
