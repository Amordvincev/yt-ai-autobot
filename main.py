import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from generate_script import load_templates, pick_template
from generate_audio import generate_audio
from assemble_video import build_shorts

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SHORTS_COUNT = config.get("shorts_per_day", 3)


def run_pipeline(upload=True):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    templates = load_templates()
    used_ids = set()
    created = []

    for i in range(min(SHORTS_COUNT, len(templates))):
        available = [t for t in templates if t["id"] not in used_ids]
        if not available:
            break
        script = available[i % len(available)]
        used_ids.add(script["id"])

        print(f"[{i+1}/{SHORTS_COUNT}] {script['title']}")

        audio_path = os.path.join(OUTPUT_DIR, f"audio_{i}.mp3")
        voice = config["voice"]
        generate_audio(script["lines"], audio_path, voice=voice)

        video_path = os.path.join(OUTPUT_DIR, f"shorts_{i}.mp4")
        result = build_shorts(script, audio_path, i, video_path)

        if result:
            created.append(result)

    print(f"\n[done] Created {len(created)} shorts")
    for v in created:
        kb = os.path.getsize(v) / 1024
        print(f"  {v} ({kb:.0f} KB)")

    if upload and created:
        from upload_youtube import upload_video
        for vid_path in created:
            script = {"title": f"Shorts #{vid_path.split('_')[-1].split('.')[0]}", "tags": ["shorts"]}
            upload_video(vid_path, script, config)

    return created


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args()
    run_pipeline(upload=not args.no_upload)
