@echo off
cd /d "%~dp0"
start "" http://127.0.0.1:8000/manual-queue
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
