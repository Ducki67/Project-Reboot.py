@echo off
title Launcher
cd /d "%~dp0"
python -m pip install customtkinter psutil pillow


python main.py
pause