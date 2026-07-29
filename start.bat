@echo off
echo === HireMind 一键启动 ===
echo.
wsl bash ~/HireMind/scripts/start_all.sh
echo.
echo 正在用 Chrome 打开页面...
start chrome http://localhost:5173
