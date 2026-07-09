import os
import sys
import subprocess
import tempfile
import json
import re

HAS_GTTS = False
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    pass


def edge_tts_direct(text, output_path, voice="ru-RU-DariyaNeural"):
    """Direct HTTP call to Microsoft Edge TTS API (bypasses edge-tts library issues)."""
    import requests
    import uuid

    trusted_client_token = "6A92C9AB-68F8-4A40-A6C1-ED8D7E8E8E8E"
    wss_url = f"wss://speech.platform.bing.com/consumer/speech/synthesize/standard/v2?trustedclienttoken={trusted_client_token}&connectionId={uuid.uuid4().hex}"

    ssml = (
        f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
        f"xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='{voice[:5]}'>"
        f"<voice name='{voice}'>"
        f"<prosody rate='0%' pitch='0%'>{text}</prosody>"
        f"</voice></speak>"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
    }

    try:
        resp = requests.post(
            wss_url.replace("wss://", "https://"),
            data=ssml.encode("utf-8"),
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"[edge direct] {e}")
    return False


def edge_tts_library(text, output_path, voice="ru-RU-DariyaNeural"):
    try:
        import asyncio
        from edge_tts import Communicate

        async def _run():
            comm = Communicate(text, voice)
            await comm.save(output_path)

        asyncio.run(_run())
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"[edge lib] {e}")
    return False


def generate_audio(text_lines, output_path, voice="ru"):
    full_text = " ".join(text_lines)

    edge_voice = {
        "ru": "ru-RU-DariyaNeural",
        "en": "en-US-JennyNeural",
    }.get(voice[:2], "ru-RU-DariyaNeural")

    methods = []
    try:
        import requests
        methods.append(("edge_direct", lambda: edge_tts_direct(full_text, output_path, edge_voice)))
    except ImportError:
        pass

    if not methods:
        if HAS_GTTS:
            methods.append(("gtts", lambda: gtts_fallback(full_text, output_path, voice)))
        try:
            import asyncio
            from edge_tts import Communicate
            methods.append(("edge_lib", lambda: edge_tts_library(full_text, output_path, edge_voice)))
        except ImportError:
            pass

    for name, method in methods:
        print(f"[audio] trying {name}...")
        if method():
            print(f"[audio] {name} OK")
            return output_path
        print(f"[audio] {name} failed")

    if HAS_GTTS:
        print("[audio] falling back to gTTS")
        gtts_fallback(full_text, output_path, voice)
        return output_path

    raise RuntimeError("No TTS backend available")


def gtts_fallback(full_text, output_path, voice="ru"):
    lang = voice[:2] if len(voice) >= 2 else "ru"
    tts = gTTS(text=full_text, lang=lang, slow=False)
    tts.save(output_path)
