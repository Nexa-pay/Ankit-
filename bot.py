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
OWNER_ID = int(os.environ.get('6950501653', '0'))  # Set your Telegram user ID here
if OWNER_ID == 0:
    logger.warning("6950501653 not set! Owner commands will be disabled.")

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
    CHANNEL_USERNAME_DISPLAY = f"@{CHANNEL_USENAME}"

logger.info(f"Bot configured for channel: {https://t.me/vellickor}")
logger.info(f"Owner ID: {6950501653}")

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
    },
    'number': {
        'name': '🔢 Number Guess',
        'description': 'Guess the number (1-10) and win 3x your bet!',
        'min_bet': 15,
        'max_bet': 150
    },
    'rps': {
        'name': '✂️ Rock Paper Scissors',
        'description': 'Play against the bot and win!',
        'min_bet': 10,
        'max_bet': 100
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

# ==================== OWNER COMMANDS ====================

def is_owner(user_id):
    """Check if user is the bot owner."""
    return user_id == OWNER_ID

async def owner_addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to add coins to a user.
    Usage: /addcoins @username amount
    """
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    # Check arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /addcoins @username amount\n"
            "Example: /addcoins @john 100"
        )
        return
    
    username = context.args[0].replace('@', '')
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number!")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    
    # Find user by username
    target_user_id = None
    target_user_data = None
    
    for uid, data in user_data.items():
        if data.get('username', '').lower() == username.lower():
            target_user_id = uid
            target_user_data = data
            break
    
    if not target_user_id:
        await update.message.reply_text(f"❌ User @{username} not found in database!")
        return
    
    # Add coins
    old_points = target_user_data.get('points', 0)
    target_user_data['points'] = old_points + amount
    
    await update.message.reply_text(
        f"✅ Added {amount} coins to @{username}\n"
        f"Old balance: {old_points}\n"
        f"New balance: {target_user_data['points']}"
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
    """Owner command to remove coins from a user.
    Usage: /removecoins @username amount
    """
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /removecoins @username amount\n"
            "Example: /removecoins @john 50"
        )
        return
    
    username = context.args[0].replace('@', '')
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number!")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    
    # Find user by username
    target_user_id = None
    target_user_data = None
    
    for uid, data in user_data.items():
        if data.get('username', '').lower() == username.lower():
            target_user_id = uid
            target_user_data = data
            break
    
    if not target_user_id:
        await update.message.reply_text(f"❌ User @{username} not found in database!")
        return
    
    # Remove coins
    old_points = target_user_data.get('points', 0)
    new_points = max(0, old_points - amount)  # Don't go below 0
    target_user_data['points'] = new_points
    
    await update.message.reply_text(
        f"✅ Removed {amount} coins from @{username}\n"
        f"Old balance: {old_points}\n"
        f"New balance: {new_points}"
    )

async def owner_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to start a giveaway.
    Usage: /giveaway amount [duration_minutes]
    """
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /giveaway amount [duration_minutes]\n"
            "Example: /giveaway 500 60"
        )
        return
    
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number!")
        return
    
    duration = 60  # Default 60 minutes
    if len(context.args) > 1:
        try:
            duration = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Duration must be a number (minutes)!")
            return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    
    # Create giveaway
    giveaway_id = str(int(time.time()))
    end_time = datetime.now() + timedelta(minutes=duration)
    
    active_giveaways[giveaway_id] = {
        'amount': amount,
        'end_time': end_time,
        'participants': [],
        'creator_id': update.effective_user.id
    }
    
    # Create announcement
    keyboard = [
        [InlineKeyboardButton("🎁 Join Giveaway", callback_data=f"giveaway_{giveaway_id}")],
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    giveaway_text = (
        f"🎉 **GIVEAWAY ANNOUNCEMENT!** 🎉\n\n"
        f"**Prize:** {amount} coins\n"
        f"**Duration:** {duration} minutes\n"
        f"**Ends:** {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"**How to enter:**\n"
        f"1. Click the button below\n"
        f"2. Join our channel\n"
        f"3. Wait for the winner announcement!\n\n"
        f"Good luck everyone! 🍀"
    )
    
    await update.message.reply_text(
        "✅ Giveaway created successfully!"
    )
    
    # Broadcast to all users (or send to a channel)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=giveaway_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def owner_endgiveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to end a giveaway and pick a winner."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    if not active_giveaways:
        await update.message.reply_text("❌ No active giveaways!")
        return
    
    # Show active giveaways
    text = "**Active Giveaways:**\n\n"
    keyboard = []
    
    for gid, giveaway in active_giveaways.items():
        text += f"ID: `{gid}`\n"
        text += f"Prize: {giveaway['amount']} coins\n"
        text += f"Participants: {len(giveaway['participants'])}\n"
        text += f"Ends: {giveaway['end_time'].strftime('%H:%M:%S')}\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"End Giveaway {gid[:8]}...", 
            callback_data=f"endgiveaway_{gid}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def owner_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to see bot statistics."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    total_users = len(user_data)
    total_points = sum(data.get('points', 0) for data in user_data.values())
    total_games = sum(data.get('games_played', 0) for data in user_data.values())
    active_giveaways_count = len(active_giveaways)
    
    # Top users
    top_users = sorted(user_data.items(), key=lambda x: x[1].get('points', 0), reverse=True)[:5]
    
    stats_text = (
        f"📊 **BOT STATISTICS** 📊\n\n"
        f"**General:**\n"
        f"• Total Users: {total_users}\n"
        f"• Total Points: {total_points}\n"
        f"• Games Played: {total_games}\n"
        f"• Active Giveaways: {active_giveaways_count}\n\n"
        f"**Top 5 Users:**\n"
    )
    
    for i, (uid, data) in enumerate(top_users, 1):
        name = data.get('first_name', 'Unknown')
        points = data.get('points', 0)
        stats_text += f"{i}. {name} - {points} points\n"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def owner_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command to broadcast message to all users."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ This command is only for bot owner!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /broadcast your message here\n"
            "Example: /broadcast New event starting soon!"
        )
        return
    
    message = ' '.join(context.args)
    
    await update.message.reply_text(
        f"📢 Broadcasting to {len(user_data)} users...\n"
        f"Message: {message}"
    )
    
    success = 0
    failed = 0
    
    for user_id in user_data.keys():
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 **Broadcast from Owner:**\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
            time.sleep(0.05)  # Small delay to avoid rate limits
        except:
            failed += 1
    
    await update.message.reply_text(
        f"✅ Broadcast completed!\n"
        f"✓ Sent: {success}\n"
        f"✗ Failed: {failed}"
    )

