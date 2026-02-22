import os
import logging
import sys
import random
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import time

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("CRITICAL: BOT_TOKEN environment variable is not set!")
    sys.exit(1)

# Owner Configuration
OWNER_ID = int(os.environ.get('OWNER_ID', '0'))  # Set your Telegram user ID here
if OWNER_ID == 0:
    logger.warning("OWNER_ID not set! Owner commands will be disabled.")

# Channel and Group Configuration
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', '@thehindigroup')
CHANNEL_LINK = os.environ.get('CHANNEL_LINK', 'https://t.me/thehindigroup')
GROUP_LINK = os.environ.get('GROUP_LINK', 'https://t.me/+Uc3SnOfhASEzZDcx')

# Clean channel username for display
if CHANNEL_USERNAME.startswith('@'):
    CHANNEL_USERNAME_CLEAN = CHANNEL_USERNAME[1:]
    CHANNEL_USERNAME_DISPLAY = CHANNEL_USERNAME
else:
    CHANNEL_USERNAME_CLEAN = CHANNEL_USERNAME
    CHANNEL_USERNAME_DISPLAY = f"@{CHANNEL_USERNAME}"

logger.info(f"Bot configured for channel: {CHANNEL_USERNAME_DISPLAY}")
logger.info(f"Channel link: {CHANNEL_LINK}")
logger.info(f"Group link: {GROUP_LINK}")
logger.info(f"Owner ID: {OWNER_ID}")

# Store user data
user_data = {}

# Store active giveaways
active_giveaways = {}

# Game data
games = {
    'dice': {
        'name': '🎲 Dice Roll',
        'description': 'Roll the dice and win up to 100 points!',
        'min_bet': 10,
        'max_bet': 100
    },
    'coin': {
        'name': '🪙 Coin Flip',
        'description': 'Heads or Tails? Double your points!',
        'min_bet': 5,
        'max_bet': 50
    },
    'slots': {
        'name': '🎰 Slot Machine',
        'description': 'Spin and win big jackpots!',
        'min_bet': 20,
        'max_bet': 200
    }
}

# Promotion messages
PROMO_MESSAGES = [
    "🔥 Welcome to AKASH Bot! The ultimate gaming experience awaits!",
    "🎮 Join AKASH for exclusive gaming content and tips!",
    "⚡ Level up your gaming skills with AKASH!",
    "🏆 Become a champion with AKASH community!",
    "🎯 Get pro gaming strategies only at AKASH!",
    "💫 New gaming content daily at AKASH!",
    "🚀 Join thousands of gamers at AKASH!",
    "🎲 Exclusive giveaways and contests at AKASH!",
]

# ==================== HELPER FUNCTIONS ====================

def is_owner(user_id):
    """Check if user is the bot owner."""
    return user_id == OWNER_ID

def get_user(user_id, username=None, first_name=None):
    """Get or create user in database."""
    if user_id not in user_data:
        user_data[user_id] = {
            'username': username,
            'first_name': first_name,
            'joined_date': datetime.now(),
            'points': 100,  # Starting bonus
            'referrals': 0,
            'last_checkin': None,
            'games_played': 0,
            'games_won': 0,
            'total_winnings': 0
        }
    return user_data[user_id]

def calculate_win_rate(user_id):
    """Calculate user's win rate percentage."""
    stats = user_data.get(user_id, {})
    games_played = stats.get('games_played', 0)
    games_won = stats.get('games_won', 0)
    
    if games_played == 0:
        return 0
    return round((games_won / games_played) * 100)

# ==================== FIXED OWNER COMMANDS ====================

