import os
import subprocess
import psutil
import GPUtil
import wmi
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json

app = FastAPI()

# CORS configuration for Flutter App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_telemetry():
    # CPU & RAM (Non-blocking)
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Disk Usage
    try:
        disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
    except:
        disk = 0.0
    
    # GPU Stats
    try:
        gpus = GPUtil.getGPUs()
        gpu_percent = gpus[0].load * 100 if gpus else 0.0
    except:
        gpu_percent = 0.0

    # Resource Hungry Apps
    top_ram_app = "N/A"
    top_cpu_app = "N/A"
    try:
        processes = []
        for proc in psutil.process_iter(['name', 'memory_percent', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if processes:
            ram_sorted = sorted(processes, key=lambda p: p['memory_percent'] or 0, reverse=True)
            top_ram_app = ram_sorted[0]['name'] if ram_sorted else "N/A"
            
            cpu_sorted = sorted(processes, key=lambda p: p['cpu_percent'] or 0, reverse=True)
            top_cpu_app = cpu_sorted[0]['name'] if cpu_sorted else "N/A"
    except Exception:
        pass

    # Temp & Fan Speed
    temp = 0.0
    fan_speed = 0.0
    try:
        w = wmi.WMI(namespace="root\\wmi")
        temperatures = w.MSAcpi_ThermalZoneTemperature()
        if temperatures:
            temp = (temperatures[0].CurrentTemperature / 10.0) - 273.15
            
        w2 = wmi.WMI()
        fans = w2.Win32_Fan()
        if fans and hasattr(fans[0], 'DesiredSpeed'):
            fan_speed = float(fans[0].DesiredSpeed or 0.0)
    except:
        pass

    return {
        "cpu": cpu,
        "ram": ram,
        "gpu": gpu_percent,
        "disk": disk,
        "temp": round(temp, 1),
        "fanSpeed": fan_speed,
        "topRamApp": top_ram_app,
        "topCpuApp": top_cpu_app,
        "status": "Online"
    }

@app.get("/stats")
async def get_stats():
    # Brief sleep for accurate CPU reading
    psutil.cpu_percent(interval=0.1)
    try:
        return get_telemetry()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    await websocket.accept()
    psutil.cpu_percent(interval=None) # Init
    try:
        while True:
            data = get_telemetry()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except Exception as e:
        print(f"📡 WebSocket Log: Client Disconnected ({e})")

@app.get("/launch/{app_name}")
async def launch_app(app_name: str):
    app_map = {
        "chrome": "start chrome",
        "vscode": "code",
        "whatsapp": "start whatsapp:",
        "notepad": "notepad"
    }
    cmd = app_map.get(app_name.lower(), app_name)
    try:
        subprocess.Popen(cmd, shell=True)
        return {"status": "success", "message": f"{app_name} initialized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- NEW: HELIX CODING AGENT CONTROLLER ---

@app.post("/command")
@app.post("/start-agent")
async def control_agent(request: Request):
    try:
        body = await request.json()
        command = body.get("command", "")
    except:
        command = "START_CODING_AGENT" # Default for /start-agent

    if command == "START_CODING_AGENT":
        agent_script = r"E:\Helix\helix_coding_agent.py"
        if os.path.exists(agent_script):
            # Stealth launch using pythonw and CREATE_NO_WINDOW
            subprocess.Popen(
                ['pythonw', agent_script],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("🧬 HELIX: Coding Agent Woken Up (Stealth Mode)")
            return {"status": "success", "message": "Agent Started Successfully"}
        return {"status": "error", "message": "Script not found at E:\\Helix"}
    
    return {"status": "unknown", "message": "Command not recognized"}

# --- AUTO-START ON RUN ---

if __name__ == "__main__":
    print("------------------------------------------")
    print("🧬 HELIX MASTER ENGINE: ONLINE")
    print("📡 PORT: 8000 | MODE: STEALTH LINKED")
    print("------------------------------------------")
    
    # Optional: Auto-start coding agent when engine starts
    agent_path = r"E:\Helix\helix_coding_agent.py"
    if os.path.exists(agent_path):
        subprocess.Popen(['pythonw', agent_path], creationflags=subprocess.CREATE_NO_WINDOW)
        print("🚀 System: Coding Agent linked background.")

    uvicorn.run(app, host="0.0.0.0", port=8000)