from utils.db_channel import load_json

SETTINGS_FILE = "config/settings.json"

def load_settings():
    """📂 Load bot settings (placeholder for future config)."""
    return load_json(SETTINGS_FILE, {})