async def owner_addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to add coins to a user.
    Usage: /addcoins @username amount  OR  /addcoins amount (reply to user)
    """
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    # CASE 1: Replying to a user's message
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        
        # Check if amount is provided
        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ Usage when replying: /addcoins amount\n"
                "Example: /addcoins 100 (when replying to someone)"
            )
            return
        
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number!")
            return
        
        # Get or create user
        user = get_user(target_id, target_user.username, target_user.first_name)
        
        # Add coins
        old_points = user['points']
        user['points'] = old_points + amount
        
        await update.message.reply_text(
            f"✅ Added {amount} coins to {target_user.first_name}\n"
            f"💰 Old balance: {old_points}\n"
            f"💰 New balance: {user['points']}"
        )
        
        # Notify the user
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎁 **You received {amount} coins from the owner!**\n"
                     f"Your new balance: {user['points']} coins",
                parse_mode='Markdown'
            )
        except:
            pass
        
        return
    
    # CASE 2: Adding coins to self (owner)
    if len(context.args) == 1 and context.args[0].isdigit():
        # Add coins to self
        amount = int(context.args[0])
        user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
        
        old_points = user['points']
        user['points'] = old_points + amount
        
        await update.message.reply_text(
            f"✅ Added {amount} coins to yourself\n"
            f"💰 Old balance: {old_points}\n"
            f"💰 New balance: {user['points']}"
        )
        return
    
    # CASE 3: Adding coins to another user by username
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ **Three ways to use this command:**\n\n"
            "1️⃣ **Reply to a user's message:**\n"
            "   `/addcoins 100` (while replying to them)\n\n"
            "2️⃣ **Add to yourself:**\n"
            "   `/addcoins 100`\n\n"
            "3️⃣ **Use username:**\n"
            "   `/addcoins @username 100`\n\n"
            "Examples:\n"
            "• `/addcoins 500` (reply to message)\n"
            "• `/addcoins 500` (add to self)\n"
            "• `/addcoins @john 500`",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0].replace('@', '').lower()
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number!")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    
    # Find user by username (case-insensitive)
    target_user_id = None
    target_user_data = None
    target_first_name = None
    
    for uid, data in user_data.items():
        db_username = data.get('username', '')
        if db_username and db_username.lower() == username:
            target_user_id = uid
            target_user_data = data
            target_first_name = data.get('first_name', username)
            break
    
    if not target_user_id:
        # Check if it might be the owner themselves
        if username == update.effective_user.username.lower():
            user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
            old_points = user['points']
            user['points'] = old_points + amount
            await update.message.reply_text(
                f"✅ Added {amount} coins to yourself\n"
                f"💰 Old balance: {old_points}\n"
                f"💰 New balance: {user['points']}"
            )
            return
        
        await update.message.reply_text(
            f"❌ User @{username} not found in database!\n"
            f"Make sure they have used the bot at least once with /start"
        )
        return
    
    # Add coins
    old_points = target_user_data.get('points', 0)
    target_user_data['points'] = old_points + amount
    
    await update.message.reply_text(
        f"✅ Added {amount} coins to @{username}\n"
        f"💰 Old balance: {old_points}\n"
        f"💰 New balance: {target_user_data['points']}"
    )
    
    # Notify the user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎁 **You received {amount} coins from the owner!**\n"
                 f"Your new balance: {target_user_data['points']} coins",
            parse_mode='Markdown'
        )
    except:
        pass

async def owner_removecoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to remove coins from a user."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    # Replying to a user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        
        if len(context.args) < 1:
            await update.message.reply_text("Usage when replying: /removecoins amount")
            return
        
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Amount must be a number!")
            return
        
        if target_id not in user_data:
            await update.message.reply_text("User not found in database!")
            return
        
        old_points = user_data[target_id].get('points', 0)
        new_points = max(0, old_points - amount)
        user_data[target_id]['points'] = new_points
        
        await update.message.reply_text(
            f"✅ Removed {amount} coins from {target_user.first_name}\n"
            f"Old: {old_points} → New: {new_points}"
        )
        return
    
    # Regular username method
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /removecoins @username amount")
        return
    
    username = context.args[0].replace('@', '').lower()
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Amount must be a number!")
        return
    
    for uid, data in user_data.items():
        db_username = data.get('username', '')
        if db_username and db_username.lower() == username:
            old_points = data.get('points', 0)
            new_points = max(0, old_points - amount)
            data['points'] = new_points
            await update.message.reply_text(f"✅ Removed {amount} coins from @{username}")
            return
    
    await update.message.reply_text(f"❌ User @{username} not found!")

# ==================== GROUP GAME COMMANDS ====================

async def group_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play dice game in group - /dice [bet]"""
    user = update.effective_user
    user_id = user.id
    
    # Check if in group
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command only works in groups!")
        return
    
    # Check bet amount
    bet = 10  # Default bet
    if context.args:
        try:
            bet = int(context.args[0])
            if bet < 10 or bet > 100:
                await update.message.reply_text("Bet must be between 10 and 100 points!")
                return
        except:
            await update.message.reply_text("Usage: /dice [bet amount]")
            return
    
    # Get user data
    user = get_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if user['points'] < bet:
        await update.message.reply_text(
            f"❌ {update.effective_user.first_name}, you don't have enough points!\n"
            f"Your points: {user['points']}\n"
            f"Required: {bet}"
        )
        return
    
    # Deduct bet
    user['points'] -= bet
    user['games_played'] += 1
    
    # Roll dice
    roll = random.randint(1, 6)
    
    # Determine winnings
    if roll <= 3:
        winnings = 0
        result_text = "❌ Lost!"
    elif roll <= 5:
        winnings = bet * 2
        result_text = "✅ Won double!"
        user['games_won'] += 1
        user['total_winnings'] += winnings
    else:
        winnings = bet * 3
        result_text = "🎉 JACKPOT! Won TRIPLE!"
        user['games_won'] += 1
        user['total_winnings'] += winnings
    
    if winnings > 0:
        user['points'] += winnings
    
    dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    
    result_message = (
        f"🎲 **Group Dice Game** 🎲\n\n"
        f"Player: {update.effective_user.first_name}\n"
        f"Rolled: {dice_faces[roll-1]} {roll}\n"
        f"{result_text}\n\n"
        f"Bet: {bet}\n"
        f"Won: {winnings}\n"
        f"New Balance: {user['points']}"
    )
    
    await update.message.reply_text(result_message, parse_mode='Markdown')

