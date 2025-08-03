# Telegram Bot Configuration
# Edit this file with your settings

# Bot Token (Get from @BotFather)
BOT_TOKEN = "8489755531:AAGqXhAbc91XMSMUCDi6mudPFWiiCRLT1Jk"

# Admin User IDs (Add your Telegram user ID here)
ADMIN_IDS = [
    1664861755,  # Replace with your Telegram user ID
    # Add more admin IDs here
]

# Bot Settings
BOT_NAME = "@LinkRemoval24_Bot"
BOT_VERSION = "1.0.0"

# Group Settings
MAX_LINKS_PER_MESSAGE = 0  # No links allowed
ALLOWED_DOMAINS = []  # Empty list = no domains allowed

# Logging Settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "bot.log"

# Message Templates
BAN_MESSAGE = "🚫 {user} has been banned for sharing links.\n\nSharing any type of links is not allowed in this group."
CAPTION_BAN_MESSAGE = "🚫 {user} has been banned for sharing links in caption.\n\nSharing any type of links is not allowed in this group."

# Auto-delete settings
BAN_MESSAGE_DELETE_DELAY = 5  # Seconds before auto-deleting ban messages

# Spam Detection Settings
ENABLE_SPAM_DETECTION = True
ENABLE_LINK_DETECTION = True
ENABLE_ADMIN_PROTECTION = True

# Additional API Keys (if needed in future)
# OPENAI_API_KEY = "your_openai_key_here"
# GOOGLE_API_KEY = "your_google_key_here"
# DATABASE_URL = "your_database_url_here" 