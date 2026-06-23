import json
import os

SETTINGS_PATH = os.path.expanduser("~/.vibecode_translator_settings.json")
LEGACY_SETTINGS_PATH = os.path.expanduser("~/.vibecode_reader_settings.json")

DEFAULT_SETTINGS = {
    "provider": "claude",
    "api_key": "",
    "model": "",
    "language": "en",  # "en" = English, "zh" = 繁體中文
}

def load_settings():
    path = SETTINGS_PATH if os.path.exists(SETTINGS_PATH) else LEGACY_SETTINGS_PATH
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        merged = {**DEFAULT_SETTINGS, **data}
        # Always sanitize the key on load — guards against any dirty value on disk
        merged["api_key"] = "".join(merged.get("api_key", "").split())
        return merged
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
