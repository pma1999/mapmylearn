@echo off
cd backend
python -m uvicorn api:app --reload --port 8000