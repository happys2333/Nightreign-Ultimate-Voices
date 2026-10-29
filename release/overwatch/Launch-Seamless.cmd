@echo off
setlocal
if not exist "%~dp0SeamlessCoop\nrsc.dll" (
  echo Copy your existing complete SeamlessCoop folder beside this launcher first.
  echo For a custom mod profile, read README.en.md or README.zh-CN.md.
  pause
  exit /b 1
)
where me3 >nul 2>nul
if errorlevel 1 (
  "%LOCALAPPDATA%\Programs\garyttierney\me3\bin\me3.exe" launch -g nightreign -p "%~dp0UltimateVoices-Seamless.me3"
) else (
  me3 launch -g nightreign -p "%~dp0UltimateVoices-Seamless.me3"
)
if errorlevel 1 pause
