import json
import os
from utils.logging_utils import log_error

SETTINGS_FILE = "config/settings.json"
CLONED_BOTS_FILE = "config/cloned_bots.json"
FILES_FILE = "config/files.json"

def load_json(file_path, default):
    """📂 Load JSON file with error handling."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return default
    except Exception as e:
        log_error(f"🚨 Error loading {file_path}: {str(e)}")
        return default

def save_json(file_path, data):
    """💾 Save JSON file with error handling."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log_error(f"🚨 Error saving {file_path}: {str(e)}")

def get_setting(key, default=None):
    """🔍 Get a setting from settings.json."""
    settings = load_json(SETTINGS_FILE, {})
    return settings.get(key, default)

def set_setting(key, value):
    """📝 Set a setting in settings.json."""
    settings = load_json(SETTINGS_FILE, {})
    settings[key] = value
    save_json(SETTINGS_FILE, settings)

def get_cloned_bots():
    """🤖 Get list of cloned bots."""
    return load_json(CLONED_BOTS_FILE, [])
