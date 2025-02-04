from flask import Flask, request, jsonify, send_file
import instaloader
from fake_useragent import UserAgent
import os
import datetime
import requests

app = Flask(__name__)
loader = instaloader.Instaloader()

# Directory for storing downloads
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Initialize UserAgent to rotate user agents
ua = UserAgent()

@app.route('/preview', methods=['GET'])
def get_preview():
    """Fetch Instagram media preview for all types"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    headers = {
        "User-Agent": ua.random
    }

    try:
        # Clean URL to remove query parameters
        url = url.split('?')[0]  # Removing query parameters
        
        # Try to extract shortcode from URL for Post, Reel, Story, etc.
        shortcode = url.split("/")[-2]
        
        # Try Post, Reel, or any media type (including carousel)
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            media_items = []

            # Check if the post itself is a video or image
            if post.is_video:
                media_items.append({
                    "url": post.video_url,
                    "type": "video"
                })
            else:
                media_items.append({
                    "url": post.url,
                    "type": "image"
                })

            # If the post contains a carousel (multiple images/videos)
            for post_media in post.get_sidecar_nodes():
                if post_media.is_video:
                    media_items.append({
                        "url": post_media.video_url,
                        "type": "video"
                    })
                else:
                    media_items.append({
                        "url": post_media.display_url,
                        "type": "image"
                    })
            
            return jsonify({
                "username": post.owner_username,
                "caption": post.caption,
                "media_items": media_items
            })
        
        except Exception as e:
            return jsonify({"error": f"Failed to fetch post: {str(e)}"}), 400

    except Exception as e:
        # Handle other exceptions, e.g., profile pictures, stories, etc.
        try:
            # Try Profile Picture (if URL corresponds to a profile)
            profile = instaloader.Profile.from_username(loader.context, url.split("/")[-2])
            return jsonify({
                "username": profile.username,
                "media_url": profile.profile_pic_url,
                "media_type": "image"
            })
        except Exception:
            try:
                # Try Story (for user stories)
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
        # Get current date and time for timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Determine file extension based on the media type
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