import os
import subprocess
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def build_video(script, audio_path, media_files, output_path):
    lines = script["lines"]
    bg_path = os.path.join(ASSETS_DIR, "bg.png")
    subtitle_path = os.path.join(OUTPUT_DIR, "subtitles.srt")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    with open(subtitle_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines):
            s = i * 15
            e = (i + 1) * 15
            f.write(f"{i+1}\n")
            f.write(f"00:00:{s:02d},000 --> 00:00:{e:02d},000\n")
            f.write(f"{line}\n\n")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", bg_path,
        "-i", audio_path,
        "-vf", f"subtitles={subtitle_path}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"[ffmpeg error]: {result.stderr[:500]}")
        return None

    if not os.path.exists(output_path):
        print("[video] Output file not created")
        return None

    size_kb = os.path.getsize(output_path) / 1024
    print(f"[video] Created: {output_path} ({size_kb:.0f} KB)")
    return output_path
