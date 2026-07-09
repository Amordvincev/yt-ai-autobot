import json
import random
import os

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template_scripts.json")


def load_templates():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_template():
    templates = load_templates()
    return random.choice(templates)


def fetch_or_generate_script(config):
    niche = config["niche"]
    language = config["language"]

    template = pick_template()
    lines = template["lines"]
    title = template["title"]
    tags = template["tags"]

    return {
        "title": title,
        "tags": tags,
        "lines": lines,
    }


if __name__ == "__main__":
    from config import config
    script = fetch_or_generate_script(config)
    print(json.dumps(script, ensure_ascii=False, indent=2))
