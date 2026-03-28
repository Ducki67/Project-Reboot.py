@echo off
title Build Production Zip
cd /d "%~dp0"
set ZIP_NAME=RebootLauncher_Release.zip
echo Compiling the executable first to ensure it's up to date...
call compile.bat SKIP
echo.
echo Creating temporary build folder...
if exist "ReleaseBuild" rmdir /s /q "ReleaseBuild"
mkdir ReleaseBuild
echo.
echo Copying executable into build folder...
copy "dist\Reboot Launcher.exe" "ReleaseBuild\"
echo.
echo Copying assets and DLLs...
xcopy "assets" "ReleaseBuild\assets" /E /I /H /Y
xcopy "dlls" "ReleaseBuild\dlls" /E /I /H /Y
echo.
echo Zipping release package...
echo Using Python to safely archive files...
if exist "%ZIP_NAME%" del /q "%ZIP_NAME%"
python -c "import shutil; shutil.make_archive('RebootLauncher_Release', 'zip', 'ReleaseBuild')"
echo.
echo Cleaning up temporary files...
rmdir /s /q "ReleaseBuild"
echo.
echo Done! Successfully created %ZIP_NAME% ready for release.
pause
