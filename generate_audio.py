import os

_HAS_GTTS = False
try:
    from gtts import gTTS
    _HAS_GTTS = True
except ImportError:
    pass

_HAS_EDGE = False
try:
    import asyncio
    from edge_tts import Communicate
    _HAS_EDGE = True
except ImportError:
    pass


def generate_audio(text_lines, output_path, voice="ru"):
    full_text = " ".join(text_lines)

    if _HAS_GTTS:
        lang = voice[:2] if len(voice) >= 2 else "ru"
        tts = gTTS(text=full_text, lang=lang, slow=False)
        tts.save(output_path)
        return output_path

    if _HAS_EDGE:
        import asyncio
        from edge_tts import Communicate

        async def _run():
            comm = Communicate(full_text, voice)
            await comm.save(output_path)

        try:
            asyncio.run(_run())
            return output_path
        except Exception:
            print("[audio] Edge TTS failed")
            raise

    raise RuntimeError("No TTS backend available (install gTTS or edge-tts)")
