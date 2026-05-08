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
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tracking I/O rates
last_io = {
    "time": time.time(),
    "net_recv": psutil.net_io_counters().bytes_recv,
    "net_sent": psutil.net_io_counters().bytes_sent,
    "disk_read": psutil.disk_io_counters().read_bytes,
    "disk_write": psutil.disk_io_counters().write_bytes
}

def get_telemetry():
    global last_io
    current_time = time.time()
    elapsed = max(current_time - last_io["time"], 0.1)
    
    # CPU & RAM
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Network (KB/s)
    net = psutil.net_io_counters()
    down = (net.bytes_recv - last_io["net_recv"]) / 1024 / elapsed
    up = (net.bytes_sent - last_io["net_sent"]) / 1024 / elapsed
    
    # Disk
    usage = psutil.disk_usage(os.path.abspath(os.sep)).percent
    dio = psutil.disk_io_counters()
    read = (dio.read_bytes - last_io["disk_read"]) / 1024 / elapsed
    write = (dio.write_bytes - last_io["disk_write"]) / 1024 / elapsed

    last_io.update({
        "time": current_time, "net_recv": net.bytes_recv, "net_sent": net.bytes_sent,
        "disk_read": dio.read_bytes, "disk_write": dio.write_bytes
    })

    # GPU
    gpus = GPUtil.getGPUs()
    gpu_data = {
        "load": gpus[0].load * 100 if gpus else 0.0,
        "memory": gpus[0].memoryUtil * 100 if gpus else 0.0,
        "temp": gpus[0].temperature if gpus else 0.0
    }

    # Top Apps
    top_apps = {"ram": "N/A", "cpu": "N/A"}
    try:
        procs = sorted([p.info for p in psutil.process_iter(['name', 'memory_percent', 'cpu_percent'])], 
                       key=lambda x: x['memory_percent'] or 0, reverse=True)
        if procs:
            top_apps["ram"] = procs[0]['name']
            top_apps["cpu"] = sorted(procs, key=lambda x: x['cpu_percent'] or 0, reverse=True)[0]['name']
    except: pass

    # Thermal & Fan (WMI)
    temp = 0.0
    fan_speed = 0.0
    try:
        w = wmi.WMI(namespace="root\\wmi")
        temps = w.MSAcpi_ThermalZoneTemperature()
        if temps: temp = (temps[0].CurrentTemperature / 10.0) - 273.15
        
        fans = wmi.WMI().Win32_Fan()
        if fans and hasattr(fans[0], 'DesiredSpeed'):
            fan_speed = float(fans[0].DesiredSpeed or 0.0)
    except: pass

    return {
        "cpu": cpu,
        "ram": ram,
        "gpu": gpu_data,
        "network": {"down": round(down, 2), "up": round(up, 2)},
        "disk": {"usage": usage, "read": round(read, 2), "write": round(write, 2)},
        "temp": round(temp, 1),
        "fanSpeed": fan_speed,
        "topRamApp": top_apps["ram"],
        "topCpuApp": top_apps["cpu"],
        "status": "Online",
        "agent_identity": "Helix",
        "hierarchy_role": "Master",
        "status": "Online"
    }

@app.get("/stats")
def get_stats():
    psutil.cpu_percent(interval=0.1)
    return get_telemetry()

@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    await websocket.accept()
    psutil.cpu_percent(interval=None) 
    try:
        while True:
            await websocket.send_text(json.dumps(get_telemetry()))
            await asyncio.sleep(1)
    except: pass

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
        if ".lnk" in cmd or ":" in cmd: os.startfile(cmd)
        else: subprocess.Popen(cmd, shell=True)
        return {"status": "success", "message": f"{app_name} launched"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)