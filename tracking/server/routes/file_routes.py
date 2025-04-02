from flask import Blueprint, request, jsonify, send_file
import os
from config import UPLOADS_DIR
import mimetypes
from datetime import datetime

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
