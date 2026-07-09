import os
import subprocess
import random

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def get_audio_duration(audio_path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", audio_path],
            capture_output=True, text=True, timeout=15
        )
        return max(float(r.stdout.strip()), 5.0)
    except Exception:
        return 20.0


def _wrap_text(text, max_chars=30):
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current += " " + w if current else w
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def create_subtitles(lines, duration, output_path):
    wrapped = []
    for line in lines:
        wrapped.extend(_wrap_text(line))
    per_line = duration / max(len(wrapped), 1)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(wrapped):
            s = i * per_line
            e = min((i + 1) * per_line, duration)
            f.write(f"{i+1}\n")
            f.write(f"{s//3600:02.0f}:{(s%3600)//60:02.0f}:{s%60:06.3f} --> "
                    f"{e//3600:02.0f}:{(e%3600)//60:02.0f}:{e%60:06.3f}\n")
            f.write(f"{line}\n\n")


def generate_bg_image(palette_idx, output_path):
    palettes = [
        [(15, 5, 40), (40, 10, 60), (10, 5, 30)],
        [(40, 10, 5), (60, 20, 10), (30, 5, 5)],
        [(5, 30, 10), (10, 50, 20), (5, 20, 5)],
        [(40, 35, 5), (60, 50, 10), (30, 25, 5)],
        [(5, 15, 40), (10, 25, 60), (5, 10, 30)],
        [(40, 5, 30), (60, 10, 50), (30, 5, 20)],
    ]
    c = palettes[palette_idx % len(palettes)]

    try:
        from PIL import Image, ImageDraw
        w, h = 1080, 1920
        img = Image.new("RGB", (w, h), c[0])
        draw = ImageDraw.Draw(img)
        cx, cy = w // 2, h // 2
        for i in range(3):
            col = c[i]
            r = 600 - i * 100
            for j in range(5, 0, -1):
                cr = int(r * j / 5)
                grad = tuple(min(255, int(col[k] + (255 - col[k]) * 0.1 * (1 - j / 5))) for k in range(3))
                draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=grad)
        for i in range(50):
            x, y, r = random.randint(0, w), random.randint(0, h), random.randint(2, 8)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 30))
        img.save(output_path, "PNG")
    except ImportError:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=#{c[0][0]:02x}{c[0][1]:02x}{c[0][2]:02x}:s=1080x1920:d=1",
            "-frames:v", "1", output_path,
        ], capture_output=True, timeout=15)


def build_shorts(script, audio_path, index, output_path):
    lines = script["lines"]
    duration = get_audio_duration(audio_path)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    subs = os.path.join(OUTPUT_DIR, f"subs_{index}.srt")
    create_subtitles(lines, duration, subs)

    bg_img = os.path.join(ASSETS_DIR, f"bg_{index}.png")
    generate_bg_image(index, bg_img)

    sub_style = (
        "FontName=DejaVuSans-Bold,FontSize=38,"
        "PrimaryCol=&H00FFFFFF,"
        "OutlineCol=&HFF000000,"
        "BorderStyle=3,Outline=3,Shadow=2,"
        "Alignment=2,MarginV=200"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", bg_img,
        "-i", audio_path,
        "-filter_complex",
        f"[0:v]zoompan=z='min(zoom+0.001,1.05)':d={duration}*30:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
        f"colorbalance=rh=-0.1:gh=-0.05:bh=0.1,"
        f"subtitles={subs}:force_style='{sub_style}'[vid]",
        "-map", "[vid]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        print(f"[video] error: {p.stderr[:400]}")
        return None
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        kb = os.path.getsize(output_path) / 1024
        print(f"[video] OK {output_path} ({kb:.0f} KB)")
        return output_path
    return None


def build_video(script, audio_path, media_files, output_path):
    return build_shorts(script, audio_path, 0, output_path)
