@echo off
title Netflix Email Relay Bot
cd /d "%~dp0"

if not exist .env (
  echo No .env found. Running setup wizard first...
  echo.
  python setup.py
  if errorlevel 1 goto :fail
  echo.
)

echo Starting bot... (press Ctrl+C to stop)
python bot.py
if errorlevel 1 goto :fail
goto :eof

:fail
echo.
echo Something went wrong. Make sure Python is installed and run setup.py first.
pause
