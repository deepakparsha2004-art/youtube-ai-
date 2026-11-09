@echo off
echo Activating venv and starting YouTube AI Backend...
call venv\Scripts\activate.bat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
