import asyncio
import os
from edge_tts import Communicate


def generate_audio(text_lines, output_path, voice="ru-RU-DariyaNeural"):
    full_text = " ".join(text_lines)

    async def _run():
        communicate = Communicate(full_text, voice)
        await communicate.save(output_path)

    asyncio.run(_run())
    return output_path


if __name__ == "__main__":
    from config import config
    lines = ["Это тестовый голос.", "Проверка работы синтеза речи."]
    out = r"C:\Users\amord\AppData\Local\Temp\opencode\yt-ai-autobot\output\test.mp3"
    generate_audio(lines, out)
    print(f"Audio saved: {out}")
