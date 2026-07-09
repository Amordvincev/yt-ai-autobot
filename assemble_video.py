import os
import subprocess
import json

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


def seconds_to_ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_audio_duration(audio_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        audio_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        print(f"[ffprobe error] {e}")
        return 60.0


def create_subtitle_file(lines, audio_duration, output_path):
    line_duration = audio_duration / len(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("1\n")
        f.write("00:00:00,000 --> 00:00:05,000\n")
        f.write("Подпишись на канал\n\n")

        start = 0.0
        for i, line in enumerate(lines):
            end = min(start + line_duration, audio_duration)
            start_ts = seconds_to_ts(start) + ",000"
            end_ts = seconds_to_ts(end) + ",000"
            f.write(f"{i+2}\n")
            f.write(f"{start_ts} --> {end_ts}\n")
            f.write(f"{line}\n\n")
            start = end


def build_video(script, audio_path, media_files, output_path):
    lines = script["lines"]
    audio_duration = get_audio_duration(audio_path)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    subtitle_path = os.path.join(OUTPUT_DIR, "subtitles.srt")
    create_subtitle_file(lines, audio_duration, subtitle_path)

    valid_clips = [
        m["file"] for m in media_files
        if m["file"] and os.path.exists(m["file"])
    ]

    filters = []
    if valid_clips:
        for i, clip in enumerate(valid_clips):
            filters.append(f"movie={clip}:f=image2[f{i}]")
        concat_inputs = "".join(f"[f{i}]" for i in range(len(valid_clips)))
        filters.append(f"{concat_inputs}concat=n={len(valid_clips)}:v=1:a=0,scale=1280:720[vid]")
        filter_complex = ";".join(filters)
        video_input = "[vid]"
    else:
        bg_path = os.path.join(ASSETS_DIR, "bg.png")
        if not os.path.exists(bg_path):
            _create_fallback_background(bg_path)
        filter_complex = f"movie={bg_path}:loop=0:size=1x[bg];[bg]scale=1280:720[vid]"
        video_input = "[vid]"

    out_file = output_path
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", video_input,
        "-map", "0:a",
        "-vf", f"subtitles={subtitle_path}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        out_file,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        print(f"[video] Saved: {out_file}")
        return out_file
    except subprocess.CalledProcessError as e:
        print(f"[ffmpeg error] {e.stderr}")
        return None


def _create_fallback_background(path):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (1280, 720), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 600, 1280, 720], fill=(30, 30, 50))
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font = ImageFont.load_default()
        draw.text((60, 630), "Подпишись на канал", fill=(255, 255, 255), font=font)
        img.save(path, "PNG")
    except ImportError:
        print("[fallback] PIL not installed, skipping background image")


if __name__ == "__main__":
    from config import config
    from generate_script import fetch_or_generate_script

    script = fetch_or_generate_script(config)
    audio_path = os.path.join(OUTPUT_DIR, "audio.mp3")
    from generate_audio import generate_audio
    generate_audio(script["lines"], audio_path)

    media_files = []
    out = os.path.join(OUTPUT_DIR, "final_video.mp4")
    build_video(script, audio_path, media_files, out)
    print(f"Done: {out}")
