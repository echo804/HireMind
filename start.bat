@echo off
echo === HireMind 一键启动 ===
echo.
wsl bash ~/HireMind/scripts/start_all.sh
echo.
echo 按任意键打开前端页面...
pause >nul
start http://localhost:5173
