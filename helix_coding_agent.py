import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
ALLOWED_WRITE_PATH = r"E:\Helix_Projects"

def is_path_safe(path):
    return os.path.abspath(path).startswith(os.path.abspath(ALLOWED_WRITE_PATH))

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    command = data.get('command')
    # Default path E:\Helix_Projects rahega agar alag se nahi diya
    cwd = data.get('path', ALLOWED_WRITE_PATH) 

    print(f"🚀 Executing Terminal Command: {command}")
    
    try:
        # shell=True zaruri hai 'flutter' ya 'cd' jaise commands ke liye
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        stdout, stderr = process.communicate()
        
        print(f"✅ Output: {stdout[:100]}...") # Debug log
        return jsonify({
            "stdout": stdout,
            "stderr": stderr,
            "code": process.returncode
        }), 200
    except Exception as e:
        print(f"❌ Execution Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    data = request.json
    command = data.get('command')
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ALLOWED_WRITE_PATH)
        stdout, stderr = process.communicate()
        return jsonify({"stdout": stdout, "stderr": stderr, "code": process.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/write', methods=['POST'])
def write_file():
    data = request.json
    file_path = data.get('path')
    content = data.get('content')
    if not is_path_safe(file_path):
        return jsonify({"error": "Access Denied"}), 403
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def write_file():
    data = request.json
    print(f"📩 Received Write Request: {data}") # <--- DEBUG PRINT
    
    file_path = data.get('path')
    content = data.get('content')
    
    if not is_path_safe(file_path):
        print(f"🚫 Security Block: Path {file_path} is unsafe!") # <--- DEBUG PRINT
        return jsonify({"error": "Access Denied"}), 403
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Successfully wrote: {file_path}") # <--- DEBUG PRINT
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"❌ Write Error: {str(e)}") # <--- DEBUG PRINT
        return jsonify({"error": str(e)}), 500

# Ye route phone ke wake-up signal ke liye hai
@app.route('/command', methods=['POST'])
def command_handler():
    data = request.json
    if data.get('command') == 'START_CODING_AGENT':
        print("🧬 HELIX: Coding Agent Activation Confirmed!")
        return jsonify({"status": "online"}), 200
    return jsonify({"status": "unknown"}), 404

@app.route('/list', methods=['POST'])
def list_files():
    data = request.json
    path = data.get('path', ALLOWED_WRITE_PATH)
    if not is_path_safe(path):
        return jsonify({"error": "Access Denied"}), 403
    try:
        files = os.listdir(path)
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🧬 HELIX CODING AGENT: STANDBY ON PORT 8888")
    app.run(host='0.0.0.0', port=8888)