@echo off
REM Скрипт запуска локального RAG-ассистента

echo Активация виртуального окружения...
call ..\venv\Scripts\activate.bat

echo Запуск ассистента...
python app\main.py

pause
