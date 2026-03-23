@echo off
title Launcher
cd /d "%~dp0"
python -m pip install customtkinter psutil pillow
echo [INFO] Rendszergazdakent futtasd a .bat-ot!
python main.py
pause
