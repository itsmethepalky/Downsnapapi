from flask import Flask, request, jsonify, send_file
import instaloader
from fake_useragent import UserAgent
import os
import datetime
import requests
import random
import time

app = Flask(__name__)

# Initialize Instaloader with spoofed settings
loader = instaloader.Instaloader()

# Directory for storing downloads
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Initialize UserAgent to rotate user agents
ua = UserAgent()

# Predefined list of fake headers
HEADERS_LIST = [
    {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"},
    {"User-Agent": ua.random, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9"},
    {"User-Agent": ua.random, "Referer": "https://www.google.com/"},
]

def get_random_headers():
    """Returns a random header to mimic real browser behavior."""
    return random.choice(HEADERS_LIST)

@app.route('/preview', methods=['GET'])
def get_preview():
    """Fetch Instagram media preview with better spoofing"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    headers = get_random_headers()

    try:
        # Clean URL to remove query parameters
        url = url.split('?')[0]  

        # Introduce random delay (mimicking human behavior)
        time.sleep(random.uniform(1.5, 3.5))

        # Extract shortcode from URL for Post, Reel, etc.
        shortcode = url.split("/")[-2]

        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            media_items = []

            if post.is_video:
                media_items.append({"url": post.video_url, "type": "video"})
            else:
                media_items.append({"url": post.url, "type": "image"})

            for post_media in post.get_sidecar_nodes():
                if post_media.is_video:
                    media_items.append({"url": post_media.video_url, "type": "video"})
                else:
                    media_items.append({"url": post_media.display_url, "type": "image"})

            return jsonify({
                "username": post.owner_username,
                "caption": post.caption,
                "media_items": media_items
            })

        except Exception as e:
            return jsonify({"error": f"Failed to fetch post: {str(e)}"}), 400

    except Exception as e:
        try:
            profile = instaloader.Profile.from_username(loader.context, url.split("/")[-2])
            return jsonify({
                "username": profile.username,
                "media_url": profile.profile_pic_url,
                "media_type": "image"
            })
        except Exception:
            return jsonify({"error": "Invalid Instagram URL or private account"}), 400

@app.route('/download', methods=['GET'])
def download_media():
    """Download Instagram media with fake headers"""
    media_url = request.args.get('media_url')

    if not media_url:
        return jsonify({"error": "Media URL is required"}), 400

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        file_extension = "mp4" if "video" in media_url else "jpg"
        filename = f"Downsnap-{timestamp}.{file_extension}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        # Spoof request with fake headers
        response = requests.get(media_url, headers=get_random_headers(), stream=True)

        if response.status_code == 200:
            with open(filepath, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({"error": "Failed to download media"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)