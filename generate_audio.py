import os
import sys

IS_GITHUB = os.environ.get("GITHUB_ACTIONS") == "true"
IS_WINDOWS = sys.platform == "win32"

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


def _gtts(text_lines, output_path, voice="ru"):
    lang = voice[:2] if len(voice) >= 2 else "ru"
    tts = gTTS(text=" ".join(text_lines), lang=lang, slow=False)
    tts.save(output_path)
    return output_path


def _edge(text_lines, output_path, voice="ru"):
    edge_voice = {
        "ru": "ru-RU-DariyaNeural",
        "en": "en-US-JennyNeural",
    }.get(voice[:2], "ru-RU-DariyaNeural")

    import asyncio
    from edge_tts import Communicate

    async def _run():
        comm = Communicate(" ".join(text_lines), edge_voice)
        await comm.save(output_path)

    asyncio.run(_run())
    return output_path


def generate_audio(text_lines, output_path, voice="ru"):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if IS_GITHUB or not IS_WINDOWS or not HAS_EDGE:
        if HAS_GTTS:
            return _gtts(text_lines, output_path, voice)
        if HAS_EDGE:
            return _edge(text_lines, output_path, voice)

    if IS_WINDOWS and HAS_EDGE:
        try:
            return _edge(text_lines, output_path, voice)
        except Exception:
            pass
        if HAS_GTTS:
            return _gtts(text_lines, output_path, voice)

    if HAS_GTTS:
        return _gtts(text_lines, output_path, voice)

    raise RuntimeError("No TTS available (pip install gtts or edge-tts)")
