import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


class Config:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        defaults = {
            "niche": "facts",
            "language": "ru",
            "video_duration_min": 120,
            "video_duration_max": 300,
            "schedule_time": "08:00",
            "timezone": "UTC",
            "pexels_api_key": "",
            "openai_api_key": "",
            "youtube_channel_id": "",
            "youtube_client_secret": "",
            "youtube_refresh_token": "",
            "voice": "ru-RU-DariyaNeural",
            "music": "ambient",
            "output_dir": "output",
            "assets_dir": "assets",
        }
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                defaults.update(loaded)
        return defaults

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def __getitem__(self, key):
        return self.data.get(key, "")

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)


config = Config()