# ==================== GIVEAWAY HANDLERS ====================

async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE, giveaway_id: str):
    """Handle user joining a giveaway."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or "Anonymous"
    
    if giveaway_id not in active_giveaways:
        await query.edit_message_text(
            "❌ This giveaway has ended or doesn't exist!"
        )
        return
    
    giveaway = active_giveaways[giveaway_id]
    
    # Check if already joined
    if user_id in giveaway['participants']:
        await query.edit_message_text(
            "❌ You've already joined this giveaway!",
            show_alert=True
        )
        return
    
    # Add to participants
    giveaway['participants'].append(user_id)
    
    await query.edit_message_text(
        f"✅ You've successfully joined the giveaway!\n\n"
        f"Prize: {giveaway['amount']} coins\n"
        f"Total participants: {len(giveaway['participants'])}\n\n"
        f"Good luck! 🍀"
    )

async def end_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE, giveaway_id: str):
    """End a giveaway and pick a winner (owner only)."""
    query = update.callback_query
    await query.answer()
    
    if not is_owner(query.from_user.id):
        await query.edit_message_text("❌ Only owner can end giveaways!")
        return
    
    if giveaway_id not in active_giveaways:
        await query.edit_message_text("❌ Giveaway not found!")
        return
    
    giveaway = active_giveaways[giveaway_id]
    
    if not giveaway['participants']:
        await query.edit_message_text(
            "❌ No participants in this giveaway!\n"
            "Giveaway cancelled."
        )
        del active_giveaways[giveaway_id]
        return
    
    # Pick random winner
    winner_id = random.choice(giveaway['participants'])
    winner_data = user_data.get(winner_id, {})
    winner_name = winner_data.get('first_name', 'Unknown')
    winner_username = winner_data.get('username', 'No username')
    
    # Award prize
    if winner_id in user_data:
        user_data[winner_id]['points'] = user_data[winner_id].get('points', 0) + giveaway['amount']
    
    # Announce winner
    winner_text = (
        f"🎉 **GIVEAWAY WINNER ANNOUNCEMENT!** 🎉\n\n"
        f"**Prize:** {giveaway['amount']} coins\n"
        f"**Total Participants:** {len(giveaway['participants'])}\n\n"
        f"**Winner:** {winner_name} (@{winner_username})\n\n"
        f"Congratulations! 🎊"
    )
    
    await query.edit_message_text(
        winner_text,
        parse_mode='Markdown'
    )
    
    # Notify winner
    try:
        await context.bot.send_message(
            chat_id=winner_id,
            text=f"🎉 **Congratulations! You won the giveaway!** 🎉\n\n"
                 f"You received {giveaway['amount']} coins!\n"
                 f"Your new balance: {user_data[winner_id]['points']}",
            parse_mode='Markdown'
        )
    except:
        pass
    
    # Remove giveaway
    del active_giveaways[giveaway_id]

# ==================== GAME FUNCTIONS ====================

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
            'points': 100,  # Starting bonus
            'referrals': 0,
            'last_checkin': None,
            'games_played': 0,
            'games_won': 0,
            'total_winnings': 0
        }
    
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
        f"Hello {user.first_name}! 👋\n\n"
        f"Get ready for the ultimate gaming experience with AKASH!\n\n"
        f"**What we offer:**\n"
        f"• 🎲 5+ Exciting Games\n"
        f"• 💰 Win Real Points\n"
        f"• 🏆 Daily Tournaments\n"
        f"• 🎁 Weekly Giveaways\n"
        f"• 🤝 Referral Bonuses\n\n"
        f"**Your Stats:**\n"
        f"• Points: {user_data[user_id]['points']}\n"
        f"• Games Played: {user_data[user_id]['games_played']}\n"
        f"• Win Rate: {calculate_win_rate(user_id)}%\n\n"
        f"**Our Community:**\n"
        f"📢 Channel: {CHANNEL_USERNAME_DISPLAY}\n"
        f"👥 Group: {GROUP_LINK}\n\n"
        f"👇 **Click PLAY GAMES to start!** 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
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
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='owner_broadcast')],
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
        [InlineKeyboardButton("🔢 Number Guess", callback_data='game_number')],
        [InlineKeyboardButton("✂️ Rock Paper Scissors", callback_data='game_rps')],
        [InlineKeyboardButton("🏆 Daily Tournament", callback_data='tournament')],
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
        f"🎰 Slot Machine - Win big jackpots\n"
        f"🔢 Number Guess - 3x your bet\n"
        f"✂️ Rock Paper Scissors - Beat the bot\n\n"
        f"**Select a game to play:**"
    )
    
    await query.edit_message_text(
        games_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ==================== GAME IMPLEMENTATIONS ====================

async def game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dice roll game menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_points = user_data.get(user_id, {}).get('points', 0)
    
    keyboard = [
        [InlineKeyboardButton("💰 Bet 10 Points", callback_data='dice_10')],
        [InlineKeyboardButton("💰 Bet 25 Points", callback_data='dice_25')],
        [InlineKeyboardButton("💰 Bet 50 Points", callback_data='dice_50')],
        [InlineKeyboardButton("💰 Bet 100 Points", callback_data='dice_100')],
        [InlineKeyboardButton("🔙 Back to Games", callback_data='games_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    dice_text = (
        f"🎲 **DICE ROLL** 🎲\n\n"
        f"Your Points: **{user_points}**\n\n"
        f"**How to play:**\n"
        f"• Choose your bet amount\n"
        f"• Roll higher than 3 to win!\n"
        f"• Roll 1-3: You lose\n"
        f"• Roll 4-6: You win double!\n"
        f"• Roll 6: You win triple!\n\n"
        f"Select your bet amount:"
    )
    
    await query.edit_message_text(
        dice_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def play_dice(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    """Play dice game with specific bet."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'points': 100, 'games_played': 0, 'games_won': 0, 'total_winnings': 0}
    
    if user_data[user_id]['points'] < bet:
        await query.edit_message_text(
            f"❌ You don't have enough points!\n"
            f"Your points: {user_data[user_id]['points']}\n"
            f"Required: {bet}\n\n"
            f"Earn more points with /checkin or referrals!",
            parse_mode='Markdown'
        )
        return
    
    # Deduct bet
    user_data[user_id]['points'] -= bet
    user_data[user_id]['games_played'] += 1
    
    # Roll dice (1-6)
    roll = random.randint(1, 6)
    
    # Determine winnings
    if roll <= 3:
        winnings = 0
        result_text = "❌ You lost!"
        win = False
    elif roll <= 5:
        winnings = bet * 2
        result_text = "✅ You won double!"
        win = True
    else:
        winnings = bet * 3
        result_text = "🎉 JACKPOT! You won TRIPLE!"
        win = True
    
    if winnings > 0:
        user_data[user_id]['points'] += winnings
        user_data[user_id]['games_won'] += 1
        user_data[user_id]['total_winnings'] += winnings
    
    dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    
    result_message = (
        f"🎲 **DICE ROLL RESULT** 🎲\n\n"
        f"You rolled: **{dice_faces[roll-1]} {roll}**\n\n"
        f"{result_text}\n\n"
        f"Bet: **{bet}** points\n"
        f"Won: **{winnings}** points\n"
        f"New Balance: **{user_data[user_id]['points']}** points\n\n"
        f"Games Played: {user_data[user_id]['games_played']}\n"
        f"Win Rate: {calculate_win_rate(user_id)}%"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎲 Play Again", callback_data='game_dice')],
        [InlineKeyboardButton("🔙 Games Menu", callback_data='games_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Coin flip game menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_points = user_data.get(user_id, {}).get('points', 0)
    
    keyboard = [
        [InlineKeyboardButton("Bet 10 Points - Heads", callback_data='coin_10_heads')],
        [InlineKeyboardButton("Bet 10 Points - Tails", callback_data='coin_10_tails')],
        [InlineKeyboardButton("Bet 25 Points - Heads", callback_data='coin_25_heads')],
        [InlineKeyboardButton("Bet 25 Points - Tails", callback_data='coin_25_tails')],
        [InlineKeyboardButton("Bet 50 Points - Heads", callback_data='coin_50_heads')],
        [InlineKeyboardButton("Bet 50 Points - Tails", callback_data='coin_50_tails')],
        [InlineKeyboardButton("🔙 Back to Games", callback_data='games_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    coin_text = (
        f"🪙 **COIN FLIP** 🪙\n\n"
        f"Your Points: **{user_points}**\n\n"
        f"**How to play:**\n"
        f"• Choose Heads or Tails\n"
        f"• Win double your bet!\n\n"
        f"Make your choice:"
    )
    
    await query.edit_message_text(
        coin_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def play_coin(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int, choice: str):
    """Play coin flip game."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'points': 100, 'games_played': 0, 'games_won': 0, 'total_winnings': 0}
    
    if user_data[user_id]['points'] < bet:
        await query.edit_message_text(
            f"❌ You don't have enough points!\n"
            f"Your points: {user_data[user_id]['points']}",
            parse_mode='Markdown'
        )
        return
    
    user_data[user_id]['points'] -= bet
    user_data[user_id]['games_played'] += 1
    
    flip = random.choice(['Heads', 'Tails'])
    coin_emoji = "🪙 Heads" if flip == 'Heads' else "🪙 Tails"
    
    if choice.lower() == flip.lower():
        winnings = bet * 2
        user_data[user_id]['points'] += winnings
        user_data[user_id]['games_won'] += 1
        user_data[user_id]['total_winnings'] += winnings
        result_text = "✅ **YOU WIN!**"
    else:
        winnings = 0
        result_text = "❌ **You lose!**"
    
    result_message = (
        f"🪙 **COIN FLIP RESULT** 🪙\n\n"
        f"Coin landed: **{coin_emoji}**\n"
        f"Your choice: **{choice}**\n\n"
        f"{result_text}\n\n"
        f"Bet: **{bet}** points\n"
        f"Won: **{winnings}** points\n"
        f"New Balance: **{user_data[user_id]['points']}** points"
    )
    
    keyboard = [
        [InlineKeyboardButton("🪙 Play Again", callback_data='game_coin')],
        [InlineKeyboardButton("🔙 Games Menu", callback_data='games_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def game_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Slot machine game menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_points = user_data.get(user_id, {}).get('points', 0)
    
    keyboard = [
        [InlineKeyboardButton("💰 Bet 20 Points", callback_data='slots_20')],
        [InlineKeyboardButton("💰 Bet 50 Points", callback_data='slots_50')],
        [InlineKeyboardButton("💰 Bet 100 Points", callback_data='slots_100')],
        [InlineKeyboardButton("💰 Bet 200 Points", callback_data='slots_200')],
        [InlineKeyboardButton("🔙 Back to Games", callback_data='games_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    slots_text = (
        f"🎰 **SLOT MACHINE** 🎰\n\n"
        f"Your Points: **{user_points}**\n\n"
        f"**Winning Combinations:**\n"
        f"🍒🍒🍒 - Win 3x\n"
        f"🍋🍋🍋 - Win 5x\n"
        f"💎💎💎 - Win 10x\n"
        f"7️⃣7️⃣7️⃣ - JACKPOT 20x!\n\n"
        f"Select your bet:"
    )
    
    await query.edit_message_text(
        slots_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def play_slots(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    """Play slot machine."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'points': 100, 'games_played': 0, 'games_won': 0, 'total_winnings': 0}
    
    if user_data[user_id]['points'] < bet:
        await query.edit_message_text(
            f"❌ You don't have enough points!\n"
            f"Your points: {user_data[user_id]['points']}",
            parse_mode='Markdown'
        )
        return
    
    user_data[user_id]['points'] -= bet
    user_data[user_id]['games_played'] += 1
    
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
        user_data[user_id]['points'] += winnings
        user_data[user_id]['games_won'] += 1
        user_data[user_id]['total_winnings'] += winnings
        result_text = f"🎉 **JACKPOT! {multiplier}x WINNER!**"
    else:
        winnings = 0
        result_text = "❌ **Try again!**"
    
    result_message = (
        f"🎰 **SLOT MACHINE RESULT** 🎰\n\n"
        f"{' | '.join(result)}\n\n"
        f"{result_text}\n\n"
        f"Bet: **{bet}** points\n"
        f"Won: **{winnings}** points\n"
        f"Multiplier: **{multiplier}x**\n"
        f"New Balance: **{user_data[user_id]['points']}** points"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎰 Play Again", callback_data='game_slots')],
        [InlineKeyboardButton("🔙 Games Menu", callback_data='games_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def game_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's game statistics."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    stats = user_data.get(user_id, {})
    
    games_played = stats.get('games_played', 0)
    games_won = stats.get('games_won', 0)
    win_rate = calculate_win_rate(user_id)
    total_winnings = stats.get('total_winnings', 0)
    points = stats.get('points', 0)
    
    stats_text = (
        f"📊 **YOUR GAME STATISTICS** 📊\n\n"
        f"🎮 Games Played: **{games_played}**\n"
        f"🏆 Games Won: **{games_won}**\n"
        f"📈 Win Rate: **{win_rate}%**\n"
        f"💰 Total Winnings: **{total_winnings}**\n"
        f"💵 Current Balance: **{points}**\n\n"
        f"**Achievements:**\n"
    )
    
    achievements = []
    if games_played >= 10:
        achievements.append("🏅 Novice Player - Played 10 games")
    if games_played >= 50:
        achievements.append("🎖️ Experienced - Played 50 games")
    if win_rate >= 50:
        achievements.append("⭐ Sharp Shooter - 50%+ Win Rate")
    if total_winnings >= 1000:
        achievements.append("💰 High Roller - Won 1000+ points")
    
    if achievements:
        stats_text += "\n".join([f"• {a}" for a in achievements])
    else:
        stats_text += "• Play more games to earn achievements!"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Games", callback_data='games_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def calculate_win_rate(user_id):
    """Calculate user's win rate percentage."""
    stats = user_data.get(user_id, {})
    games_played = stats.get('games_played', 0)
    games_won = stats.get('games_won', 0)
    
    if games_played == 0:
        return 0
    return round((games_won / games_played) * 100)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top players leaderboard."""
    query = update.callback_query
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1].get('points', 0), reverse=True)
    top_users = sorted_users[:10]
    
    leaderboard_text = "🏆 **TOP PLAYERS LEADERBOARD** 🏆\n\n"
    
    if not top_users:
        leaderboard_text += "No players yet! Be the first to play!"
    else:
        for i, (user_id, data) in enumerate(top_users, 1):
            name = data.get('first_name', 'Anonymous')
            points = data.get('points', 0)
            wins = data.get('games_won', 0)
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🎮"
            leaderboard_text += f"{medal} **{i}.** {name}\n"
            leaderboard_text += f"   Points: {points} | Wins: {wins}\n\n"
    
    if query:
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            leaderboard_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

# ==================== CALLBACK HANDLER ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks."""
    query = update.callback_query
    data = query.data
    
    # Owner panel
    if data == 'owner_panel':
        await owner_panel(update, context)
    elif data == 'owner_stats':
        await owner_stats(update, context)
    elif data == 'owner_create_giveaway':
        await query.edit_message_text(
            "To create a giveaway, use:\n"
            "`/giveaway amount minutes`\n\n"
            "Example: `/giveaway 500 60`",
            parse_mode='Markdown'
        )
    elif data == 'owner_broadcast':
        await query.edit_message_text(
            "To broadcast a message, use:\n"
            "`/broadcast your message here`",
            parse_mode='Markdown'
        )
    elif data == 'owner_addcoins':
        await query.edit_message_text(
            "To add coins to a user, use:\n"
            "`/addcoins @username amount`\n\n"
            "Example: `/addcoins @john 100`",
            parse_mode='Markdown'
        )
    
    # Giveaway handling
    elif data.startswith('giveaway_'):
        giveaway_id = data.replace('giveaway_', '')
        await join_giveaway(update, context, giveaway_id)
    elif data.startswith('endgiveaway_'):
        giveaway_id = data.replace('endgiveaway_', '')
        await end_giveaway(update, context, giveaway_id)
    
    # Games menu
    elif data == 'games_menu':
        await games_menu(update, context)
    elif data == 'game_dice':
        await game_dice(update, context)
    elif data == 'game_coin':
        await game_coin(update, context)
    elif data == 'game_slots':
        await game_slots(update, context)
    elif data == 'game_stats':
        await game_stats(update, context)
    
    # Dice bets
    elif data.startswith('dice_'):
        bet = int(data.split('_')[1])
        await play_dice(update, context, bet)
    
    # Coin flip bets
    elif data.startswith('coin_'):
        parts = data.split('_')
        bet = int(parts[1])
        choice = parts[2]
        await play_coin(update, context, bet, choice)
    
    # Slots bets
    elif data.startswith('slots_'):
        bet = int(data.split('_')[1])
        await play_slots(update, context, bet)
    
    # Leaderboard
    elif data == 'leaderboard':
        await leaderboard(update, context)
    
    # Other menus
    elif data == 'earn':
        points = user_data.get(query.from_user.id, {}).get('points', 0)
        earn_text = (
            "💰 **Earn Points** 💰\n\n"
            "**Ways to earn:**\n"
            "• Invite friends (+50 points each)\n"
            "• Daily check-in (+10 points)\n"
            "• Win games (varies)\n"
            "• Participate in giveaways (BIG prizes!)\n"
            "• Top players bonus (+500 points)\n\n"
            f"Your current points: {points}\n\n"
            "Use /checkin to claim your daily points!"
        )
        await query.edit_message_text(earn_text, parse_mode='Markdown')
        
    elif data == 'stats':
        user_stats = user_data.get(query.from_user.id, {})
        stats_text = (
            f"📊 **Your Stats** 📊\n\n"
            f"• Username: @{user_stats.get('username', 'N/A')}\n"
            f"• Points: {user_stats.get('points', 0)}\n"
            f"• Referrals: {user_stats.get('referrals', 0)}\n"
            f"• Games Played: {user_stats.get('games_played', 0)}\n"
            f"• Games Won: {user_stats.get('games_won', 0)}\n"
            f"• Win Rate: {calculate_win_rate(query.from_user.id)}%\n"
            f"• Joined: {user_stats.get('joined_date', datetime.now()).strftime('%Y-%m-%d')}"
        )
        await query.edit_message_text(stats_text, parse_mode='Markdown')
        
    elif data == 'refer':
        user_stats = user_data.get(query.from_user.id, {})
        bot_username = (await context.bot.get_me()).username
        refer_text = (
            "🤝 **Refer Friends** 🤝\n\n"
            f"Share this link to earn points:\n"
            f"`https://t.me/{bot_username}?start={query.from_user.id}`\n\n"
            "**Benefits:**\n"
            "• 50 points per referral\n"
            "• Bonus for top referrers\n"
            "• Exclusive rewards\n\n"
            f"Total referrals: {user_stats.get('referrals', 0)}"
        )
        await query.edit_message_text(refer_text, parse_mode='Markdown')
    
    elif data == 'back_to_menu':
        await back_to_menu(update, context)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🎮 PLAY GAMES 🎮", callback_data='games_menu')],
        [InlineKeyboardButton("💰 Earn Points", callback_data='earn')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats')],
        [InlineKeyboardButton("🤝 Refer Friends", callback_data='refer')],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data='leaderboard')],
    ]
    
    if is_owner(user_id):
        keyboard.append([InlineKeyboardButton("👑 Owner Panel", callback_data='owner_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_stats = user_data.get(user_id, {})
    
    await query.edit_message_text(
        f"🎮 **AKASH Bot Menu** 🎮\n\n"
        f"Welcome back! Your points: **{user_stats.get('points', 0)}**\n\n"
        f"Choose an option below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ==================== OTHER COMMANDS ====================

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send promotional message."""
    promo_text = random.choice(PROMO_MESSAGES)
    
    keyboard = [
        [InlineKeyboardButton("🎮 Play Games Now", callback_data='games_menu')],
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    full_promo = (
        f"{promo_text}\n\n"
        f"🔗 **Join AKASH today!**\n"
        f"Channel: {CHANNEL_USERNAME_DISPLAY}\n\n"
        f"Click below to start playing!"
    )
    
    await update.message.reply_text(
        full_promo,
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
            'points': 100,
            'referrals': 0,
            'last_checkin': None,
            'games_played': 0,
            'games_won': 0,
            'total_winnings': 0
        }
    
    last_checkin = user_data[user_id].get('last_checkin')
    today = datetime.now().date()
    
    if last_checkin and last_checkin.date() == today:
        await update.message.reply_text("❌ You've already checked in today! Come back tomorrow.")
        return
    
    user_data[user_id]['points'] += 10
    user_data[user_id]['last_checkin'] = datetime.now()
    
    await update.message.reply_text(
        f"✅ Daily check-in successful!\n"
        f"You earned 10 points!\n"
        f"Total points: {user_data[user_id]['points']}\n\n"
        f"🎮 Ready to play? Use /start and click PLAY GAMES!"
    )

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle referral links."""
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])
        new_user_id = update.effective_user.id
        
        if referrer_id != new_user_id:
            if referrer_id not in user_data:
                user_data[referrer_id] = {
                    'points': 100,
                    'referrals': 0,
                    'games_played': 0,
                    'games_won': 0,
                    'total_winnings': 0
                }
            
            user_data[referrer_id]['points'] += 50
            user_data[referrer_id]['referrals'] += 1
            
            await start(update, context)
            
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 Someone joined using your referral link!\n"
                         f"You earned 50 points! Total points: {user_data[referrer_id]['points']}\n\n"
                         f"Play games to win more! Use /start"
                )
            except:
                pass

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
        logger.info(f"Starting AKASH Bot with token: {BOT_TOKEN[:10]}...")
        
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
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        
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
