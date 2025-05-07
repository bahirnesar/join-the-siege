from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from src.classifier import classify_file, classify_batch_files
import asyncio

app = Flask(__name__)

@app.route('/classify_file', methods=['POST'])
def classify_file_route():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_content = file.read()
        filename = secure_filename(file.filename)
        result = classify_file(file_content, filename)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/classify_batch_files', methods=['POST'])
def classify_batch_files_route():
    try:
        if 'files[]' not in request.files:
            return jsonify({"error": "No files provided in the request"}), 400

        files = request.files.getlist('files[]')
        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400
        
        # Process each file
        file_contents = []
        for file in files:
            file_content = file.read()
            filename = secure_filename(file.filename)
            file_contents.append((file_content, filename))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(classify_batch_files(file_contents))
        loop.close()
        
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)