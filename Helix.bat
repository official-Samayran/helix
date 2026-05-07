@echo off
setlocal
set PYTHONUTF8=1
cd /d "E:\Helix"

:: Cleanup
taskkill /f /im python.exe /t >nul 2>&1
taskkill /f /im pythonw.exe /t >nul 2>&1
taskkill /f /im ollama.exe /t >nul 2>&1

:: 1. Start Ollama
start /b "" ollama serve

:: 2. Start Helix Engine (8000)
:: Yahan 'python.exe' hi use karo, VBS isse apne aap hide kar dega
start /b "" "C:\Users\offic\AppData\Local\Programs\Python\Python311\python.exe" "E:\Helix\helix_engine.py"

:: 3. Wait 15 seconds
timeout /t 15 /nobreak >nul

:: 4. Start WebUI (8080)
set OLLAMA_BASE_URL=http://127.0.0.1:11434
start /b "" "C:\Users\offic\AppData\Local\Programs\Python\Python311\Scripts\open-webui.exe" serve --port 8080

exit