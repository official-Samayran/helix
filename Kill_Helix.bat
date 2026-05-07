@echo off
:: Admin Rights Request
if not "%1"=="am_admin" (
    powershell -Command "Start-Process -Verb RunAs -FilePath '%0' -ArgumentList 'am_admin'"
    exit /b
)

echo 🚨 Terminating Helix, Ollama, and WebUI...

:: 1. Sirf Python processes ko maro (Helix & WebUI)
taskkill /f /im python.exe /t 2>nul
taskkill /f /im pythonw.exe /t 2>nul

:: 2. Sirf Ollama aur uske runners ko maro
taskkill /f /im ollama.exe /t 2>nul
taskkill /f /im "ollama runner.exe" /t 2>nul

:: 3. Specific Port clean-up (Only for Helix/WebUI ports)
:: Is baar hum PID 0 ko skip karenge logic se
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr /v "0.0.0.0:0"') do (
    if not "%%a"=="0" taskkill /f /pid %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr /v "0.0.0.0:0"') do (
    if not "%%a"=="0" taskkill /f /pid %%a 2>nul
)

echo.
echo ✅ Clean-up complete. System is safe, Sir.
pause