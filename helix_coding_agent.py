import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
# Identification: This is the Master Agent (Helix)
ALLOWED_WRITE_PATH = r"E:\Helix_Projects"

def is_path_safe(path):
    return os.path.abspath(path).startswith(os.path.abspath(ALLOWED_WRITE_PATH))

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    command = data.get('command')
    cwd = data.get('path', ALLOWED_WRITE_PATH) 
    
    # Helix handles complex commands by ensuring the environment is ready
    print(f"🚀 Helix Executing: {command}")
    
    try:
        # Note: To run Flutter commands, the system PATH must be configured on the PC
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        stdout, stderr = process.communicate()
        return jsonify({
            "stdout": stdout,
            "stderr": stderr,
            "code": process.returncode
        }), 200
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
        return jsonify({"status": "success", "agent": "Helix"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.json
    file_path = data.get('path')
    if not is_path_safe(file_path):
        return jsonify({"error": "Access Denied"}), 403
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            import shutil
            shutil.rmtree(file_path)
        else:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"status": "deleted", "path": file_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/command', methods=['POST'])
def command_handler():
    data = request.json
    if data.get('command') == 'START_CODING_AGENT':
        print("🧬 Helix Coding Agent: Activation Confirmed!")
        return jsonify({"status": "online", "identity": "Helix"}), 200
    return jsonify({"status": "unknown"}), 404

if __name__ == '__main__':
    print("🧬 HELIX (Master) CODING AGENT: STANDBY ON PORT 8888")
    app.run(host='0.0.0.0', port=8888)