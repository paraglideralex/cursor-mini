@echo off
REM Запуск ML Service из корня CodeLens
cd /d "%~dp0..\.."
python services\ml-service\run.py
