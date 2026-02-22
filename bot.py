import os
import logging
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import random

# Enable logging - FIXED THE SYNTAX ERROR HERE
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration with error handling
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("CRITICAL: BOT_TOKEN environment variable is not set!")
    logger.error("Please set BOT_TOKEN in Railway environment variables")
    sys.exit(1)

BOT_USERNAME = "AnkitHunterBot"
CHANNEL_USERNAME = "@ankithuntercomback"  # Change this to your channel
GROUP_LINK = "https://t.me/ankithuntergroup"  # Change this to your group

# Store user data (in production, use database)
user_data = {}

# Promotion messages
PROMO_MESSAGES = [
    "🔥 Welcome to Ankit Hunter Comback! The ultimate gaming experience awaits!",
    "🎮 Join Ankit Hunter Comback for exclusive gaming content and tips!",
    "⚡ Level up your gaming skills with Ankit Hunter Comback!",
    "🏆 Become a champion with Ankit Hunter Comback community!",
    "🎯 Get pro gaming strategies only at Ankit Hunter Comback!",
    "💫 New gaming content daily at Ankit Hunter Comback!",
    "🚀 Join thousands of gamers at Ankit Hunter Comback!",
    "🎲 Exclusive giveaways and contests at Ankit Hunter Comback!",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Initialize user data
    if user_id not in user_data:
        user_data[user_id] = {
            'username': user.username,
            'first_name': user.first_name,
            'joined_date': datetime.now(),
            'points': 0,
            'referrals': 0,
            'last_checkin': None
        }
    
    # Create welcome message with buttons
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🎮 Play Games", callback_data='games')],
        [InlineKeyboardButton("💰 Earn Points", callback_data='earn')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats')],
        [InlineKeyboardButton("🤝 Refer Friends", callback_data='refer')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎮 **Welcome to Ankit Hunter Comback!** 🎮\n\n"
        f"Hello {user.first_name}! 👋\n\n"
        f"Get ready for the ultimate gaming experience with Ankit Hunter Comback!\n\n"
        f"**What we offer:**\n"
        f"• Exclusive gaming content\n"
        f"• Pro tips and strategies\n"
        f"• Daily giveaways\n"
        f"• Gaming community\n"
        f"• Earn points and rewards\n\n"
        f"Use the buttons below to get started!"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send promotional message about Ankit Hunter Comback."""
    # Select random promo message
    promo_text = random.choice(PROMO_MESSAGES)
    
    # Create promotional keyboard
    keyboard = [
        [InlineKeyboardButton("🎮 Join Now", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("👥 Community", url=GROUP_LINK)],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    full_promo = (
        f"{promo_text}\n\n"
        f"🔗 **Join Ankit Hunter Comback today!**\n"
        f"Channel: {CHANNEL_USERNAME}\n"
        f"Group: {GROUP_LINK}\n\n"
        f"Don't miss out on the action! 🎯"
    )
    
    await update.message.reply_text(
        full_promo,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callback queries."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == 'games':
        games_text = (
            "🎮 **Available Games** 🎮\n\n"
            "• Ankit Hunter Adventure\n"
            "• Comback Racing\n"
            "• Hunter Puzzle\n"
            "• Weekly Tournaments\n\n"
            "More games coming soon!"
        )
        await query.edit_message_text(games_text, parse_mode='Markdown')
        
    elif query.data == 'earn':
        points = user_data.get(user_id, {}).get('points', 0)
        earn_text = (
            "💰 **Earn Points** 💰\n\n"
            "**Ways to earn:**\n"
            "• Invite friends (+50 points each)\n"
            "• Daily check-in (+10 points)\n"
            "• Share content (+20 points)\n"
            "• Participate in events (+100 points)\n"
            "• Top referrals bonus (+500 points)\n\n"
            f"Your current points: {points}\n\n"
            "Use /checkin to claim your daily points!"
        )
        await query.edit_message_text(earn_text, parse_mode='Markdown')
        
    elif query.data == 'stats':
        user_stats = user_data.get(user_id, {})
        stats_text = (
            f"📊 **Your Stats** 📊\n\n"
            f"• Username: @{user_stats.get('username', 'N/A')}\n"
            f"• Points: {user_stats.get('points', 0)}\n"
            f"• Referrals: {user_stats.get('referrals', 0)}\n"
            f"• Joined: {user_stats.get('joined_date', datetime.now()).strftime('%Y-%m-%d')}\n"
            f"• Rank: {get_user_rank(user_stats.get('points', 0))}"
        )
        await query.edit_message_text(stats_text, parse_mode='Markdown')
        
    elif query.data == 'refer':
        user_stats = user_data.get(user_id, {})
        bot_username = (await context.bot.get_me()).username
        refer_text = (
            "🤝 **Refer Friends** 🤝\n\n"
            f"Share this link to earn points:\n"
            f"`https://t.me/{bot_username}?start={user_id}`\n\n"
            "**Benefits:**\n"
            "• 50 points per referral\n"
            "• Bonus for top referrers\n"
            "• Exclusive rewards\n\n"
            f"Total referrals: {user_stats.get('referrals', 0)}"
        )
        await query.edit_message_text(refer_text, parse_mode='Markdown')
        return
    
    # Add back button
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Choose an option:", reply_markup=reply_markup)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🎮 Play Games", callback_data='games')],
        [InlineKeyboardButton("💰 Earn Points", callback_data='earn')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats')],
        [InlineKeyboardButton("🤝 Refer Friends", callback_data='refer')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🎮 **Ankit Hunter Comback Menu** 🎮\n\nChoose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Daily check-in to earn points."""
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_data:
        user_data[user_id] = {
            'username': user.username,
            'first_name': user.first_name,
            'joined_date': datetime.now(),
            'points': 0,
            'referrals': 0,
            'last_checkin': None
        }
    
    last_checkin = user_data[user_id].get('last_checkin')
    today = datetime.now().date()
    
    if last_checkin and last_checkin.date() == today:
        await update.message.reply_text("❌ You've already checked in today! Come back tomorrow.")
        return
    
    # Award points
    user_data[user_id]['points'] += 10
    user_data[user_id]['last_checkin'] = datetime.now()
    
    await update.message.reply_text(
        f"✅ Daily check-in successful!\n"
        f"You earned 10 points!\n"
        f"Total points: {user_data[user_id]['points']}"
    )

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle referral links."""
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])
        new_user_id = update.effective_user.id
        
        if referrer_id != new_user_id:
            # Initialize if not exists
            if referrer_id not in user_data:
                user_data[referrer_id] = {
                    'username': None,
                    'first_name': None,
                    'joined_date': datetime.now(),
                    'points': 0,
                    'referrals': 0,
                    'last_checkin': None
                }
            
            user_data[referrer_id]['points'] += 50
            user_data[referrer_id]['referrals'] += 1
            
            # Welcome the new user
            await start(update, context)
            
            # Try to notify referrer (if they've started the bot)
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 Great news! Someone joined using your referral link!\n"
                         f"You earned 50 points! Total points: {user_data[referrer_id]['points']}"
                )
            except:
                pass  # Referrer hasn't started the bot

def get_user_rank(points):
    """Get user rank based on points."""
    if points < 100:
        return "🥉 Bronze"
    elif points < 500:
        return "🥈 Silver"
    elif points < 1000:
        return "🥇 Gold"
    else:
        return "👑 Platinum"

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

async def post_init(application: Application):
    """Post initialization hook."""
    bot_info = await application.bot.get_me()
    logger.info(f"Bot started: @{bot_info.username}")

def main():
    """Start the bot."""
    try:
        # Create application with proper error handling
        logger.info(f"Starting bot with token: {BOT_TOKEN[:10]}...")
        
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .build()
        )
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("promo", promo))
        application.add_handler(CommandHandler("checkin", checkin))
        
        # Add callback query handlers
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
        
        # Add message handler for referral links
        application.add_handler(MessageHandler(filters.Regex(r'^/start \d+$'), handle_referral))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start bot
        logger.info("🤖 Ankit Hunter Comback Bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
