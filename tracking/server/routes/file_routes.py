from flask import Blueprint, request, jsonify, send_file
import os
from config import UPLOADS_DIR

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
    files = os.listdir(UPLOADS_DIR)
    return jsonify({"files": files})
