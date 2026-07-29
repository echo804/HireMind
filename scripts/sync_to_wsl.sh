#!/bin/bash
# 一键同步 Windows 侧代码到 WSL ~/HireMind
cp -r /mnt/d/codexproject/codexproject/HireMind/app/* ~/HireMind/app/
cp -r /mnt/d/codexproject/codexproject/HireMind/frontend/src/* ~/HireMind/frontend/src/
cp /mnt/d/codexproject/codexproject/HireMind/pyproject.toml ~/HireMind/
echo "Synced. Touching to trigger reload..."
touch ~/HireMind/app/main.py
echo "Done"