async def group_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play coin flip in group - /coin [heads/tails] [bet]"""
    user = update.effective_user
    user_id = user.id
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command only works in groups!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /coin [heads/tails] [bet]\nExample: /coin heads 10")
        return
    
    choice = context.args[0].lower()
    if choice not in ['heads', 'tails']:
        await update.message.reply_text("Choose 'heads' or 'tails'!")
        return
    
    try:
        bet = int(context.args[1])
        if bet < 5 or bet > 50:
            await update.message.reply_text("Bet must be between 5 and 50 points!")
            return
    except:
        await update.message.reply_text("Bet must be a number!")
        return
    
    user = get_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if user['points'] < bet:
        await update.message.reply_text(f"❌ You don't have enough points! Your points: {user['points']}")
        return
    
    user['points'] -= bet
    user['games_played'] += 1
    
    flip = random.choice(['heads', 'tails'])
    
    if choice == flip:
        winnings = bet * 2
        user['points'] += winnings
        user['games_won'] += 1
        user['total_winnings'] += winnings
        result = "✅ WIN!"
    else:
        winnings = 0
        result = "❌ Lose!"
    
    result_message = (
        f"🪙 **Group Coin Flip** 🪙\n\n"
        f"Player: {update.effective_user.first_name}\n"
        f"Choice: {choice.capitalize()}\n"
        f"Result: {flip.capitalize()}\n"
        f"{result}\n\n"
        f"Bet: {bet}\n"
        f"Won: {winnings}\n"
        f"New Balance: {user['points']}"
    )
    
    await update.message.reply_text(result_message, parse_mode='Markdown')

async def group_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play slots in group - /slots [bet]"""
    user = update.effective_user
    user_id = user.id
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command only works in groups!")
        return
    
    bet = 20  # Default bet
    if context.args:
        try:
            bet = int(context.args[0])
            if bet < 20 or bet > 200:
                await update.message.reply_text("Bet must be between 20 and 200 points!")
                return
        except:
            await update.message.reply_text("Usage: /slots [bet amount]")
            return
    
    user = get_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if user['points'] < bet:
        await update.message.reply_text(f"❌ You don't have enough points! Your points: {user['points']}")
        return
    
    user['points'] -= bet
    user['games_played'] += 1
    
    symbols = ['🍒', '🍋', '💎', '7️⃣']
    result = [random.choice(symbols) for _ in range(3)]
    
    multiplier = 0
    if result[0] == result[1] == result[2]:
        if result[0] == '🍒':
            multiplier = 3
        elif result[0] == '🍋':
            multiplier = 5
        elif result[0] == '💎':
            multiplier = 10
        elif result[0] == '7️⃣':
            multiplier = 20
    
    if multiplier > 0:
        winnings = bet * multiplier
        user['points'] += winnings
        user['games_won'] += 1
        user['total_winnings'] += winnings
        result_text = f"🎉 JACKPOT! {multiplier}x WINNER!"
    else:
        winnings = 0
        result_text = "❌ Try again!"
    
    result_message = (
        f"🎰 **Group Slots** 🎰\n\n"
        f"Player: {update.effective_user.first_name}\n"
        f"{' | '.join(result)}\n"
        f"{result_text}\n\n"
        f"Bet: {bet}\n"
        f"Won: {winnings}\n"
        f"New Balance: {user['points']}"
    )
    
    await update.message.reply_text(result_message, parse_mode='Markdown')

