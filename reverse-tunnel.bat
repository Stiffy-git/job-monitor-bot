@echo off
REM ============================================
REM Reverse SSH-туннель для Avito (Windows)
REM Запускать на СВОЁМ ПК!
REM ============================================

set SERVER_USER=%1
set SERVER_HOST=%2
set TUNNEL_PORT=%3

if "%SERVER_USER%"=="" set SERVER_USER=root
if "%SERVER_HOST%"=="" set SERVER_HOST=YOUR_SERVER_IP
if "%TUNNEL_PORT%"=="" set TUNNEL_PORT=1080

echo.
echo Reverse SSH-тунnel for Avito
echo Server: %SERVER_USER%@%SERVER_HOST%
echo Port on server: %TUNNEL_PORT%
echo.
echo To stop: press Ctrl+C
echo.

ssh -R %TUNNEL_PORT%:127.0.0.1:%TUNNEL_PORT% -N -o ServerAliveInterval=60 %SERVER_USER%@%SERVER_HOST%
