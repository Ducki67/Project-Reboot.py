@echo off
title Launcher
cd /d "%~dp0"
python -m pip install customtkinter psutil pillow pypresence pywin32 requests urllib3
echo [INFO] Rendszergazdakent futtasd a .bat-ot!
::python main.py
::python mainTest1.py
::python main wllworking.py :: our back up

:: new

python main.py

pause
