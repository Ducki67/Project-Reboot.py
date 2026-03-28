@echo off
title Compile Reboot Launcher
cd /d "%~dp0"
echo Installing PyInstaller...
python -m pip install pyinstaller
echo.
echo Compiling main.py into a standalone executable...
echo This might take a minute...
python -m PyInstaller --noconfirm --onefile --windowed --icon "assets\icons\reboot.ico" --name "Reboot Launcher" main.py
echo.
echo Compilation complete! 
echo Your shiny new executable is located in the "dist" folder!
if "%1"=="" pause
