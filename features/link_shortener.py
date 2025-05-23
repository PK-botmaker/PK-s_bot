import requests
import urllib.parse
from utils.logging_utils import log_error
from utils.db_channel import get_setting

async def shorten_link(url: str) -> str:
    """Shorten a URL using configured shortener."""
    try:
        shortener = await get_setting("shortener", {"type": "none", "api_key": ""})
        shortener_type = shortener.get("type", "none")
        api_key = shortener.get("api_key", "")

        if shortener_type == "gplinks" and api_key:
            encoded_url = urllib.parse.quote(url)
            api_url = f"https://api.gplinks.com/api?api={api_key}&url={encoded_url}&alias=CustomAlias&format=text"
            response = requests.get(api_url)
            response.raise_for_status()
            short_url = response.text.strip()
            if short_url.startswith("http"):
                logger.info(f"✅ GPLinks shortened URL: {short_url}")
                return short_url
            else:
                await log_error(f"Invalid GPLinks response: {short_url}")
                logger.info(f"⚠️ GPLinks failed, using original URL: {url}")
                return url
        elif shortener_type == "bitly" and api_key:
            headers = {"Authorization": f"Bearer {api_key}"}
            data = {"long_url": url}
            response = requests.post("https://api-ssl.bitly.com/v4/shorten", headers=headers, json=data)
            response.raise_for_status()
            short_url = response.json()["link"]
            logger.info(f"✅ Bitly shortened URL: {short_url}")
            return short_url
        else:
            logger.info(f"✅ No shortener, using original URL: {url}")
            return url
    except Exception as e:
        await log_error(f"Shortener error: {str(e)}")
        logger.info(f"⚠️ Shortener failed, using original URL: {url}")
        return url
