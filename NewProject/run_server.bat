@echo off
rem Change directory to the script's location
cd /d "%~dp0"
set PYTHONPATH=.
..\.venv\Scripts\python.exe -m uvicorn simple_app:app --reload --host 127.0.0.1 --port 8000