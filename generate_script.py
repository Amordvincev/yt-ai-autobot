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
    template = pick_template()

    hook = random.choice(template["hooks"])
    fact = template["fact"]
    outro = random.choice(template["outros"])

    lines = [f"{hook} {fact} {outro}"]

    return {
        "title": template["title"],
        "tags": template["tags"],
        "lines": lines,
    }
