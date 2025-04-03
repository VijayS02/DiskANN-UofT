from flask import Blueprint, request, jsonify, send_file
import os
from services import stream_func
from config import UPLOADS_DIR, BUILD_DIR
import mimetypes
from datetime import datetime
import sys
import subprocess
import time

file_bp = Blueprint("file", __name__)

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:  # 🔹 Check if the file key exists
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':  # 🔹 Check if a file was actually selected
        return jsonify({"error": "No selected file"}), 400

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    file.save(file_path)
    
    return jsonify({"message": "File uploaded successfully", "path": file_path})

@file_bp.route('/uploads')
def list_files():
    if not os.path.exists(UPLOADS_DIR):
        return jsonify({"files": []})

    files_info = []
    for filename in os.listdir(UPLOADS_DIR):
        file_path = os.path.join(UPLOADS_DIR, filename)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

            files_info.append({
                "filename": filename,
                "size_bytes": size,
                "mime_type": mime_type or "application/octet-stream",
                "modified": modified_time,
                "url": f"/uploads/{filename}"  # assuming you serve files from here
            })

    return jsonify({"files": files_info})


@file_bp.route('/uploads/delete', methods=['post'])
def delete_file():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({"error": "Missing filename in request"}), 400

    filename = data['filename']
    file_path = os.path.join(UPLOADS_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        os.remove(file_path)
        return jsonify({"message": f"File '{filename}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stream_func
def perform_fvecs_to_fbin(exec, input_path, output_path, dtype="float"):
        process = subprocess.Popen(
                        [exec, dtype, input_path, output_path],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True,
                    )
        for line in process.stdout:
            sys.stdout.write(line) 
            sys.stdout.flush()

        for line in process.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()

        process.wait()

        time.sleep(1)

        if process.returncode != 0:
            raise Exception("Error computing ground truth")


@file_bp.route('/uploads/fvecs_to_fbin', methods=['post'])
def fvecs_to_fbin():
    convert_executable = os.path.join(BUILD_DIR, 'apps', 'utils', 'fvecs_to_bin')
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({"error": "Missing 'filename' in request"}), 400

    filename = data['filename']
    file_path = os.path.join(UPLOADS_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": f"Input file '{file_path}' not found"}), 404

    if not file_path.endswith('.fvecs'):
        return jsonify({"error": "Input file must have a .fvecs extension"}), 400

    output_path = file_path.replace('.fvecs', '.fbin')

    perform_fvecs_to_fbin(convert_executable, file_path, output_path)

    return jsonify({
        "message": "Conversion Initiated",
        "output_path": output_path,
    }), 200