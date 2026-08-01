@echo off
title HireMind Service - KEEP THIS WINDOW OPEN
echo ============================================
echo   HireMind starting... KEEP THIS WINDOW OPEN
echo ============================================
echo.

wsl.exe -d Ubuntu -e bash -c "bash ~/HireMind/scripts/start_all.sh && echo '=== SERVICE STARTED, WINDOW STAYS OPEN ===' && sleep infinity"

pause
