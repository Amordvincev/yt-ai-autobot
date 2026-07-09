import os
import json
import requests
import random

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def search_video(search_query, api_key, per_page=5):
    if not api_key:
        return None

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": api_key}
    params = {
        "query": search_query,
        "per_page": per_page,
        "orientation": "landscape",
        "size": "medium",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        videos = data.get("videos", [])
        if not videos:
            return None

        video = random.choice(videos)
        for file in video.get("video_files", []):
            if file.get("quality") in ("hd", "sd") and file.get("width", 0) >= 1280:
                return {
                    "url": file["link"],
                    "width": file.get("width"),
                    "height": file.get("height"),
                    "duration": video.get("duration"),
                }
    except Exception as e:
        print(f"[Pexels error] {e}")
    return None


def download_video(url, index):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    ext = ".mp4"
    path = os.path.join(ASSETS_DIR, f"clip_{index}{ext}")

    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return path
    except Exception as e:
        print(f"[download error] {e}")
        return None


def fetch_and_cache_media(script_lines, config):
    api_key = config.get("pexels_api_key", "")
    media_files = []

    if not api_key:
        print("[Pexels] No API key — using fallback static assets")
        return media_files

    for i, line in enumerate(script_lines):
        words = [w for w in line.split() if len(w) > 4]
        query = random.choice(words) if words else "nature"
        result = search_video(query, api_key)
        if result:
            path = download_video(result["url"], i)
            if path:
                media_files.append({"file": path, "index": i})
        else:
            media_files.append({"file": None, "index": i})

    return media_files


if __name__ == "__main__":
    from config import config
    lines = ["Тестовая строка для поиска видео"]
    media = fetch_and_cache_media(lines, config)
    print(json.dumps(media, ensure_ascii=False, indent=2))
