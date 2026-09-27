@echo off
start "Smart Taka - Backend" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate && uvicorn app.main:app --reload"
start "Smart Taka - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
