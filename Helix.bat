@echo off
setlocal
set PYTHONUTF8=1
cd /d "E:\Helix"

:: Cleanup: Pehle se chal rahe saare processes ko band karna
taskkill /f /im python.exe /t >nul 2>&1
taskkill /f /im pythonw.exe /t >nul 2>&1
taskkill /f /im ollama.exe /t >nul 2>&1

:: 1. Start Ollama (Foundation)
start /b "" ollama serve

:: 2. Start Helix Engine (Port: 8000)
start /b "" "C:\Users\offic\AppData\Local\Programs\Python\Python311\python.exe" "E:\Helix\helix_engine.py"

:: 3. Start Helix Coding Agent (Port: 8888) - New Upgradation
start /b "" "C:\Users\offic\AppData\Local\Programs\Python\Python311\python.exe" "E:\Helix\helix_coding_agent.py"

:: 4. Wait 15 seconds (Systems ko stable hone ke liye)
timeout /t 15 /nobreak >nul

:: 5. Start WebUI (Port: 8080)
set OLLAMA_BASE_URL=http://127.0.0.1:11434
start /b "" "C:\Users\offic\AppData\Local\Programs\Python\Python311\Scripts\open-webui.exe" serve --port 8080

exit