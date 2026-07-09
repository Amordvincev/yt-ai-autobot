import os
import subprocess
import sys

HAS_GTTS = False
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    pass

HAS_EDGE = False
try:
    import asyncio
    from edge_tts import Communicate
    HAS_EDGE = True
except ImportError:
    pass


def generate_audio(text_lines, output_path, voice="ru"):
    full_text = " ".join(text_lines)

    if HAS_EDGE:
        edge_voice = {
            "ru": "ru-RU-DariyaNeural",
            "en": "en-US-JennyNeural",
        }.get(voice[:2], "ru-RU-DariyaNeural")

        async def _run():
            comm = Communicate(full_text, edge_voice)
            await comm.save(output_path)

        try:
            asyncio.run(_run())
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"[audio] Edge TTS: {output_path}")
                return output_path
        except Exception as e:
            print(f"[audio] Edge TTS failed: {e}")

    if HAS_GTTS:
        lang = voice[:2] if len(voice) >= 2 else "ru"
        tts = gTTS(text=full_text, lang=lang, slow=False)
        tts.save(output_path)
        print(f"[audio] gTTS: {output_path}")
        return output_path

    if sys.platform == "win32":
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(full_text)
            print("[audio] Windows TTS - no file saved, using gTTS fallback")
        except ImportError:
            pass

    raise RuntimeError("No TTS backend available (pip install gtts edge-tts)")
