# Telegram Bot Configuration
# Edit this file with your settings

# Bot Token (Get from @BotFather)
BOT_TOKEN = "8489755531:AAGqXhAbc91XMSMUCDi6mudPFWiiCRLT1Jk"

# Admin User IDs (Add your Telegram user ID here)
ADMIN_IDS: list[int] = [
    1664861755,  # Replace with your Telegram user ID
    # Add more admin IDs here
]

# Bot Settings
BOT_NAME = "@LinkRemoval24_Bot"
BOT_VERSION = "1.0.0"

# Group Settings
MAX_LINKS_PER_MESSAGE = 0  # No links allowed
ALLOWED_DOMAINS: list[str] = []  # Empty list = no domains allowed

# Warning System Settings
USE_WARNING_SYSTEM = True  # Use warnings instead of bans
MAX_WARNINGS_BEFORE_BAN = 3  # Ban after 3 warnings
WARNING_MESSAGE_DELETE_DELAY = 5  # Warning messages auto-delete delay

# Forwarded Message Settings
BLOCK_FORWARDED_MESSAGES = True  # Block all forwarded messages
# Seconds before auto-deleting notifications
FORWARDED_MESSAGE_DELETE_DELAY = 5

# Logging Settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "bot.log"

# Message Templates
BAN_MESSAGE = (
    "🚫 {user} has been banned for sharing links.\n\n"
    "Sharing any type of links is not allowed in this group."
)
CAPTION_BAN_MESSAGE = (
    "🚫 {user} has been banned for sharing links in caption.\n\n"
    "Sharing any type of links is not allowed in this group."
)
FORWARDED_MESSAGE_WARNING = (
    "⚠️ {user}, forwarded messages are not allowed in this group.\n\n"
    "Please send original messages only."
)
LINK_WARNING_MESSAGE = (
    "⚠️ {user}, sharing links is not allowed in this group.\n\n"
    "Warning {warning_count}/{max_warnings}. "
    "You will be banned after {max_warnings} warnings."
)
CAPTION_LINK_WARNING_MESSAGE = (
    "⚠️ {user}, sharing links in captions is not allowed in this group.\n\n"
    "Warning {warning_count}/{max_warnings}. "
    "You will be banned after {max_warnings} warnings."
)

# Auto-delete settings
BAN_MESSAGE_DELETE_DELAY = 5  # Seconds before auto-deleting ban messages

# Spam Detection Settings
ENABLE_SPAM_DETECTION = True
ENABLE_LINK_DETECTION = True
ENABLE_ADMIN_PROTECTION = True
ENABLE_FORWARDED_MESSAGE_BLOCKING = True
ENABLE_WARNING_SYSTEM = True

# Additional API Keys (if needed in future)
# OPENAI_API_KEY = "your_openai_key_here"
# GOOGLE_API_KEY = "your_google_key_here"
# DATABASE_URL = "your_database_url_here" 