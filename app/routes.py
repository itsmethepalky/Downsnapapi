from flask import request, jsonify, send_file
from app import app
from app.utils import extract_instagram_data
import requests
from io import BytesIO
from datetime import datetime

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Downsnap API!"})

@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    media_data = extract_instagram_data(url)
    if not media_data:
        return jsonify({"error": "Unable to fetch media"}), 400

    return jsonify({"media": media_data})

@app.route("/api/download-file", methods=["GET"])
def download_file():
    media_url = request.args.get("url")
    if not media_url:
        return jsonify({"error": "Media URL is required"}), 400

    try:
        response = requests.head(media_url, allow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Downsnap-{now}"

        if 'video' in content_type:
            filename += ".mp4"
            mimetype = 'video/mp4'
        elif 'image' in content_type:
            filename += ".jpg"
            mimetype = 'image/jpeg'
        else:
            return jsonify({"error": "Unsupported content type"}), 400

        response = requests.get(media_url, stream=True)
        response.raise_for_status()

        return send_file(BytesIO(response.content), as_attachment=True, download_name=filename, mimetype=mimetype)
    
    except Exception as e:
        return jsonify({"error": "Failed to download the file", "details": str(e)}), 500