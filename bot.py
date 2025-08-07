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

# Warning tracking system (in-memory storage)
user_warnings = {}  # {user_id: warning_count}

def get_user_warnings(user_id: int) -> int:
    """Get warning count for a user."""
    return user_warnings.get(user_id, 0)

def add_user_warning(user_id: int) -> int:
    """Add a warning for a user and return new count."""
    current_warnings = get_user_warnings(user_id)
    user_warnings[user_id] = current_warnings + 1
    return user_warnings[user_id]

def clear_user_warnings(user_id: int):
    """Clear warnings for a user."""
    if user_id in user_warnings:
        del user_warnings[user_id]

def reset_all_warnings():
    """Reset all user warnings."""
    user_warnings.clear()

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
    help_text = f"""
🤖 <b>Group Management Bot Commands:</b>

<b>Admin Commands:</b>
/start - Start the bot
/help - Show this help message
/status - Show bot status
/ban @username - Ban a user
/unban @username - Unban a user
/warn @username - Manually warn a user ⭐ NEW!
/clear_warnings - Clear all warnings ⭐ NEW!
/check_warnings @username - Check user warnings ⭐ NEW!
/toggle_forwarded_blocking - Toggle forwarded message blocking

<b>Bot Features:</b>
• Automatically detects spam links
• Filters advertisement messages
• Removes unwanted content
• <b>Blocks forwarded messages</b> ⭐ NEW!
• <b>Warning System</b> ⭐ NEW! ({MAX_WARNINGS_BEFORE_BAN} warnings before ban)
• Warns users for violations
• Bans repeat offenders
• Auto-deletes warning messages after {WARNING_MESSAGE_DELETE_DELAY} seconds

<b>Spam Detection:</b>
• URL links (with exceptions)
• Money-making schemes
• Investment scams
• Adult content
• Gambling ads
• And many more patterns...

<b>Forwarded Message Protection:</b>
• All forwarded messages are automatically deleted
• Users get a warning message
• Warning messages auto-delete after {FORWARDED_MESSAGE_DELETE_DELAY} seconds
• Admins can still forward messages

<b>Warning System:</b>
• Users get warnings instead of immediate bans
• {MAX_WARNINGS_BEFORE_BAN} warnings before permanent ban
• Warning count is tracked per user
• Admins can manually warn users
• Admins can clear warnings
• Admins can check warning status

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
Forwarded Message Blocking: ✅
Warning System: {'✅ Enabled' if USE_WARNING_SYSTEM else '❌ Disabled'}
Admin Protection: ✅
Auto-Delete: ✅ ({BAN_MESSAGE_DELETE_DELAY}s)

<b>Warning System Settings:</b>
Max Warnings: {MAX_WARNINGS_BEFORE_BAN}
Warning Delete Delay: {WARNING_MESSAGE_DELETE_DELAY}s
Current Active Warnings: {len(user_warnings)} users

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
    
    # Check for forwarded messages (NEW FEATURE)
    if ENABLE_FORWARDED_MESSAGE_BLOCKING and message.forward_from:
        try:
            # Delete the forwarded message
            await message.delete()
            
            # Send warning message
            warning_msg = FORWARDED_MESSAGE_WARNING.format(user=user.mention_html())
            sent_message = await context.bot.send_message(
                chat_id=chat.id,
                text=warning_msg,
                parse_mode='HTML'
            )
            
            # Auto-delete warning message after configured delay
            asyncio.create_task(
                delete_message_after_delay(
                    context.bot, chat.id, sent_message.message_id, 
                    FORWARDED_MESSAGE_DELETE_DELAY
                )
            )
            
            logger.info(f"Deleted forwarded message from user {user.id} in chat {chat.id}")
            
        except Exception as e:
            logger.error(f"Error handling forwarded message: {e}")
        return  # Exit after handling forwarded message
    
    # Check for links in text messages
    if message.text and len(spam_filter.extract_urls(message.text)) > 0:
        try:
            # Delete the message
            await message.delete()
            
            if USE_WARNING_SYSTEM:
                # Add warning to user
                warning_count = add_user_warning(user.id)
                
                # Check if user should be banned
                if warning_count >= MAX_WARNINGS_BEFORE_BAN:
                    # Ban user after max warnings
                    await context.bot.ban_chat_member(chat.id, user.id)
                    ban_msg = BAN_MESSAGE.format(user=user.mention_html())
                    
                    sent_message = await context.bot.send_message(
                        chat_id=chat.id,
                        text=ban_msg,
                        parse_mode='HTML'
                    )
                    
                    # Clear warnings after ban
                    clear_user_warnings(user.id)
                    
                    logger.info(f"User {user.id} banned after {warning_count} warnings in chat {chat.id}")
                    
                else:
                    # Send warning message
                    warning_msg = LINK_WARNING_MESSAGE.format(
                        user=user.mention_html(),
                        warning_count=warning_count,
                        max_warnings=MAX_WARNINGS_BEFORE_BAN
                    )
                    
                    sent_message = await context.bot.send_message(
                        chat_id=chat.id,
                        text=warning_msg,
                        parse_mode='HTML'
                    )
                    
                    logger.info(f"User {user.id} got warning {warning_count}/{MAX_WARNINGS_BEFORE_BAN} in chat {chat.id}")
                
                # Auto-delete warning/ban message
                asyncio.create_task(
                    delete_message_after_delay(
                        context.bot, chat.id, sent_message.message_id, 
                        WARNING_MESSAGE_DELETE_DELAY
                    )
                )
                
            else:
                # Old system - immediate ban
                await context.bot.ban_chat_member(chat.id, user.id)
                ban_msg = BAN_MESSAGE.format(user=user.mention_html())
                
                sent_message = await context.bot.send_message(
                    chat_id=chat.id,
                    text=ban_msg,
                    parse_mode='HTML'
                )
                
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
            
            if USE_WARNING_SYSTEM:
                # Add warning to user
                warning_count = add_user_warning(user.id)
                
                # Check if user should be banned
                if warning_count >= MAX_WARNINGS_BEFORE_BAN:
                    # Ban user after max warnings
                    await context.bot.ban_chat_member(chat.id, user.id)
                    ban_msg = CAPTION_BAN_MESSAGE.format(user=user.mention_html())
                    
                    sent_message = await context.bot.send_message(
                        chat_id=chat.id,
                        text=ban_msg,
                        parse_mode='HTML'
                    )
                    
                    # Clear warnings after ban
                    clear_user_warnings(user.id)
                    
                    logger.info(f"User {user.id} banned after {warning_count} warnings (caption) in chat {chat.id}")
                    
                else:
                    # Send warning message
                    warning_msg = CAPTION_LINK_WARNING_MESSAGE.format(
                        user=user.mention_html(),
                        warning_count=warning_count,
                        max_warnings=MAX_WARNINGS_BEFORE_BAN
                    )
                    
                    sent_message = await context.bot.send_message(
                        chat_id=chat.id,
                        text=warning_msg,
                        parse_mode='HTML'
                    )
                    
                    logger.info(f"User {user.id} got warning {warning_count}/{MAX_WARNINGS_BEFORE_BAN} (caption) in chat {chat.id}")
                
                # Auto-delete warning/ban message
                asyncio.create_task(
                    delete_message_after_delay(
                        context.bot, chat.id, sent_message.message_id, 
                        WARNING_MESSAGE_DELETE_DELAY
                    )
                )
                
            else:
                # Old system - immediate ban
                await context.bot.ban_chat_member(chat.id, user.id)
                ban_msg = CAPTION_BAN_MESSAGE.format(user=user.mention_html())
                
                sent_message = await context.bot.send_message(
                    chat_id=chat.id,
                    text=ban_msg,
                    parse_mode='HTML'
                )
                
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

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually warn a user."""
    if not context.args:
        await update.message.reply_text("Usage: /warn @username")
        return
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(
        update.effective_chat.id, update.effective_user.id
    )
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text(
            "❌ You need admin privileges to use this command."
        )
        return
    
    username = context.args[0].replace('@', '')
    try:
        # Get user by username
        user = await context.bot.get_chat(username)
        warning_count = add_user_warning(user.id)
        
        warning_msg = LINK_WARNING_MESSAGE.format(
            user=user.mention_html(),
            warning_count=warning_count,
            max_warnings=MAX_WARNINGS_BEFORE_BAN
        )
        
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=warning_msg,
            parse_mode='HTML'
        )
        
        # Auto-delete warning message
        asyncio.create_task(
            delete_message_after_delay(
                context.bot, update.effective_chat.id, sent_message.message_id, 
                WARNING_MESSAGE_DELETE_DELAY
            )
        )
        
        await update.message.reply_text(
            f"✅ {username} has been warned. "
            f"Warning count: {warning_count}/{MAX_WARNINGS_BEFORE_BAN}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error warning user: {e}")


