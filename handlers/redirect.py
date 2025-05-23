import json
import logging

logger = logging.getLogger(__name__)

TOKEN_STORAGE_PATH = "/opt/render/project/src/data/tokens.json"

def get_tokens():
    """Load one-time link tokens from tokens.json. 🔗"""
    try:
        with open(TOKEN_STORAGE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"🚨 Failed to load tokens: {str(e)}")
        return {}

def save_tokens(tokens):
    """Save one-time link tokens to tokens.json. 💾"""
    try:
        with open(TOKEN_STORAGE_PATH, "w") as f:
            json.dump(tokens, f, indent=4)
    except Exception as e:
        logger.error(f"🚨 Failed to save tokens: {str(e)}")

def redirect_handler(token):
    """Handle the redirect for one-time GDToT links. 🌐
    Returns the GDToT URL if the token is valid, else None.
    """
    tokens = get_tokens()
    gdtot_url = tokens.get(token)

    if gdtot_url:
        # Invalidate the token after use (one-time link) 🔗
        tokens.pop(token, None)
        save_tokens(tokens)
        logger.info(f"ℹ️ Redirecting token {token} to {gdtot_url}")
        return gdtot_url
    else:
        logger.warning(f"🚫 Invalid or expired token: {token}")
        return None