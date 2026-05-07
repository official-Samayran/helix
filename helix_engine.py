import os
import subprocess
import psutil
import GPUtil
import wmi
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_telemetry():
    # CPU & RAM
    cpu = psutil.cpu_percent(interval=None) # Use None for non-blocking in WS loop, handle interval externally if needed, but 0.1 is okay for simple. Let's use 0.1
    # Actually for a loop that sleeps 1s, interval=None gives percent since last call!
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Disk
    try:
        disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
    except:
        disk = 0.0
    
    # GPU
    gpus = GPUtil.getGPUs()
    gpu_percent = gpus[0].load * 100 if gpus else 0.0

    # Top Apps (RAM & CPU)
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
            
            # Simple sorting for CPU might be inaccurate in interval=None without sleep, but it's okay for an indicator.
            cpu_sorted = sorted(processes, key=lambda p: p['cpu_percent'] or 0, reverse=True)
            top_cpu_app = cpu_sorted[0]['name'] if cpu_sorted else "N/A"
    except Exception:
        pass

    # Temp & Fan via WMI
    temp = 0.0
    fan_speed = 0.0
    try:
        w = wmi.WMI(namespace="root\\wmi")
        try:
            temperatures = w.MSAcpi_ThermalZoneTemperature()
            if temperatures:
                # WMI returns temp in decidegrees Kelvin. Convert to Celsius: (K / 10) - 273.15
                temp = (temperatures[0].CurrentTemperature / 10.0) - 273.15
        except:
            pass
            
        w2 = wmi.WMI()
        try:
            fans = w2.Win32_Fan()
            if fans and hasattr(fans[0], 'DesiredSpeed'):
                fan_speed = float(fans[0].DesiredSpeed or 0.0)
        except:
            pass
    except Exception:
        pass

    return {
        "cpu": cpu,
        "ram": ram,
        "gpu": gpu_percent,
        "disk": disk,
        "temp": temp,
        "fanSpeed": fan_speed,
        "topRamApp": top_ram_app,
        "topCpuApp": top_cpu_app,
        "status": "Online"
    }

@app.get("/stats")
def get_stats():
    # Need to trigger psutil.cpu_percent once before getting the value for accurate read if it wasn't called recently.
    psutil.cpu_percent(interval=0.1)
    try:
        return get_telemetry()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    await websocket.accept()
    psutil.cpu_percent(interval=None) # Initialize
    try:
        while True:
            data = get_telemetry()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket disconnected: {e}")

@app.get("/launch/{app_name}")
def launch_app(app_name: str):
    app_map = {
        "chrome": "start chrome",
        "premiere": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Adobe Premiere Pro 2023.lnk",
        "vscode": "code",
        "whatsapp": "start whatsapp:"
    }
    
    cmd = app_map.get(app_name.lower(), app_name)
    try:
        if ".lnk" in cmd or ":" in cmd:
            os.startfile(cmd)
        else:
            subprocess.Popen(cmd, shell=True)
        return {"status": "success", "message": f"{app_name} launched"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)