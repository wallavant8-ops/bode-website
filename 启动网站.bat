@echo off
title Bode Hardware Website
cd /d C:\Users\jxzhuyx\Desktop\bode-website
echo Starting Bode Hardware website...
echo Website: http://localhost:5000
echo Admin:   http://localhost:5000/admin
echo.
echo Press Ctrl+C to stop.
echo.
:loop
python app.py
echo.
echo [%date% %time%] Server stopped, restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