async def group_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check balance in group - /balance"""
    if update.effective_chat.type not in ['group', 'supergroup']:
        return
    
    user = get_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    
    await update.message.reply_text(
        f"💰 **{update.effective_user.first_name}'s Balance** 💰\n\n"
        f"Points: {user['points']}\n"
        f"Games Played: {user['games_played']}\n"
        f"Games Won: {user['games_won']}\n"
        f"Win Rate: {calculate_win_rate(update.effective_user.id)}%",
        parse_mode='Markdown'
    )

# ==================== GIVEAWAY HANDLERS ====================

async def owner_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to start a giveaway."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /giveaway amount [duration_minutes]")
        return
    
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Amount must be a number!")
        return
    
    duration = 60
    if len(context.args) > 1:
        try:
            duration = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Duration must be a number!")
            return
    
    giveaway_id = str(int(time.time()))
    end_time = datetime.now() + timedelta(minutes=duration)
    
    active_giveaways[giveaway_id] = {
        'amount': amount,
        'end_time': end_time,
        'participants': [],
        'creator_id': update.effective_user.id
    }
    
    keyboard = [
        [InlineKeyboardButton("🎁 Join Giveaway", callback_data=f"giveaway_{giveaway_id}")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    giveaway_text = (
        f"🎉 **GIVEAWAY!** 🎉\n\n"
        f"Prize: {amount} coins\n"
        f"Duration: {duration} minutes\n"
        f"Ends: {end_time.strftime('%H:%M:%S')}\n\n"
        f"Click below to enter!"
    )
    
    await update.message.reply_text("✅ Giveaway created!")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=giveaway_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ==================== EXISTING FUNCTIONS (Keep all your existing functions) ====================

# [Keep all your existing functions here: start, games_menu, game_dice, play_dice, 
#  game_coin, play_coin, game_slots, play_slots, game_stats, leaderboard, 
#  button_callback, back_to_menu, promo, checkin, handle_referral, error_handler, post_init]

# I'll include the critical ones that need updates:

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Initialize user data
    user = get_user(user_id, user.username, user.first_name)
    
    # Create welcome message with buttons
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🎮 PLAY GAMES 🎮", callback_data='games_menu')],
        [InlineKeyboardButton("💰 Earn Points", callback_data='earn')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats')],
        [InlineKeyboardButton("🤝 Refer Friends", callback_data='refer')],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data='leaderboard')],
    ]
    
    # Add owner button if user is owner
    if is_owner(user_id):
        keyboard.append([InlineKeyboardButton("👑 Owner Panel", callback_data='owner_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎮 **Welcome to AKASH Bot!** 🎮\n\n"
        f"Hello {user['first_name']}! 👋\n\n"
        f"**Your Stats:**\n"
        f"• Points: {user['points']}\n"
        f"• Games Played: {user['games_played']}\n"
        f"• Win Rate: {calculate_win_rate(user_id)}%\n\n"
        f"**Group Games:**\n"
        f"• /dice [bet] - Play dice in group\n"
        f"• /coin [heads/tails] [bet] - Flip coin\n"
        f"• /slots [bet] - Play slots\n"
        f"• /balance - Check your balance\n\n"
        f"👇 **Click PLAY GAMES to start!** 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show games menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_points = user_data.get(user_id, {}).get('points', 0)
    
    keyboard = [
        [InlineKeyboardButton("🎲 Dice Roll", callback_data='game_dice')],
        [InlineKeyboardButton("🪙 Coin Flip", callback_data='game_coin')],
        [InlineKeyboardButton("🎰 Slot Machine", callback_data='game_slots')],
        [InlineKeyboardButton("📊 My Game Stats", callback_data='game_stats')],
        [InlineKeyboardButton("🔙 Main Menu", callback_data='back_to_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    games_text = (
        f"🎮 **GAMES MENU** 🎮\n\n"
        f"Your Points: **{user_points}** 💰\n\n"
        f"**Available Games:**\n"
        f"🎲 Dice Roll - Win up to 100 points\n"
        f"🪙 Coin Flip - Double your points\n"
        f"🎰 Slot Machine - Win big jackpots\n\n"
        f"**Select a game to play:**"
    )
    
    await query.edit_message_text(
        games_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show owner panel."""
    query = update.callback_query
    await query.answer()
    
    if not is_owner(query.from_user.id):
        await query.edit_message_text("❌ Access denied!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Bot Statistics", callback_data='owner_stats')],
        [InlineKeyboardButton("🎁 Create Giveaway", callback_data='owner_create_giveaway')],
        [InlineKeyboardButton("💰 Add Coins", callback_data='owner_addcoins')],
        [InlineKeyboardButton("🔙 Main Menu", callback_data='back_to_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👑 **Owner Control Panel** 👑\n\n"
        "Select an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot."""
    try:
        logger.info(f"Starting AKASH Bot with token: {BOT_TOKEN[:10]}...")
        
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .build()
        )
        
        # Private chat commands
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("promo", promo))
        application.add_handler(CommandHandler("checkin", checkin))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        
        # Group game commands
        application.add_handler(CommandHandler("dice", group_dice))
        application.add_handler(CommandHandler("coin", group_coin))
        application.add_handler(CommandHandler("slots", group_slots))
        application.add_handler(CommandHandler("balance", group_balance))
        
        # Owner commands
        application.add_handler(CommandHandler("addcoins", owner_addcoins))
        application.add_handler(CommandHandler("removecoins", owner_removecoins))
        application.add_handler(CommandHandler("giveaway", owner_giveaway))
        application.add_handler(CommandHandler("endgiveaway", owner_endgiveaway))
        application.add_handler(CommandHandler("stats", owner_stats))
        application.add_handler(CommandHandler("broadcast", owner_broadcast))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Add message handler for referral links
        application.add_handler(MessageHandler(filters.Regex(r'^/start \d+$'), handle_referral))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        logger.info("🤖 AKASH Bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
