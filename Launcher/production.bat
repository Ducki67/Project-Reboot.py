@echo off
title Build Production Release
cd /d "%~dp0"

echo Compiling the executable first to ensure it's up to date...
call compile.bat SKIP
echo.

echo Creating standalone build folder...
if exist "ReleaseBuild" rmdir /s /q "ReleaseBuild"
mkdir ReleaseBuild

echo Copying compiled executable into build folder...
copy "dist\Reboot.py.exe" "ReleaseBuild\"

echo Copying assets and DLLs...
xcopy "assets" "ReleaseBuild\assets" /E /I /H /Y >nul
xcopy "dlls" "ReleaseBuild\dlls" /E /I /H /Y >nul

echo.
choice /C YN /M "Do you want to ZIP the portable release?"
if errorlevel 2 goto AskSetup
if errorlevel 1 (
    echo.
    echo Zipping portable release...
    if exist "Reboot.py_Portable.zip" del /q "Reboot.py_Portable.zip"
    python -c "import shutil; shutil.make_archive('Reboot.py_Portable', 'zip', 'ReleaseBuild')"
    echo Successfully created Reboot.py_Portable.zip
)

:AskSetup
echo.
choice /C YN /M "Do you want to build the Desktop Installer (.exe setup)?"
if errorlevel 2 goto Finish
if errorlevel 1 (
    echo.
    set ISCC_PATH=
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
    
    if "%ISCC_PATH%"=="" (
        echo Inno Setup 6 compiler (ISCC.exe) not found!
        echo Please download and install it from: https://jrsoftware.org/isdl.php
    ) else (
        echo Found Inno Setup Compiler. Compiling installer.iss...
        %ISCC_PATH% "installer.iss"
        echo Installer created in Output\
    )
)

:Finish
echo.
echo =========================================================
echo Done! 
echo The prepared unzipped files remain in the ReleaseBuild\ folder.
echo =========================================================
pause
