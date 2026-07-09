#!/usr/bin/env python3
import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from generate_script import fetch_or_generate_script
from generate_audio import generate_audio
from fetch_media import fetch_and_cache_media
from assemble_video import build_video
from upload_youtube import upload_video

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def run_pipeline(upload=True):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script = fetch_or_generate_script(config)

    print(f"[pipeline] Title: {script['title']}")
    print(f"[pipeline] Lines: {len(script['lines'])}")

    audio_path = os.path.join(OUTPUT_DIR, f"audio_{timestamp}.mp3")
    generate_audio(script["lines"], audio_path, voice=config["voice"])
    print(f"[pipeline] Audio: {audio_path}")

    media_files = fetch_and_cache_media(script["lines"], config)
    print(f"[pipeline] Media clips: {len(media_files)}")

    video_path = os.path.join(OUTPUT_DIR, f"video_{timestamp}.mp4")
    result_path = build_video(script, audio_path, media_files, video_path)

    if not result_path or not os.path.exists(result_path):
        print("[pipeline] Video assembly failed")
        return

    print(f"[pipeline] Video: {result_path}")

    if upload:
        url = upload_video(result_path, script, config)
        if url:
            print(f"[pipeline] Done! Published: {url}")
        else:
            print("[pipeline] Video created but upload skipped (no auth)")
    else:
        print(f"[pipeline] Done! Video saved locally: {result_path}")

    for f in [audio_path]:
        try:
            if os.path.exists(f):
                os.remove(f)
                print(f"[pipeline] Cleaned up: {f}")
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-upload", action="store_true", help="Skip YouTube upload")
    args = parser.parse_args()

    run_pipeline(upload=not args.no_upload)
