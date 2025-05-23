Cloner Bot
A Telegram bot for cloning files, managing requests, and hosting cloned bots. Created by @bot_paiyan_official.
Features

File Cloning: Clone files (photo, video, document, audio; max 2GB) to storage channels with success/failure messages (e.g., “✅ File cloned!”).
Custom Caption & Buttons: Set captions (e.g., 🎥 {filename}) and buttons (e.g., [Download ⬇️]) with validated links.
Clone Bot: Host new bots via [Clone Bot 🤖]; no user Render deployment.
Shortener Skip: Skip shortener for 1 hour post-verification.
Link Shorteners: Supports GPLinks, with submenu for GPLinks, ModijiURL, Other (ModijiURL/Other under development).
Dynamic Settings: Configure via buttons, stored in DB channel, with success/failure feedback.
Group Requests: Text as requests, hidden link previews, startid buttons.
User-Friendly: Nested buttons, emojis (e.g., “✅”, “📂”).
Anti-Ban: Private channels, redeployment script.
Render Deployment: Only TELEGRAM_TOKEN, ADMIN_IDS needed.

Setup

Clone Repo:git clone https://github.com/yourusername/cloner-bot.git
cd cloner_bot


Set Env Vars in Render:
TELEGRAM_TOKEN: From @BotFather.
ADMIN_IDS: Comma-separated admin IDs (e.g., 123456789,987654321).


Configure Shorteners:
Update config/shorteners.json with GPLinks API token.
Set via [Settings ⚙️] -> [Shortener 🔗] -> [GPLinks 🔗].


Deploy:
Create Render Web Service, point to repo, use Dockerfile.
Set env vars in Render dashboard.


Configure:
Run /start, use [Settings ⚙️] to set DB channel, log channel, shortener, etc.
Use [Clone Bot 🤖] to create hosted bots.



Folder Structure

bot.py: Main entry point.
handlers/: Command/callback handlers.
features/: Core features (shortener, cover image, etc.).
utils/: DB channel, logging, helpers.
config/: Settings and shortener configs.
scripts/: Anti-ban scripts.

Contact
Created by @bot_paiyan_official.
