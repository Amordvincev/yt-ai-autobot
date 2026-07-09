import os
import subprocess
import random
import math

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def create_shorts_bg(color_theme, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    script_path = os.path.join(ASSETS_DIR, "gen_bg.py")

    code = f'''
from PIL import Image, ImageDraw
import random
w, h = 1080, 1920
colors = [
    [(10,10,35),(30,20,60)],
    [(35,10,10),(60,20,20)],
    [(10,35,10),(20,60,30)],
    [(35,35,10),(60,60,20)],
    [(10,10,10),(30,30,40)],
]
c = colors[{color_theme} % len(colors)]
img = Image.new("RGB", (w, h), c[0])
draw = ImageDraw.Draw(img)
for i in range(20):
    x = random.randint(0, w)
    y = random.randint(0, h)
    r = random.randint(50, 300)
    alpha = random.randint(10, 40)
    col = tuple(min(255, int(c[1][j] + (255-c[1][j])*0.2)) for j in range(3))
    for offset in range(r, 0, -2):
        a = int(alpha * (1 - offset/r))
        mix = tuple(int(c[0][j] + (col[j]-c[0][j])*(1-offset/r)) for j in range(3))
        draw.ellipse([x-offset, y-offset, x+offset, y+offset], fill=mix+ (a,) if False else mix)
img.save(r"{output_path}")
print("BG saved")
'''
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    subprocess.run(["python", script_path], capture_output=True, text=True, timeout=60)
    return output_path


def build_shorts(script, audio_path, index, output_path):
    lines = script["lines"]
    audio_duration = None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", audio_path],
            capture_output=True, text=True, timeout=15
        )
        audio_duration = float(result.stdout.strip())
    except Exception:
        audio_duration = 20.0

    subtitle_path = os.path.join(OUTPUT_DIR, f"subs_{index}.srt")
    bg_path = os.path.join(ASSETS_DIR, f"bg_{index}.png")

    create_shorts_bg(index, bg_path)

    per_line_time = audio_duration / max(len(lines), 1)
    line_duration = per_line_time

    with open(subtitle_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines):
            start = i * line_duration
            end = min((i + 1) * line_duration, audio_duration)
            start_h = int(start // 3600)
            start_m = int((start % 3600) // 60)
            start_s = start % 60
            end_h = int(end // 3600)
            end_m = int((end % 3600) // 60)
            end_s = end % 60
            f.write(f"{i+1}\n")
            f.write(f"{start_h:02d}:{start_m:02d}:{start_s:05.2f} --> {end_h:02d}:{end_m:02d}:{end_s:05.2f}\n")
            f.write(f"{line}\n\n")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", bg_path,
        "-i", audio_path,
        "-vf",
        f"subtitles={subtitle_path}:force_style='FontSize=36,FontName=Arial,PrimaryCol=&H00FFFFFF,BackCol=&H80000000,Alignment=2,MarginV=200'",
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
        print(f"[shorts] ffmpeg error: {result.stderr[:300]}")
        return None

    if not os.path.exists(output_path):
        print(f"[shorts] output not created")
        return None

    kb = os.path.getsize(output_path) / 1024
    print(f"[shorts] {output_path} ({kb:.0f} KB, {audio_duration:.0f}s)")
    return output_path


def build_video(script, audio_path, media_files, output_path):
    return build_shorts(script, audio_path, 0, output_path)


if __name__ == "__main__":
    from config import config
    from generate_script import fetch_or_generate_script
    from generate_audio import generate_audio

    script = fetch_or_generate_script(config)
    audio_path = os.path.join(OUTPUT_DIR, "audio_shorts.mp3")
    generate_audio(script["lines"], audio_path)
    video_path = os.path.join(OUTPUT_DIR, "shorts.mp4")
    build_shorts(script, audio_path, 0, video_path)
