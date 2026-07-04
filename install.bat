@echo off
REM ============================================
REM Job Monitor Bot — Установка (Windows)
REM ============================================

echo.
echo 🔧 Установка Job Monitor Bot...
echo.

REM Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден.
    echo Скачайте с https://www.python.org/downloads/
    echo Не забудьте поставить галочку "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Установка зависимостей
echo 📦 Установка зависимостей...
python -m pip install -r requirements.txt --quiet

echo.
echo 🌐 Установка Playwright...
python -m playwright install chromium

echo.
echo ✅ Установка завершена!
echo.
echo 📋 Следующие шаги:
echo    1. Отредактируйте config.yaml (вставьте bot_token и channel_id)
echo    2. Запустите: python main.py
echo.
echo 💡 Для автозапуска скопируйте start.bat в папку автозагрузки:
echo    Win+R → shell:startup
echo.
pause
