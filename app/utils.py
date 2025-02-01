import instaloader

L = instaloader.Instaloader()

def extract_instagram_data(url):
    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
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

        return media_items

    except Exception as e:
        return {"error": str(e)}