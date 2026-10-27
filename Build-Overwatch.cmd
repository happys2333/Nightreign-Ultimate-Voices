@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag your existing Seamless Co-op .me3 profile onto this file.
  echo Optional second argument: Overwatch installation directory.
  pause
  exit /b 1
)
set "NUV_OW_DIR=D:\Overwatch"
if not "%~2"=="" set "NUV_OW_DIR=%~2"
uv run python -m nuv ow-extract --overwatch-dir "%NUV_OW_DIR%"
if errorlevel 1 goto failed
uv run python -m nuv ow-import --build --base-profile "%~1"
if errorlevel 1 goto failed
echo Ready: dist\UltimateVoices-Overwatch\Launch.cmd
pause
exit /b 0
:failed
echo Preparation failed. See the error above. Existing packages were preserved.
pause
exit /b 1
