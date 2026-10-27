@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv is required: https://docs.astral.sh/uv/getting-started/installation/
  pause
  exit /b 1
)
if "%~1"=="" (
  uv run python -m nuv build
) else (
  uv run python -m nuv build --base-profile "%~1"
)
if errorlevel 1 pause