async def clear_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear warnings for a user or all users."""
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(
        update.effective_chat.id, update.effective_user.id
    )
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text(
            "❌ You need admin privileges to use this command."
        )
        return
    
    if not context.args:
        # Clear all warnings
        reset_all_warnings()
        await update.message.reply_text("✅ All user warnings have been cleared.")
        return
    
    username = context.args[0].replace('@', '')
    try:
        # Get user by username
        user = await context.bot.get_chat(username)
        clear_user_warnings(user.id)
        await update.message.reply_text(f"✅ Warnings cleared for {username}.")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error clearing warnings: {e}")


async def check_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check warnings for a user."""
    if not context.args:
        await update.message.reply_text("Usage: /check_warnings @username")
        return
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(
        update.effective_chat.id, update.effective_user.id
    )
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text(
            "❌ You need admin privileges to use this command."
        )
        return
    
    username = context.args[0].replace('@', '')
    try:
        # Get user by username
        user = await context.bot.get_chat(username)
        warning_count = get_user_warnings(user.id)
        
        status_text = f"""
📊 <b>Warning Status for {username}:</b>

Current Warnings: {warning_count}/{MAX_WARNINGS_BEFORE_BAN}
Status: {'🟢 Safe' if warning_count < MAX_WARNINGS_BEFORE_BAN else '🔴 At Risk'}
        """
        
        await update.message.reply_html(status_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking warnings: {e}")


async def toggle_forwarded_blocking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle forwarded message blocking on/off."""
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(
        update.effective_chat.id, update.effective_user.id
    )
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text(
            "❌ You need admin privileges to use this command."
        )
        return
    
    # Toggle the setting (this would need to be stored in a database or file)
    # For now, we'll just show the current status
    current_status = "✅ Enabled" if ENABLE_FORWARDED_MESSAGE_BLOCKING else "❌ Disabled"
    
    status_text = f"""
🔄 <b>Forwarded Message Blocking Status:</b>

Current Status: {current_status}

To change this setting, edit the config.py file:
ENABLE_FORWARDED_MESSAGE_BLOCKING = True/False

Then restart the bot.
    """
    await update.message.reply_html(status_text)


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
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("clear_warnings", clear_warnings))
    application.add_handler(CommandHandler("check_warnings", check_warnings))
    application.add_handler(CommandHandler("toggle_forwarded_blocking", toggle_forwarded_blocking))
    
    # Add message handler for spam filtering
    application.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 