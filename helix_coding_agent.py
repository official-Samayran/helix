import os
import shlex
import logging
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# --- CONFIGURATION ---
ALLOWED_WRITE_PATH = os.path.abspath(r"E:\Helix_Projects")
API_KEY = "your_secure_secret_key_here"  # Match this in your Flutter app
LOG_FILE = "helix_activity.log"

# --- LOGGING SETUP ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] Helix: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_action(action, details):
    logging.info(f"{action} | {details}")

# --- SECURITY UTILITIES ---
def check_auth():
    key = request.headers.get("X-API-KEY")
    if not key or key != API_KEY:
        log_action("AUTH_FAILURE", f"Invalid key from {request.remote_addr}")
        abort(401, description="Unauthorized: Invalid API Key")

def is_write_safe(path):
    """Restricts Write/Delete/Modify to E:\Helix_Projects."""
    target = os.path.abspath(path)
    return target.startswith(ALLOWED_WRITE_PATH)

# --- CORE ROUTES ---

@app.before_request
def before_request():
    if request.endpoint != 'heartbeat':
        check_auth()

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return jsonify({"status": "stealth_mode_active", "identity": "Helix"}), 200

@app.route('/read', methods=['POST'])
def read_file():
    """Global Read Access: Allowed to read from anywhere on system."""
    data = request.json
    path = data.get('path')
    try:
        if os.path.isdir(path):
            return jsonify({"type": "directory", "content": os.listdir(path)})
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify({"type": "file", "content": f.read()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/write', methods=['POST'])
def write_file():
    data = request.json
    path = data.get('path')
    content = data.get('content', '')

    if not is_write_safe(path):
        log_action("WRITE_DENIED", path)
        return jsonify({"error": "Forbidden: Path outside ALLOWED_WRITE_PATH"}), 403

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_action("WRITE_SUCCESS", path)
        return jsonify({"status": "success", "path": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute():
    """Secure execution using shlex and shell=False."""
    data = request.json
    raw_command = data.get('command')
    cwd = data.get('path', ALLOWED_WRITE_PATH)

    try:
        args = shlex.split(raw_command)
        # Security: Prevent execution of relative scripts outside allowed path if needed
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            shell=False 
        )
        stdout, stderr = process.communicate()
        log_action("EXECUTE", raw_command)
        return jsonify({"stdout": stdout, "stderr": stderr, "code": process.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- AUTONOMOUS ENDPOINTS ---

@app.route('/plan', methods=['POST'])
def generate_plan():
    """Generates a structured implementation roadmap."""
    data = request.json
    goal = data.get('goal', 'No goal provided')
    
    # Logic for task decomposition (Mocking autonomous logic)
    plan = [
        {"task_id": 1, "desc": f"Analyze requirements for: {goal}", "status": "pending"},
        {"task_id": 2, "desc": "Check directory structure in ALLOWED_WRITE_PATH", "status": "pending"},
        {"task_id": 3, "desc": "Execute implementation and verify via /execute", "status": "pending"}
    ]
    log_action("PLAN_GENERATED", goal)
    return jsonify({"goal": goal, "tasks": plan})

@app.route('/walkthrough', methods=['GET'])
def walkthrough():
    """Returns a Markdown summary of recent activity from the log."""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()[-20:] # Last 20 actions
        md = "### Helix Session Walkthrough\n" + "".join([f"- {l}" for l in lines])
        return jsonify({"markdown": md})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("""
    🧬 HELIX AUTONOMOUS AGENT
    -------------------------
    STATUS: STEALTH MODE ACTIVE
    AUTH: API-KEY ENABLED
    READ: GLOBAL
    WRITE: LOCALIZED (E:\\Helix_Projects)
    """)
    app.run(host='0.0.0.0', port=8888)