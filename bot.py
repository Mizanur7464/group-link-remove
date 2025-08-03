import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from spam_filter import spam_filter
from config import *

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    filename=LOG_FILE
)
logger = logging.getLogger(__name__)

# Admin commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "I'm your group management bot. I can help you:\n"
        "• Filter spam and ads\n"
        "• Remove unwanted links\n"
        "• Keep your group clean\n\n"
        "Use /help to see all commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
🤖 <b>Group Management Bot Commands:</b>

<b>Admin Commands:</b>
/start - Start the bot
/help - Show this help message
/status - Show bot status
/ban @username - Ban a user
/unban @username - Unban a user
/warn @username - Warn a user
/clear - Clear all warnings

<b>Bot Features:</b>
• Automatically detects spam links
• Filters advertisement messages
• Removes unwanted content
• Warns users for violations
• Bans repeat offenders
• Auto-deletes ban messages after 5 seconds

<b>Spam Detection:</b>
• URL links (with exceptions)
• Money-making schemes
• Investment scams
• Adult content
• Gambling ads
• And many more patterns...

Made with ❤️ for your group safety!
    """
    await update.message.reply_html(help_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status."""
    chat_id = update.effective_chat.id
    status_text = f"""
📊 <b>Bot Status:</b>

Chat ID: {chat_id}
Active: ✅
Spam Filtering: ✅
Link Detection: ✅
Admin Protection: ✅
Auto-Delete: ✅ ({BAN_MESSAGE_DELETE_DELAY}s)

Bot is running and protecting your group! 🛡️
    """
    await update.message.reply_html(status_text)

async def delete_message_after_delay(bot, chat_id: int, message_id: int, delay: int = 5):
    """Delete a message after a specified delay."""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Auto-deleted message {message_id} from chat {chat_id} after {delay} seconds")
    except Exception as e:
        logger.error(f"Error auto-deleting message: {e}")

def is_spam_message(text: str) -> bool:
    """Check if a message contains spam patterns."""
    if not text:
        return False
    
    # Use advanced spam filter
    analysis = spam_filter.analyze_message(text)
    return analysis['is_spam']

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and filter spam."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Skip if message is from bot or admin
    if user.is_bot:
        return
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(chat.id, user.id)
    if chat_member.status in ['creator', 'administrator']:
        return  # Allow admin messages
    
    # Check for links in text messages
    if message.text and len(spam_filter.extract_urls(message.text)) > 0:
        try:
            # Delete the message
            await message.delete()
            
            # Ban user for sharing links
            await context.bot.ban_chat_member(chat.id, user.id)
            ban_msg = BAN_MESSAGE.format(user=user.mention_html())
            
            # Send ban message and auto-delete after configured delay
            sent_message = await context.bot.send_message(
                chat_id=chat.id,
                text=ban_msg,
                parse_mode='HTML'
            )
            
            # Schedule message deletion after configured delay
            asyncio.create_task(
                delete_message_after_delay(
                    context.bot, chat.id, sent_message.message_id, 
                    BAN_MESSAGE_DELETE_DELAY
                )
            )
            
            logger.info(f"User {user.id} banned for sharing links in chat {chat.id}")
            
        except Exception as e:
            logger.error(f"Error handling link message: {e}")
    
    # Check for links in captions
    elif message.caption and len(spam_filter.extract_urls(message.caption)) > 0:
        try:
            await message.delete()
            
            # Ban user for sharing links
            await context.bot.ban_chat_member(chat.id, user.id)
            ban_msg = CAPTION_BAN_MESSAGE.format(user=user.mention_html())
            
            # Send ban message and auto-delete after configured delay
            sent_message = await context.bot.send_message(
                chat_id=chat.id,
                text=ban_msg,
                parse_mode='HTML'
            )
            
            # Schedule message deletion after configured delay
            asyncio.create_task(
                delete_message_after_delay(
                    context.bot, chat.id, sent_message.message_id, 
                    BAN_MESSAGE_DELETE_DELAY
                )
            )
            
            logger.info(f"User {user.id} banned for sharing links in caption in chat {chat.id}")
            
        except Exception as e:
            logger.error(f"Error handling link caption: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from the group."""
    if not context.args:
        await update.message.reply_text("Usage: /ban @username")
        return
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text("❌ You need admin privileges to use this command.")
        return
    
    username = context.args[0].replace('@', '')
    try:
        # Get user by username
        user = await context.bot.get_chat(username)
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ {username} has been banned from the group.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error banning user: {e}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user from the group."""
    if not context.args:
        await update.message.reply_text("Usage: /unban @username")
        return
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text("❌ You need admin privileges to use this command.")
        return
    
    username = context.args[0].replace('@', '')
    try:
        user = await context.bot.get_chat(username)
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ {username} has been unbanned from the group.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error unbanning user: {e}")

def main():
    """Start the bot."""
    # Get token from config or environment variable
    token = BOT_TOKEN if BOT_TOKEN != "your_bot_token_here" else os.getenv('TELEGRAM_BOT_TOKEN')
    if not token or token == "your_bot_token_here":
        logger.error("No token provided! Set BOT_TOKEN in config.py or TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    
    # Add message handler for spam filtering
    application.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 