@echo off
cd C:\Users\DY15D\OneDrive\Desktop\NewProject\NewProject
set PYTHONPATH=C:\Users\DY15D\OneDrive\Desktop\NewProject\NewProject
C:\Users\DY15D\OneDrive\Desktop\NewProject\.venv\Scripts\python.exe -m uvicorn simple_app:app --reload --host 127.0.0.1 --port 8000