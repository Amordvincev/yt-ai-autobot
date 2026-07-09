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


def generate_geq_expression(palette_idx):
    palettes = [
        # deep space purple-blue
        {"r": "255*0.08+30*sin(2*PI*T/8+X/200)", "g": "255*0.04+20*cos(2*PI*T/10+Y/200)", "b": "255*0.25+50*sin(2*PI*T/12+X/300+Y/300)"},
        # warm sunset orange-red
        {"r": "255*0.25+60*sin(2*PI*T/9+X/250)", "g": "255*0.08+30*cos(2*PI*T/11+Y/250)", "b": "255*0.04+20*sin(2*PI*T/13+X/350+Y/250)"},
        # neon green-blue
        {"r": "255*0.04+20*sin(2*PI*T/7+X/300)", "g": "255*0.2+40*cos(2*PI*T/9+Y/300)", "b": "255*0.15+35*sin(2*PI*T/11+X/400+Y/300)"},
        # gold-amber
        {"r": "255*0.2+50*sin(2*PI*T/6+X/200)", "g": "255*0.15+40*cos(2*PI*T/8+Y/200)", "b": "255*0.03+15*sin(2*PI*T/10+X/300+Y/200)"},
        # cyberpunk pink-blue
        {"r": "255*0.2+45*sin(2*PI*T/5+X/180)", "g": "255*0.03+15*cos(2*PI*T/7+Y/180)", "b": "255*0.25+55*sin(2*PI*T/9+X/280+Y/180)"},
        # forest green-teal
        {"r": "255*0.05+20*sin(2*PI*T/11+X/280)", "g": "255*0.2+35*cos(2*PI*T/13+Y/280)", "b": "255*0.1+25*sin(2*PI*T/15+X/380+Y/280)"},
    ]
    return palettes[palette_idx % len(palettes)]


def create_subtitles(lines, duration, output_path):
    per_line = duration / max(len(lines), 1)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines):
            s = i * per_line
            e = min((i + 1) * per_line, duration)
            f.write(f"{i+1}\n")
            f.write(f"{s//3600:02.0f}:{(s%3600)//60:02.0f}:{s%60:06.3f} --> "
                    f"{e//3600:02.0f}:{(e%3600)//60:02.0f}:{e%60:06.3f}\n")
            f.write(f"{line}\n\n")


def build_shorts(script, audio_path, index, output_path):
    lines = script["lines"]
    duration = get_audio_duration(audio_path)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    subs = os.path.join(OUTPUT_DIR, f"subs_{index}.srt")
    create_subtitles(lines, duration, subs)

    pal = generate_geq_expression(index)
    palette_idx = index

    sub_style = (
        "FontName=DejaVuSans-Bold,FontSize=54,"
        "PrimaryCol=&H00FFFFFF,"
        "OutlineCol=&HFF000000,"
        "BorderStyle=3,Outline=5,Shadow=3,"
        "Alignment=2,MarginV=250,"
        "WrapStyle=1"
    )

    filter_chain = (
        f"geq=r='{pal['r']}':g='{pal['g']}':b='{pal['b']}'[bg];"
        f"[bg]subtitles={subs}:force_style='{sub_style}'[vid]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}:r=30",
        "-i", audio_path,
        "-filter_complex", filter_chain,
        "-map", "[vid]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        print(f"[video] ffmpeg error: {p.stderr[:400]}")
        return None

    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        kb = os.path.getsize(output_path) / 1024
        print(f"[video] OK {output_path} ({kb:.0f} KB)")
        return output_path
    print("[video] output file missing or too small")
    return None


def build_video(script, audio_path, media_files, output_path):
    return build_shorts(script, audio_path, 0, output_path)
