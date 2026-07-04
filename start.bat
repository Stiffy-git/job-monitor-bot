@echo off
REM ============================================
REM Job Monitor Bot — Запуск (Windows)
REM ============================================

cd /d "%~dp0"

echo.
echo 🚀 Запуск Job Monitor Bot...
echo    Для остановки: Ctrl+C
echo.

python main.py
pause
