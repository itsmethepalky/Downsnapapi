from flask import Flask, request, jsonify, send_file
import instaloader
import os
import datetime
import requests

app = Flask(__name__)
loader = instaloader.Instaloader()

# Directory for storing downloads
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/preview', methods=['GET'])
def get_preview():
    """Fetch Instagram media preview for all types, including carousels"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Try to extract shortcode from URL for Post, Reel, Story, etc.
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        media_list = []
        for idx, item in enumerate(post.get_sidecar_nodes()):
            media_url = item.url
            media_type = "video" if item.is_video else "image"
            media_list.append({
                "media_url": media_url,
                "media_type": media_type,
                "caption": item.caption if item.caption else "No caption"
            })

        return jsonify({
            "username": post.owner_username,
            "media_list": media_list
        })

    except Exception:
        # Try Profile Picture
        try:
            profile = instaloader.Profile.from_username(loader.context, url.split("/")[-2])
            media_url = profile.profile_pic_url

            return jsonify({
                "username": profile.username,
                "media_url": media_url,
                "media_type": "image"
            })
        except Exception:
            # Try Story (for user stories)
            try:
                username = url.split("/")[-2]
                story = loader.get_stories(userids=[loader.context.get_profile(username).userid])
                media_url = story[0].items[0].url

                return jsonify({
                    "username": username,
                    "media_url": media_url,
                    "media_type": "image"
                })
            except Exception:
                return jsonify({"error": "Invalid Instagram URL or private account"}), 400

@app.route('/download', methods=['GET'])
def download_media():
    """Download Instagram media and return file"""
    media_url = request.args.get('media_url')

    if not media_url:
        return jsonify({"error": "Media URL is required"}), 400

    try:
        # Get current date and time
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Determine file extension
        file_extension = "mp4" if "video" in media_url else "jpg"
        filename = f"Downsnap-{timestamp}.{file_extension}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        # Download media
        response = requests.get(media_url, stream=True)
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