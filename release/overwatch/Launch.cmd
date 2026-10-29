@echo off
setlocal
where me3 >nul 2>nul
if errorlevel 1 (
  "%LOCALAPPDATA%\Programs\garyttierney\me3\bin\me3.exe" launch -g nightreign -p "%~dp0UltimateVoices.me3"
) else (
  me3 launch -g nightreign -p "%~dp0UltimateVoices.me3"
)
if errorlevel 1 pause
