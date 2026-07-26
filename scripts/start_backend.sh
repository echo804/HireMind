#!/bin/bash
setsid bash -c "cd /mnt/d/codexproject/codexproject/HireMind && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &>/tmp/hiremind.log &"
echo "Backend started"