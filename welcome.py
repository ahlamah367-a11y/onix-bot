import os
from flask import Flask
import threading

# --- ط¥ط¹ط¯ط§ط¯ ط®ط§ط¯ظ… ط§ظ„ظˆظٹط¨ ط§ظ„ظˆظ‡ظ…ظٹ ظ„ط¥ط±ط¶ط§ط، ظ…ظ†طµط© Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# طھط´ط؛ظٹظ„ ط§ظ„ط³ظٹط±ظپط± ظپظٹ ط®ظ„ظپظٹط© ط§ظ„ط¨ظˆطھ
threading.Thread(target=run_flask, daemon=True).start()
# ---------------------------------------------

import discord
from discord.ext import commands
from discord import app_commands

import json
from datetime import datetime, timedelta
import asyncio
import random
import time
import re

# ==================================
# ط¥ط¹ط¯ط§ط¯ ط§ظ„ط¨ظˆطھ
# ==================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.guild_messages = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ==================================
# ط§ظ„ظ…ظ„ظپط§طھ ظˆظ‚ظˆط§ط¹ط¯ ط§ظ„ط¨ظٹط§ظ†ط§طھ
# ==================================

WELCOME_CONFIG_FILE = "welcome_config.json"
LOGS_CONFIG_FILE = "logs_config.json"
MOD_CONFIG_FILE = "mod_roles.json"
WARNINGS_FILE = "warnings.json"
CONFIG_FILE = "config.json"
ERROR_LOG_FILE = "error_logs.json"
PROTECTION_FILE = "protection_config.json"
SUGGESTIONS_FILE = "suggestions.json"
SUGGESTION_CONFIG_FILE = "suggestion_config.json"
XP_FILE = "xp.json"
AFK_FILE = "afk.json"
REACTION_ROLES_FILE = "reaction_roles.json"
ANTI_CONFIG_FILE = "anti_config.json"
BAD_WORDS_FILE = "bad_words.json"
PANELS_FILE = "panels.json"
MEMBER_COUNT_FILE = "member_count.json"

# ظ…ظ„ظپط§طھ ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ ط§ظ„ط¬ط¯ظٹط¯
APPLICATIONS_FILE = "applications_data.json"
APPLICATION_CONFIG_FILE = "applications_config.json"
APPLICATION_TYPES_FILE = "application_types.json"
APPLICATION_QUESTIONS_FILE = "application_questions.json"
APPLICATION_DECISIONS_FILE = "application_decisions.json"
APPLICATION_COOLDOWN_FILE = "application_cooldowns.json"

# ==================================
# ًںژ® Fun + Economy + Events System Files
# ==================================

ECONOMY_FILE = "economy.json"
ACHIEVEMENTS_FILE = "achievements.json"
EVENTS_FILE = "events.json"
FUN_STATS_FILE = "fun_stats.json"

# ==================================
# General Panels System
# ==================================

GENERAL_PANELS_FILE = "general_panels.json"

# ==================================
# ط¯ظˆط§ظ„ ط§ظ„طھط­ظ…ظٹظ„ ظˆط§ظ„ط­ظپط¸ ط§ظ„ط¹ط§ظ…ط©
# ==================================

def load_json(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_error(error):
    logs = load_json(ERROR_LOG_FILE, [])
    logs.append({
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "error": str(error)
    })
    save_json(ERROR_LOG_FILE, logs)

welcome_config = load_json(WELCOME_CONFIG_FILE, {})
mod_roles = load_json(MOD_CONFIG_FILE, {})
protection_config = load_json(PROTECTION_FILE, {})
suggestions = load_json(SUGGESTIONS_FILE, {})
suggestion_config = load_json(SUGGESTION_CONFIG_FILE, {})
xp_data = load_json(XP_FILE, {})
afk_users = load_json(AFK_FILE, {})
reaction_roles = load_json(REACTION_ROLES_FILE, {})
anti_config = load_json(ANTI_CONFIG_FILE, {})
bad_words = load_json(BAD_WORDS_FILE, [])
persistent_panels = load_json(PANELS_FILE, [])

# طھط­ظ…ظٹظ„ ط¨ظٹط§ظ†ط§طھ ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ ط§ظ„ظ…طھط·ظˆط±
applications_data = load_json(APPLICATIONS_FILE, {})
application_config = load_json(APPLICATION_CONFIG_FILE, {})
application_types = load_json(APPLICATION_TYPES_FILE, {})
application_questions = load_json(APPLICATION_QUESTIONS_FILE, {})
application_decisions = load_json(APPLICATION_DECISIONS_FILE, {})
application_cooldowns = load_json(APPLICATION_COOLDOWN_FILE, {})

# طھط­ظ…ظٹظ„ ط¨ظٹط§ظ†ط§طھ Fun + Economy + Events
economy_data = load_json(ECONOMY_FILE, {})
achievements_data = load_json(ACHIEVEMENTS_FILE, {})
events_data = load_json(EVENTS_FILE, {})
fun_stats = load_json(FUN_STATS_FILE, {})

# طھط¹ط±ظٹظپ ظ…ظ„ظپط§طھ ط§ظ„ط¨ط§ظ†ظ„ط§طھ ط§ظ„ط¹ط§ظ…ط©
general_panels = load_json(GENERAL_PANELS_FILE, [])

def save_general_panels():
    save_json(GENERAL_PANELS_FILE, general_panels)

# ==================================
# ًں’¾ ط§ظ„ط­ظپط¸ ط§ظ„ط®ط§طµط© ط¨ظ‚ط³ظ… ط§ظ„ط§ظ‚طھطµط§ط¯ ظˆط§ظ„ظپط¹ط§ظ„ظٹط§طھ
# ==================================

def save_economy():
    save_json(ECONOMY_FILE, economy_data)

def save_achievements():
    save_json(ACHIEVEMENTS_FILE, achievements_data)

def save_events():
    save_json(EVENTS_FILE, events_data)

def save_fun_stats():
    save_json(FUN_STATS_FILE, fun_stats)

# ==================================
# ًں‘¤ ط¥ظ†ط´ط§ط، ط­ط³ط§ط¨ ط§ظ„ط¹ط¶ظˆ
# ==================================

def get_economy_user(guild_id, user_id):
    guild_id = str(guild_id)
    user_id = str(user_id)

    if guild_id not in economy_data:
        economy_data[guild_id] = {}

    if user_id not in economy_data[guild_id]:
        economy_data[guild_id][user_id] = {
            "credits": 0,
            "daily": 0,
            "work": 0,
            "games": 0,
            "wins": 0,
            "events_won": 0
        }

    return economy_data[guild_id][user_id]


def get_fun_user(guild_id, user_id):
    guild_id = str(guild_id)
    user_id = str(user_id)

    if guild_id not in fun_stats:
        fun_stats[guild_id] = {}

    if user_id not in fun_stats[guild_id]:
        fun_stats[guild_id][user_id] = {
            "games": 0,
            "wins": 0,
            "messages": 0
        }

    return fun_stats[guild_id][user_id]


# ==================================
# ًںڈ† ط§ظ„ط¥ظ†ط¬ط§ط²ط§طھ
# ==================================

ACHIEVEMENTS = {
    "first_credit": {
        "name": "ًں’° ط£ظˆظ„ ظƒط±ظٹط¯طھ",
        "description": "ط§ط­طµظ„ ط¹ظ„ظ‰ ط£ظˆظ„ Credit",
        "reward": 100
    },

    "rich": {
        "name": "ًں’ژ ط§ظ„ط«ط±ظٹ",
        "description": "ظˆطµظ„ ط¥ظ„ظ‰ 10,000 Credit",
        "reward": 500
    },

    "gambler": {
        "name": "ًںژ² ط¹ط§ط´ظ‚ ط§ظ„ط£ظ„ط¹ط§ط¨",
        "description": "ط§ظ„ط¹ط¨ 25 ظ„ط¹ط¨ط©",
        "reward": 250
    },

    "winner": {
        "name": "ًںڈ† ط§ظ„ظپط§ط¦ط²",
        "description": "ط§ط±ط¨ط­ 10 ط£ظ„ط¹ط§ط¨",
        "reward": 500
    },

    "event_winner": {
        "name": "ًںژ‰ ط¨ط·ظ„ ط§ظ„ظپط¹ط§ظ„ظٹط§طھ",
        "description": "ط§ط±ط¨ط­ ظپط¹ط§ظ„ظٹط©",
        "reward": 1000
    }
}


def unlock_achievement(guild_id, user_id, achievement_id):
    guild_id = str(guild_id)
    user_id = str(user_id)

    if guild_id not in achievements_data:
        achievements_data[guild_id] = {}

    if user_id not in achievements_data[guild_id]:
        achievements_data[guild_id][user_id] = []

    if achievement_id in achievements_data[guild_id][user_id]:
        return False

    if achievement_id not in ACHIEVEMENTS:
        return False

    achievements_data[guild_id][user_id].append(achievement_id)

    reward = ACHIEVEMENTS[achievement_id]["reward"]

    user = get_economy_user(guild_id, user_id)
    user["credits"] += reward

    save_achievements()
    save_economy()

    return True


# ==================================
# ًں’° Balance
# ==================================

@bot.tree.command(
    name="balance",
    description="ط¹ط±ط¶ ط±طµظٹط¯ظƒ ط£ظˆ ط±طµظٹط¯ ط¹ط¶ظˆ"
)
async def balance(
    interaction: discord.Interaction,
    member: discord.Member = None
):
    member = member or interaction.user

    data = get_economy_user(
        interaction.guild.id,
        member.id
    )

    embed = discord.Embed(
        title="ًں’° ط§ظ„ط±طµظٹط¯",
        description=(
            f"ًں‘¤ ط§ظ„ط¹ط¶ظˆ: {member.mention}\n\n"
            f"ًں’³ **Credits:** `{data['credits']:,}`"
        ),
        color=discord.Color.gold()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# ًںژپ Daily
# ==================================

@bot.tree.command(
    name="daily",
    description="ط§ط³طھظ„ط§ظ… ظ…ظƒط§ظپط£ط© ظٹظˆظ…ظٹط©"
)
async def daily(interaction: discord.Interaction):

    user = get_economy_user(
        interaction.guild.id,
        interaction.user.id
    )

    now = int(time.time())
    cooldown = 86400

    if now - user["daily"] < cooldown:
        remaining = cooldown - (now - user["daily"])

        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        await interaction.response.send_message(
            f"âڈ³ ط§ط±ط¬ط¹ ط¨ط¹ط¯ **{hours} ط³ط§ط¹ط© ظˆ {minutes} ط¯ظ‚ظٹظ‚ط©**.",
            ephemeral=True
        )
        return

    reward = random.randint(300, 700)

    user["credits"] += reward
    user["daily"] = now

    save_economy()

    unlocked = unlock_achievement(
        interaction.guild.id,
        interaction.user.id,
        "first_credit"
    )

    await interaction.response.send_message(
        f"ًںژپ ط­طµظ„طھ ط¹ظ„ظ‰ **{reward:,} Credits** ط§ظ„ظٹظˆظ…!\n"
        f"ًں’° ط±طµظٹط¯ظƒ ط§ظ„ط¢ظ†: **{user['credits']:,}**"
    )


# ==================================
# ًں’¼ Work
# ==================================

@bot.tree.command(
    name="work",
    description="ط§ط¹ظ…ظ„ ظ„طھط­طµظ„ ط¹ظ„ظ‰ Credits"
)
async def work(interaction: discord.Interaction):

    user = get_economy_user(
        interaction.guild.id,
        interaction.user.id
    )

    now = int(time.time())
    cooldown = 3600

    if now - user["work"] < cooldown:

        remaining = cooldown - (now - user["work"])

        minutes = remaining // 60
        seconds = remaining % 60

        await interaction.response.send_message(
            f"âڈ³ ظٹظ…ظƒظ†ظƒ ط§ظ„ط¹ظ…ظ„ ط¨ط¹ط¯ `{minutes}m {seconds}s`.",
            ephemeral=True
        )
        return

    jobs = [
        "ًں’» ط¨ط±ظ…ط¬طھ ط¨ظˆطھ ط¬ط¯ظٹط¯",
        "ًں§¹ ظ†ط¸ظپطھ ط§ظ„ط³ظٹط±ظپط±",
        "ًںژ® ظ„ط¹ط¨طھ ظ…ط¹ ط§ظ„ط£ط¹ط¶ط§ط،",
        "ًں› ï¸ڈ ط³ط§ط¹ط¯طھ ط§ظ„ط¥ط¯ط§ط±ط©",
        "ًں“¦ ط±طھط¨طھ ط§ظ„ظ…ظ„ظپط§طھ",
        "âک• ط§ط´طھط؛ظ„طھ ظپظٹ ط§ظ„ظƒط§ظپظٹظ‡"
    ]

    job = random.choice(jobs)
    reward = random.randint(100, 500)

    user["credits"] += reward
    user["work"] = now

    save_economy()

    unlock_achievement(
        interaction.guild.id,
        interaction.user.id,
        "first_credit"
    )

    await interaction.response.send_message(
        f"{job}\n\n"
        f"ًں’µ ط­طµظ„طھ ط¹ظ„ظ‰ **{reward:,} Credits**\n"
        f"ًں’° ط±طµظٹط¯ظƒ: **{user['credits']:,}**"
    )


# ==================================
# ًں’¸ Pay
# ==================================

@bot.tree.command(
    name="pay",
    description="طھط­ظˆظٹظ„ Credits ط¥ظ„ظ‰ ط¹ط¶ظˆ"
)
async def pay(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    if member.bot:
        await interaction.response.send_message(
            "â‌Œ ظ„ط§ ظٹظ…ظƒظ†ظƒ ط§ظ„طھط­ظˆظٹظ„ ظ„ظ„ط¨ظˆطھط§طھ.",
            ephemeral=True
        )
        return

    if member.id == interaction.user.id:
        await interaction.response.send_message(
            "ًںک‚ طھط±ظٹط¯ طھط¯ظپط¹ ظ„ظ†ظپط³ظƒطں",
            ephemeral=True
        )
        return

    if amount <= 0:
        await interaction.response.send_message(
            "â‌Œ ط§ظ„ظ…ط¨ظ„ط؛ ظٹط¬ط¨ ط£ظ† ظٹظƒظˆظ† ط£ظƒط¨ط± ظ…ظ† طµظپط±.",
            ephemeral=True
        )
        return

    sender = get_economy_user(
        interaction.guild.id,
        interaction.user.id
    )

    receiver = get_economy_user(
        interaction.guild.id,
        member.id
    )

    if sender["credits"] < amount:
        await interaction.response.send_message(
            "â‌Œ ظ…ط§ ط¹ظ†ط¯ظƒ Credits ظƒط§ظپظٹط©.",
            ephemeral=True
        )
        return

    sender["credits"] -= amount
    receiver["credits"] += amount

    save_economy()

    await interaction.response.send_message(
        f"ًں’¸ طھظ… طھط­ظˆظٹظ„ **{amount:,} Credits** ط¥ظ„ظ‰ {member.mention}."
    )


# ==================================
# ًںڈ† Economy Leaderboard
# ==================================

@bot.tree.command(
    name="economy-leaderboard",
    description="طھط±طھظٹط¨ ط£ط؛ظ†ظ‰ ط£ط¹ط¶ط§ط، ط§ظ„ط³ظٹط±ظپط±"
)
async def economy_leaderboard(
    interaction: discord.Interaction
):

    guild_data = economy_data.get(
        str(interaction.guild.id),
        {}
    )

    ranking = sorted(
        guild_data.items(),
        key=lambda x: x[1].get("credits", 0),
        reverse=True
    )

    if not ranking:
        await interaction.response.send_message(
            "â‌Œ ظ„ط§ طھظˆط¬ط¯ ط¨ظٹط§ظ†ط§طھ ط¨ط¹ط¯."
        )
        return

    lines = []

    medals = ["ًں¥‡", "ًں¥ˆ", "ًں¥‰"]

    for index, (user_id, data) in enumerate(ranking[:10]):

        member = interaction.guild.get_member(
            int(user_id)
        )

        if not member:
            continue

        medal = (
            medals[index]
            if index < 3
            else f"`#{index + 1}`"
        )

        lines.append(
            f"{medal} {member.mention} â€” "
            f"**{data.get('credits', 0):,}** ًں’°"
        )

    embed = discord.Embed(
        title="ًںڈ† ط£ط؛ظ†ظ‰ ط£ط¹ط¶ط§ط، ط§ظ„ط³ظٹط±ظپط±",
        description="\n".join(lines),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# ًںژ® 8Ball
# ==================================

@bot.tree.command(
    name="8ball",
    description="ط§ط³ط£ظ„ ط§ظ„ظƒط±ط© ط§ظ„ط³ط­ط±ظٹط©"
)
async def eight_ball(
    interaction: discord.Interaction,
    question: str
):

    answers = [
        "ظ†ط¹ظ… âœ…",
        "ظ„ط§ â‌Œ",
        "ط؛ط§ظ„ط¨ظ‹ط§ ًں¤”",
        "ظ…ط³طھط­ظٹظ„ ًں’€",
        "ط£ظƒظٹط¯ ًں”¥",
        "ط§ط³ط£ظ„ظ†ظٹ ط¨ظƒط±ط© ًں—؟",
        "ط§ظ„ط¬ظˆط§ط¨ ط¹ظ†ط¯ ط§ظ„ظ…ط¯ظٹط± ًں‘€",
        "ظ…ط§ ط¹ظ†ط¯ظٹ ط¹ظ„ظ… ًںک‚",
        "ط§ظ„ط§ط­طھظ…ط§ظ„ ظƒط¨ظٹط± ط¬ط¯ظ‹ط§ ًں“ˆ",
        "ظ„ط§ طھط³ط£ظ„ ط£ط³ط¦ظ„ط© طµط¹ط¨ط© ًںک­"
    ]

    await interaction.response.send_message(
        f"ًںژ± **ط§ظ„ط³ط¤ط§ظ„:** {question}\n\n"
        f"ًں”® **ط§ظ„ط¬ظˆط§ط¨:** {random.choice(answers)}"
    )


# ==================================
# ًںژ² Dice
# ==================================

@bot.tree.command(
    name="dice",
    description="ط§ط±ظ…ظگ ط§ظ„ظ†ط±ط¯"
)
async def dice(interaction: discord.Interaction):

    result = random.randint(1, 6)

    await interaction.response.send_message(
        f"ًںژ² ط±ظ…ظٹطھ ط§ظ„ظ†ط±ط¯ ظˆط·ظ„ط¹: **{result}**"
    )


# ==================================
# ًںھ™ Coin Flip
# ==================================

@bot.tree.command(
    name="coinflip",
    description="ط§ظ‚ظ„ط¨ ط§ظ„ط¹ظ…ظ„ط©"
)
async def coinflip(interaction: discord.Interaction):

    result = random.choice([
        "ًںھ™ طµظˆط±ط©",
        "ًںھ™ ظƒطھط§ط¨ط©"
    ])

    await interaction.response.send_message(
        f"ًںھ™ ط§ظ„ظ†طھظٹط¬ط©: **{result}**"
    )


# ==================================
# ًںژ¯ Choose
# ==================================

@bot.tree.command(
    name="choose",
    description="ط®ظ„ ط§ظ„ط¨ظˆطھ ظٹط®طھط§ط± ظ„ظƒ"
)
async def choose(
    interaction: discord.Interaction,
    options: str
):

    choices = [
        x.strip()
        for x in options.split(",")
        if x.strip()
    ]

    if len(choices) < 2:

        await interaction.response.send_message(
            "â‌Œ ط§ظƒطھط¨ ط®ظٹط§ط±ظٹظ† ط¹ظ„ظ‰ ط§ظ„ط£ظ‚ظ„ ظ…ظپطµظˆظ„ظٹظ† ط¨ظپط§طµظ„ط©.\n"
            "ظ…ط«ط§ظ„: `/choose ط¨ظٹطھط²ط§, ط¨ط±ط؛ط±, ط´ط§ظˆط±ظ…ط§`",
            ephemeral=True
        )
        return

    selected = random.choice(choices)

    await interaction.response.send_message(
        f"ًںژ¯ ط§ط®طھط±طھ ظ„ظƒ: **{selected}**"
    )


# ==================================
# â­گ Rank
# ==================================

@bot.tree.command(
    name="rank",
    description="ط¹ط±ط¶ ظ…ط³طھظˆط§ظƒ ظˆ XP"
)
async def rank(
    interaction: discord.Interaction,
    member: discord.Member = None
):

    member = member or interaction.user

    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    guild_xp = xp_data.get(
        guild_id,
        {}
    )

    data = guild_xp.get(
        user_id,
        {
            "xp": 0,
            "level": 1
        }
    )

    level = data.get("level", 1)
    xp = data.get("xp", 0)

    next_xp = level * 100

    embed = discord.Embed(
        title=f"â­گ ظ…ط³طھظˆظ‰ {member.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="â­گ ط§ظ„ظ…ط³طھظˆظ‰",
        value=f"`{level}`",
        inline=True
    )

    embed.add_field(
        name="âœ¨ XP",
        value=f"`{xp:,}`",
        inline=True
    )

    embed.add_field(
        name="ًں“ˆ ط§ظ„ظ…ط³طھظˆظ‰ ط§ظ„ظ‚ط§ط¯ظ…",
        value=f"`{next_xp:,} XP`",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# ًں‘¤ Profile
# ==================================

@bot.tree.command(
    name="profile",
    description="ط¹ط±ط¶ ظ…ظ„ظپظƒ ط§ظ„ط´ط®طµظٹ ط§ظ„ظƒط§ظ…ظ„"
)
async def profile(
    interaction: discord.Interaction,
    member: discord.Member = None
):

    member = member or interaction.user

    gid = str(interaction.guild.id)
    uid = str(member.id)

    money = get_economy_user(
        gid,
        uid
    )

    xp = xp_data.get(
        gid,
        {}
    ).get(
        uid,
        {
            "xp": 0,
            "level": 1
        }
    )

    user_achievements = achievements_data.get(
        gid,
        {}
    ).get(
        uid,
        []
    )

    embed = discord.Embed(
        title=f"ًں‘¤ ظ…ظ„ظپ {member.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="â­گ ط§ظ„ظ…ط³طھظˆظ‰",
        value=f"`{xp.get('level', 1)}`",
        inline=True
    )

    embed.add_field(
        name="âœ¨ XP",
        value=f"`{xp.get('xp', 0):,}`",
        inline=True
    )

    embed.add_field(
        name="ًں’° Credits",
        value=f"`{money.get('credits', 0):,}`",
        inline=True
    )

    embed.add_field(
        name="ًںژ® ط§ظ„ط£ظ„ط¹ط§ط¨",
        value=f"`{money.get('games', 0)}`",
        inline=True
    )

    embed.add_field(
        name="ًںڈ† ط§ظ„ط§ظ†طھطµط§ط±ط§طھ",
        value=f"`{money.get('wins', 0)}`",
        inline=True
    )

    embed.add_field(
        name="ًںژ‰ ظپط¹ط§ظ„ظٹط§طھ ظپط§ط² ط¨ظ‡ط§",
        value=f"`{money.get('events_won', 0)}`",
        inline=True
    )

    embed.add_field(
        name="ًںڈ… ط§ظ„ط¥ظ†ط¬ط§ط²ط§طھ",
        value=f"`{len(user_achievements)}`",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# ًںڈ… Achievements
# ==================================

@bot.tree.command(
    name="achievements",
    description="ط¹ط±ط¶ ط¥ظ†ط¬ط§ط²ط§طھظƒ"
)
async def achievements(
    interaction: discord.Interaction,
    member: discord.Member = None
):

    member = member or interaction.user

    gid = str(interaction.guild.id)
    uid = str(member.id)

    unlocked = achievements_data.get(
        gid,
        {}
    ).get(
        uid,
        []
    )

    lines = []

    for achievement_id, info in ACHIEVEMENTS.items():

        if achievement_id in unlocked:
            lines.append(
                f"âœ… **{info['name']}**\n"
                f"> {info['description']}"
            )
        else:
            lines.append(
                f"ًں”’ **{info['name']}**\n"
                f"> {info['description']}"
            )

    embed = discord.Embed(
        title=f"ًںڈ… ط¥ظ†ط¬ط§ط²ط§طھ {member.display_name}",
        description="\n\n".join(lines),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# ًںژ‰ ظ†ط¸ط§ظ… ط§ظ„ظپط¹ط§ظ„ظٹط§طھ
# ==================================

class EventView(discord.ui.View):

    def __init__(self, event_id):
        super().__init__(timeout=None)

        self.event_id = str(event_id)

        button = discord.ui.Button(
            label="ًںژ‰ ظ…ط´ط§ط±ظƒط©",
            style=discord.ButtonStyle.green,
            custom_id=f"event_join_{self.event_id}"
        )

        button.callback = self.join_event

        self.add_item(button)

    async def join_event(
        self,
        interaction: discord.Interaction
    ):

        event = events_data.get(
            self.event_id
        )

        if not event:
            await interaction.response.send_message(
                "â‌Œ ظ‡ط°ظ‡ ط§ظ„ظپط¹ط§ظ„ظٹط© ط؛ظٹط± ظ…ظˆط¬ظˆط¯ط©.",
                ephemeral=True
            )
            return

        if event["ended"]:
            await interaction.response.send_message(
                "â‌Œ ط§ظ†طھظ‡طھ ط§ظ„ظپط¹ط§ظ„ظٹط©.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        if user_id in event["participants"]:
            await interaction.response.send_message(
                "âڑ ï¸ڈ ط£ظ†طھ ظ…ط´ط§ط±ظƒ ط¨ط§ظ„ظپط¹ظ„!",
                ephemeral=True
            )
            return

        event["participants"].append(
            user_id
        )

        save_events()

        await interaction.response.send_message(
            "ًںژ‰ طھظ… طھط³ط¬ظٹظ„ ظ…ط´ط§ط±ظƒطھظƒ ظپظٹ ط§ظ„ظپط¹ط§ظ„ظٹط©!",
            ephemeral=True
        )

        try:

            await interaction.message.edit(
                embed=create_event_embed(event),
                view=self
            )

        except:
            pass


def create_event_embed(event):

    remaining = max(
        0,
        event["end_time"] - int(time.time())
    )

    minutes = remaining // 60
    seconds = remaining % 60

    status = (
        "ًںں¢ ظ…ظپطھظˆط­ط©"
        if not event["ended"]
        else "ًں”´ ط§ظ†طھظ‡طھ"
    )

    embed = discord.Embed(
        title=f"ًںژ‰ {event['title']}",
        description=event["description"],
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="ًںژپ ط§ظ„ط¬ط§ط¦ط²ط©",
        value=f"**{event['reward']:,} Credits**",
        inline=True
    )

    embed.add_field(
        name="ًں‘¥ ط§ظ„ظ…ط´ط§ط±ظƒظˆظ†",
        value=f"`{len(event['participants'])}`",
        inline=True
    )

    embed.add_field(
        name="ًں“Œ ط§ظ„ط­ط§ظ„ط©",
        value=status,
        inline=True
    )

    if not event["ended"]:

        embed.add_field(
            name="âڈ³ ط§ظ„ظˆظ‚طھ ط§ظ„ظ…طھط¨ظ‚ظٹ",
            value=f"`{minutes}m {seconds}s`",
            inline=False
        )

    return embed


async def finish_event(event_id):

    event = events_data.get(
        str(event_id)
    )

    if not event or event["ended"]:
        return

    event["ended"] = True

    participants = event.get(
        "participants",
        []
    )

    guild = bot.get_guild(
        event["guild_id"]
    )

    channel = (
        guild.get_channel(event["channel_id"])
        if guild
        else None
    )

    # ظ„ط§ ظٹظˆط¬ط¯ ظ…ط´ط§ط±ظƒظٹظ†
    if not participants:

        save_events()

        if channel:

            try:

                message = await channel.fetch_message(
                    event["message_id"]
                )

                await message.edit(
                    embed=create_event_embed(event),
                    view=None
                )

                await channel.send(
                    f"ًںژ‰ ط§ظ†طھظ‡طھ ظپط¹ط§ظ„ظٹط© **{event['title']}**\n"
                    f"â‌Œ ظ„ظ… ظٹط´ط§ط±ظƒ ط£ط­ط¯طŒ ظ„ط°ظ„ظƒ ظ„ط§ ظٹظˆط¬ط¯ ظپط§ط¦ط²."
                )

            except:
                pass

        return

    winner_id = random.choice(
        participants
    )

    winner = (
        guild.get_member(winner_id)
        if guild
        else None
    )

    # ط¥ط¹ط·ط§ط، ط§ظ„ط¬ط§ط¦ط²ط©
    winner_data = get_economy_user(
        event["guild_id"],
        winner_id
    )

    winner_data["credits"] += event["reward"]
    winner_data["events_won"] += 1

    save_economy()

    unlock_achievement(
        event["guild_id"],
        winner_id,
        "event_winner"
    )

    save_events()

    if channel:

        try:

            message = await channel.fetch_message(
                event["message_id"]
            )

            await message.edit(
                embed=create_event_embed(event),
                view=None
            )

        except:
            pass

        winner_text = (
            winner.mention
            if winner
            else f"<@{winner_id}>"
        )

        await channel.send(
            f"ًںژ‰ **ط§ظ†طھظ‡طھ ط§ظ„ظپط¹ط§ظ„ظٹط©!**\n\n"
            f"ًںڈ† ط§ظ„ظپط§ط¦ط²: {winner_text}\n"
            f"ًں’° ط§ظ„ط¬ط§ط¦ط²ط©: **{event['reward']:,} Credits**\n\n"
            f"ظ…ط¨ط±ظˆظƒ! ًںژٹ"
        )


async def event_timer(event_id):

    event = events_data.get(
        str(event_id)
    )

    if not event:
        return

    remaining = (
        event["end_time"] - int(time.time())
    )

    if remaining > 0:
        await asyncio.sleep(remaining)

    await finish_event(event_id)


# ==================================
# ًںژ‰ ط¥ظ†ط´ط§ط، ظپط¹ط§ظ„ظٹط©
# ==================================

@bot.tree.command(
    name="event-create",
    description="ط¥ظ†ط´ط§ط، ظپط¹ط§ظ„ظٹط© ظ…ط¹ ط¬ط§ط¦ط²ط© Credits"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def event_create(
    interaction: discord.Interaction,
    title: str,
    description: str,
    minutes: int,
    reward: int
):

    if minutes <= 0:
        await interaction.response.send_message(
            "â‌Œ ظ…ط¯ط© ط§ظ„ظپط¹ط§ظ„ظٹط© ظٹط¬ط¨ ط£ظ† طھظƒظˆظ† ط£ظƒط¨ط± ظ…ظ† طµظپط±.",
            ephemeral=True
        )
        return

    if reward <= 0:
        await interaction.response.send_message(
            "â‌Œ ط§ظ„ط¬ط§ط¦ط²ط© ظٹط¬ط¨ ط£ظ† طھظƒظˆظ† ط£ظƒط¨ط± ظ…ظ† طµظپط±.",
            ephemeral=True
        )
        return

    event_id = str(
        random.randint(
            100000,
            999999
        )
    )

    # ط§ظ„طھط£ظƒط¯ ظ…ظ† ط¹ط¯ظ… طھظƒط±ط§ط± ID
    while event_id in events_data:

        event_id = str(
            random.randint(
                100000,
                999999
            )
        )

    event = {
        "id": event_id,
        "guild_id": interaction.guild.id,
        "channel_id": interaction.channel.id,
        "message_id": None,
        "title": title,
        "description": description,
        "reward": reward,
        "participants": [],
        "created_by": interaction.user.id,
        "end_time": int(time.time()) + (minutes * 60),
        "ended": False
    }

    events_data[event_id] = event

    embed = create_event_embed(
        event
    )

    message = await interaction.channel.send(
        embed=embed,
        view=EventView(event_id)
    )

    event["message_id"] = message.id

    save_events()

    await interaction.response.send_message(
        f"âœ… طھظ… ط¥ظ†ط´ط§ط، ط§ظ„ظپط¹ط§ظ„ظٹط©!\n"
        f"ًں†” ID: `{event_id}`\n"
        f"ًںژپ ط§ظ„ط¬ط§ط¦ط²ط©: **{reward:,} Credits**",
        ephemeral=True
    )

    asyncio.create_task(
        event_timer(event_id)
    )


# ==================================
# ًں“‹ ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ظپط¹ط§ظ„ظٹط©
# ==================================

@bot.tree.command(
    name="event-info",
    description="ط¹ط±ط¶ ظ…ط¹ظ„ظˆظ…ط§طھ ظپط¹ط§ظ„ظٹط©"
)
async def event_info(
    interaction: discord.Interaction,
    event_id: str
):

    event = events_data.get(
        event_id
    )

    if not event:
        await interaction.response.send_message(
            "â‌Œ ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط§ظ„ظپط¹ط§ظ„ظٹط©.",
            ephemeral=True
        )
        return

    embed = create_event_embed(
        event
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ==================================
# â‌Œ ط¥ظ†ظ‡ط§ط، ظپط¹ط§ظ„ظٹط© ظٹط¯ظˆظٹظ‹ط§
# ==================================

@bot.tree.command(
    name="event-end",
    description="ط¥ظ†ظ‡ط§ط، ظپط¹ط§ظ„ظٹط© ظˆط§ط®طھظٹط§ط± ط§ظ„ظپط§ط¦ط²"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def event_end(
    interaction: discord.Interaction,
    event_id: str
):

    event = events_data.get(
        event_id
    )

    if not event:
        await interaction.response.send_message(
            "â‌Œ ط§ظ„ظپط¹ط§ظ„ظٹط© ط؛ظٹط± ظ…ظˆط¬ظˆط¯ط©.",
            ephemeral=True
        )
        return

    if event["ended"]:
        await interaction.response.send_message(
            "âڑ ï¸ڈ ط§ظ„ظپط¹ط§ظ„ظٹط© ظ…ظ†طھظ‡ظٹط© ط¨ط§ظ„ظپط¹ظ„.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "âڈ³ ط¬ط§ط±ظٹ ط¥ظ†ظ‡ط§ط، ط§ظ„ظپط¹ط§ظ„ظٹط©...",
        ephemeral=True
    )

    await finish_event(
        event_id
    )


# ==================================
# ًں”„ ط§ط³طھط¹ط§ط¯ط© ط§ظ„ظپط¹ط§ظ„ظٹط§طھ ط¨ط¹ط¯ Restart
# ==================================

async def restore_events():

    for event_id, event in events_data.items():

        if event.get("ended"):
            continue

        remaining = (
            event["end_time"] - int(time.time())
        )

        if remaining <= 0:

            asyncio.create_task(
                finish_event(event_id)
            )

        else:

            asyncio.create_task(
                event_timer(event_id)
            )

class GeneralPanelView(discord.ui.View):
    def __init__(self, button_name, button_emoji, button_description):
        super().__init__(timeout=None)

        button = discord.ui.Button(
            label=button_name,
            emoji=button_emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"general_panel_{button_name}"
        )

        button.callback = self.button_callback
        self.add_item(button)

        self.button_label = button_name
        self.button_description = button_description


    async def button_callback(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=self.button_label,
            description=self.button_description,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


@bot.tree.command(
    name="panel",
    description="ط¥ظ†ط´ط§ط، ط¨ط§ظ†ظ„ ط¹ط§ظ…"
)
@app_commands.checks.has_permissions(administrator=True)
async def panel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    description: str,
    button_name: str,
    button_emoji: str,
    button_description: str,
    image: str = None
):

    embed = discord.Embed(
        title="ًں“Œ Panel",
        description=description,
        color=discord.Color.blurple()
    )

    if image:
        embed.set_image(url=image)


    view = GeneralPanelView(
        button_name,
        button_emoji,
        button_description
    )


    msg = await channel.send(
        embed=embed,
        view=view
    )


    general_panels.append({
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id,
        "button_name": button_name,
        "button_emoji": button_emoji,
        "button_description": button_description
    })


    save_general_panels()


    await interaction.response.send_message(
        "âœ… طھظ… ط¥ظ†ط´ط§ط، ط§ظ„ط¨ط§ظ†ظ„ ظˆط­ظپط¸ظ‡ ط¨ظ†ط¬ط§ط­",
        ephemeral=True
    )

def save_persistent():
    save_json(PANELS_FILE, persistent_panels)

def save_application_types():
    save_json(APPLICATION_TYPES_FILE, application_types)

def save_all_applications():
    save_json(APPLICATIONS_FILE, applications_data)
    save_json(APPLICATION_CONFIG_FILE, application_config)
    save_json(APPLICATION_TYPES_FILE, application_types)
    save_json(APPLICATION_QUESTIONS_FILE, application_questions)
    save_json(APPLICATION_DECISIONS_FILE, application_decisions)
    save_json(APPLICATION_COOLDOWN_FILE, application_cooldowns)

def save_member_count(data):
    save_json(MEMBER_COUNT_FILE, data)

def load_member_count():
    return load_json(MEMBER_COUNT_FILE, {})

def save_suggestions_config():
    save_json(SUGGESTION_CONFIG_FILE, suggestion_config)

# ==================================
# ظ†ط¸ط§ظ… ط§ظ„ط³ط¬ظ„ط§طھ (Logs System)
# ==================================

async def send_log(guild, title, description, color):
    config = load_json(LOGS_CONFIG_FILE, {})
    log_channel_id = config.get(str(guild.id))
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if channel:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
            try:
                await channel.send(embed=embed)
            except:
                pass

@bot.tree.command(name="set-logs", description="طھط­ط¯ظٹط¯ ط±ظˆظ… ط§ظ„ط³ط¬ظ„ط§طھ (Logs)")
@app_commands.describe(channel="ط±ظˆظ… ط§ظ„ط³ط¬ظ„ط§طھ")
@app_commands.checks.has_permissions(administrator=True)
async def set_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_json(LOGS_CONFIG_FILE, {})
    config[str(interaction.guild.id)] = channel.id
    save_json(LOGS_CONFIG_FILE, config)
    await interaction.response.send_message(f"âœ… طھظ… ط¶ط¨ط· ط±ظˆظ… ط§ظ„ط³ط¬ظ„ط§طھ ط¨ظ†ط¬ط§ط­ ظپظٹ {channel.mention}", ephemeral=True)

@bot.tree.command(name="remove-logs", description="ط¥ظ„ط؛ط§ط، ظˆطھظپط±ظٹط؛ ط¥ط¹ط¯ط§ط¯ ط±ظˆظ… ط§ظ„ط³ط¬ظ„ط§طھ")
@app_commands.checks.has_permissions(administrator=True)
async def remove_logs(interaction: discord.Interaction):
    config = load_json(LOGS_CONFIG_FILE, {})
    gid = str(interaction.guild.id)
    if gid in config:
        del config[gid]
        save_json(LOGS_CONFIG_FILE, config)
        await interaction.response.send_message("â‌Œ طھظ… ط¥ظ„ط؛ط§ط، ط±ظˆظ… ط§ظ„ط³ط¬ظ„ط§طھ ط¨ظ†ط¬ط§ط­.", ephemeral=True)
    else:
        await interaction.response.send_message("âڑ ï¸ڈ ط±ظˆظ… ط§ظ„ط³ط¬ظ„ط§طھ ط؛ظٹط± ظ…ظپط¹ظ„ ط£ط³ط§ط³ط§ظ‹.", ephemeral=True)

# ==================================
# ظ†ط¸ط§ظ… ط§ظ„طھط±ط­ظٹط¨ ظˆط§ظ„ط¹ط¯ط§ط¯
# ==================================

@bot.tree.command(name="set-welcome", description="طھط¹ط¯ط§ط¯ ظˆطھط®طµظٹطµ ط±ط³ط§ظ„ط© ط§ظ„طھط±ط­ظٹط¨ ظˆط£ط¹ط¶ط§ط، ط§ظ„ط³ظٹط±ظپط±")
@app_commands.describe(
    channel="ط±ظˆظ… ط§ظ„طھط±ط­ظٹط¨",
    message="ظ†طµ ط±ط³ط§ظ„ط© ط§ظ„طھط±ط­ظٹط¨ (ظٹظ…ظƒظ† ط§ط³طھط®ط¯ط§ظ… ط§ظ„ظ…طھط؛ظٹط±ط§طھ)",
    show_user="ظ‡ظ„ طھط±ظٹط¯ ظ…ظ†ط´ظ† ط§ظ„ط¹ط¶ظˆطں",
    show_count="ظ‡ظ„ طھط±ظٹط¯ ط¥ط¸ظ‡ط§ط± ط§ظ„ط¹ط¯ط¯طں"
)
@app_commands.choices(
    show_user=[
        app_commands.Choice(name="ظ†ط¹ظ…", value="yes"),
        app_commands.Choice(name="ظ„ط§", value="no")
    ],
    show_count=[
        app_commands.Choice(name="ظ†ط¹ظ…", value="yes"),
        app_commands.Choice(name="ظ„ط§", value="no")
    ]
)
@app_commands.checks.has_permissions(administrator=True)
async def set_welcome(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    show_user: str,
    show_count: str
):
    guild_id = str(interaction.guild.id)
    
    welcome_config[guild_id] = {
        "channel_id": channel.id,
        "message": message,
        "show_user": (show_user == "yes"),
        "show_count": (show_count == "yes")
    }
    save_json(WELCOME_CONFIG_FILE, welcome_config)
    
    await interaction.response.send_message(
        f"âœ… طھظ… ط­ظپط¸ ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„طھط±ط­ظٹط¨ ط¨ظ†ط¬ط§ط­ ظپظٹ ط±ظˆظ… {channel.mention}!",
        ephemeral=True
    )

@bot.tree.command(name="welcome-test", description="طھط¬ط±ط¨ط© ط±ط³ط§ظ„ط© ط§ظ„طھط±ط­ظٹط¨")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_test(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in welcome_config:
        await interaction.response.send_message("â‌Œ ظ„ظ… ظٹطھظ… ط¥ط¹ط¯ط§ط¯ ط§ظ„طھط±ط­ظٹط¨ ط¨ط¹ط¯.", ephemeral=True)
        return
    data = welcome_config[guild_id]
    channel = interaction.guild.get_channel(data.get("channel_id"))
    if not channel:
        await interaction.response.send_message("â‌Œ ط±ظˆظ… ط§ظ„طھط±ط­ظٹط¨ ط؛ظٹط± ظ…ظˆط¬ظˆط¯.", ephemeral=True)
        return
    message = data.get("message", "ط£ظ‡ظ„ط§ظ‹ ط¨ظƒ {user} ظپظٹ ط§ظ„ط³ظٹط±ظپط±!").replace("{user}", interaction.user.mention)
    embed = discord.Embed(title="ًں‘‹ طھط¬ط±ط¨ط© طھط±ط­ظٹط¨", description=message, color=discord.Color.green())
    await channel.send(content=interaction.user.mention, embed=embed)
    await interaction.response.send_message("âœ… طھظ… ط¥ط±ط³ط§ظ„ طھط¬ط±ط¨ط© ط§ظ„طھط±ط­ظٹط¨.", ephemeral=True)

@bot.tree.command(name="welcome-remove", description="ط­ط°ظپ ط¥ط¹ط¯ط§ط¯ ط§ظ„طھط±ط­ظٹط¨")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_remove(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id in welcome_config:
        del welcome_config[guild_id]
        save_json(WELCOME_CONFIG_FILE, welcome_config)
        await interaction.response.send_message("âœ… طھظ… ط­ط°ظپ ظ†ط¸ط§ظ… ط§ظ„طھط±ط­ظٹط¨.", ephemeral=True)
    else:
        await interaction.response.send_message("â‌Œ ظ†ط¸ط§ظ… ط§ظ„طھط±ط­ظٹط¨ ط؛ظٹط± ظ…ظپط¹ظ„.", ephemeral=True)

@bot.tree.command(name="member-count-setup", description="ط¥ط¹ط¯ط§ط¯ ط¹ط¯ط§ط¯ ط§ظ„ط£ط¹ط¶ط§ط،")
@app_commands.checks.has_permissions(administrator=True)
async def member_count_setup(interaction: discord.Interaction, channel: discord.VoiceChannel, name: str = "ًں‘¥ ط§ظ„ط£ط¹ط¶ط§ط،: {count}"):
    data = load_member_count()
    data[str(interaction.guild.id)] = {"channel_id": channel.id, "name": name}
    save_member_count(data)
    count = interaction.guild.member_count
    await channel.edit(name=name.replace("{count}", str(count)))
    await interaction.response.send_message(f"âœ… طھظ… ط¥ط¹ط¯ط§ط¯ ط¹ط¯ط§ط¯ ط§ظ„ط£ط¹ط¶ط§ط، ط§ظ„ط­ط§ظ„ظٹ: `{count}`", ephemeral=True)

@bot.tree.command(name="member-count-remove", description="ط­ط°ظپ ط¹ط¯ط§ط¯ ط§ظ„ط£ط¹ط¶ط§ط،")
@app_commands.checks.has_permissions(administrator=True)
async def member_count_remove(interaction: discord.Interaction):
    data = load_member_count()
    guild_id = str(interaction.guild.id)
    if guild_id in data:
        del data[guild_id]
        save_member_count(data)
        await interaction.response.send_message("âœ… طھظ… ط­ط°ظپ ط¹ط¯ط§ط¯ ط§ظ„ط£ط¹ط¶ط§ط،.", ephemeral=True)
    else:
        await interaction.response.send_message("â‌Œ ظ„ط§ ظٹظˆط¬ط¯ ط¹ط¯ط§ط¯ ط£ط¹ط¶ط§ط، ظ…ظپط¹ظ„.", ephemeral=True)

async def update_member_count(guild):
    data = load_member_count()
    guild_id = str(guild.id)
    if guild_id not in data:
        return
    channel = guild.get_channel(data[guild_id]["channel_id"])
    if channel:
        await channel.edit(name=data[guild_id]["name"].replace("{count}", str(guild.member_count)))

# ==================================
# ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† ط§ظ„طµظ„ط§ط­ظٹط§طھ ظˆط§ظ„ط£ط­ط¯ط§ط« ط§ظ„ط£ط³ط§ط³ظٹط©
# ==================================

def has_mod_permission(member):
    if member.guild_permissions.administrator or member.guild_permissions.manage_messages:
        return True
    role_id = mod_roles.get(str(member.guild.id))
    if role_id:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            return True
    return False

@bot.event
async def on_member_join(member):
    guild = member.guild
    guild_id = str(guild.id)
    
    if guild_id in welcome_config:
        data = welcome_config[guild_id]
        channel = guild.get_channel(data.get("channel_id"))
        if channel:
            raw_message = data.get("message", "ط£ظ‡ظ„ط§ظ‹ ط¨ظƒ {user} ظپظٹ ط§ظ„ط³ظٹط±ظپط±!")
            show_user = data.get("show_user", True)
            count = guild.member_count
            
            formatted_message = raw_message.replace("{count}", str(count))\
                                          .replace("{user}", member.mention if show_user else member.name)\
                                          .replace("{username}", member.name)\
                                          .replace("{server}", guild.name)

            embed = discord.Embed(title="ًں‘‹ ط¹ط¶ظˆ ط¬ط¯ظٹط¯!", description=formatted_message, color=discord.Color.green(), timestamp=datetime.utcnow())
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            try:
                await channel.send(content=member.mention if show_user else None, embed=embed)
            except:
                pass

    cfg = load_json(CONFIG_FILE, {})
    role_id = cfg.get(guild_id, {}).get("autorole_id")
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try: await member.add_roles(role)
            except: pass

    await update_member_count(guild)
    await send_log(guild, "ًں“¥ ط¯ط®ظˆظ„ ط¹ط¶ظˆ", f"ط§ظ„ط¹ط¶ظˆ: {member.mention} (`{member.id}`)", discord.Color.green())

@bot.event
async def on_member_remove(member):
    await update_member_count(member.guild)
    await send_log(member.guild, "ًں“¤ ط®ط±ظˆط¬ ط¹ط¶ظˆ", f"ط§ظ„ط¹ط¶ظˆ: {member.mention} (`{member.id}`)", discord.Color.dark_red())

# ==================================
# ظپط­طµ ط§ظ„ط­ظ…ط§ظٹط© ط§ظ„ظ…طھظ‚ط¯ظ… (Anti Check)
# ==================================

async def anti_check(message):
    if not message.guild or message.author.bot or has_mod_permission(message.author):
        return False

    config = anti_config.get(str(message.guild.id), {})
    content = message.content.lower()
    prot = protection_config.get(str(message.guild.id), {})

    if config.get("massmention") and message.mention_everyone:
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="Mass Mention")
        except: pass
        return True

    if config.get("mention") and len(message.mentions) >= 5:
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=3), reason="Spam Mentions")
        except: pass
        return True

    if config.get("badwords"):
        for word in bad_words:
            if word in content:
                try:
                    await message.delete()
                    await message.author.timeout(timedelta(minutes=2), reason="Bad Words")
                except: pass
                return True

    if (prot.get("anti_links") or prot.get("links")) and re.findall(r"https?://\S+", content):
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=2), reason="ط±ط§ط¨ط· ظ…ظ…ظ†ظˆط¹")
        except: pass
        return True

    if (prot.get("anti_invite") or prot.get("invites")) and ("discord.gg/" in content or "discord.com/invite/" in content):
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="ط¯ط¹ظˆط© ط¯ظٹط³ظƒظˆط±ط¯")
        except: pass
        return True

    return False

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if await anti_check(message):
        return

    guild_id = str(message.guild.id)
    user_id_str = str(message.author.id)
    if guild_id not in xp_data: xp_data[guild_id] = {}
    if user_id_str not in xp_data[guild_id]: xp_data[guild_id][user_id_str] = {"xp": 0, "level": 1}
    
    xp_data[guild_id][user_id_str]["xp"] += 1
    save_json(XP_FILE, xp_data)
    
    if xp_data[guild_id][user_id_str]["xp"] >= xp_data[guild_id][user_id_str]["level"] * 100:
        xp_data[guild_id][user_id_str]["level"] += 1
        save_json(XP_FILE, xp_data)
        await message.channel.send(f"ًںژ‰ ظ…ط¨ط±ظˆظƒ {message.author.mention} ظˆطµظ„طھ ظ„ظ„ظ…ط³طھظˆظ‰ `{xp_data[guild_id][user_id_str]['level']}`!")

    await bot.process_commands(message)

# ==================================
# ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ ط§ظ„ظ…طھط·ظˆط±
# ==================================

def has_application(guild_id, user_id):
    for app in applications_data.get(str(guild_id), []):
        if app["user_id"] == user_id and app["status"] == "pending":
            return True
    return False

class ApplyModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"طھظ‚ط¯ظٹظ… {app_type}")
        self.guild_id = str(guild_id)
        self.app_type = app_type

        type_questions = application_questions.get(self.guild_id, {}).get(app_type)
        if not type_questions:
            type_questions = application_questions.get(
                self.guild_id,
                ["ط§ط³ظ…ظƒطں", "ط¹ظ…ط±ظƒطں", "ط®ط¨ط±طھظƒطں", "ط§ط®طھظٹط§ط±ظٹ", "ط§ط®طھظٹط§ط±ظٹ"]
            )

        self.inputs = []
        for q in type_questions[:5]:
            if q and q != "ط§ط®طھظٹط§ط±ظٹ":
                item = discord.ui.TextInput(
                    label=q[:45],
                    style=discord.TextStyle.paragraph,
                    required=False
                )
                self.inputs.append(item)
                self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)

        if has_application(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message(
                "â‌Œ ظ„ط¯ظٹظƒ طھظ‚ط¯ظٹظ… ظ‚ظٹط¯ ط§ظ„ظ…ط±ط§ط¬ط¹ط© ط¨ط§ظ„ظپط¹ظ„.",
                ephemeral=True
            )
            return

        app_id = random.randint(100000, 999999)
        answers = []
        for i in self.inputs:
            answers.append(i.value or "ظ„ظ… ظٹظƒطھط¨")

        if gid not in applications_data:
            applications_data[gid] = []

        applications_data[gid].append({
            "id": app_id,
            "user_id": interaction.user.id,
            "type": self.app_type,
            "answers": answers,
            "status": "pending",
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        })

        save_all_applications()

        config = application_config.get(gid, {})
        result_channel_id = config.get("results_channel") or config.get("channel")
        result_channel = interaction.guild.get_channel(result_channel_id) if result_channel_id else None

        if result_channel:
            embed = discord.Embed(
                title="ًں“© طھظ‚ط¯ظٹظ… ط¬ط¯ظٹط¯",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="ًں‘¤ ط§ظ„ط¹ط¶ظˆ", value=interaction.user.mention, inline=False)
            embed.add_field(name="ًں“Œ ط§ظ„ظ†ظˆط¹", value=self.app_type, inline=False)

            type_questions = application_questions.get(gid, {}).get(self.app_type, ["ط§ظ„ط³ط¤ط§ظ„ 1", "ط§ظ„ط³ط¤ط§ظ„ 2", "ط§ظ„ط³ط¤ط§ظ„ 3"])
            for i, a in enumerate(answers):
                q_name = type_questions[i] if i < len(type_questions) else f"ط§ظ„ط³ط¤ط§ظ„ {i+1}"
                embed.add_field(name=q_name, value=a[:1024], inline=False)

            await result_channel.send(
                embed=embed,
                view=ApplicationControlView(interaction.user.id, app_id)
            )

        await interaction.response.send_message(
            "âœ… طھظ… ط¥ط±ط³ط§ظ„ ط§ظ„طھظ‚ط¯ظٹظ… ط¨ظ†ط¬ط§ط­.",
            ephemeral=True
        )

class ApplicationControlView(discord.ui.View):
    def __init__(self, user_id, app_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.app_id = app_id

    @discord.ui.button(
        label="ظ‚ط¨ظˆظ„",
        emoji="âœ…",
        style=discord.ButtonStyle.green
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gid = str(interaction.guild.id)

        application = None

        for app in applications_data.get(gid, []):
            if app.get("id") == self.app_id:
                application = app
                break

        if not application:
            await interaction.response.send_message(
                "â‌Œ ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط§ظ„طھظ‚ط¯ظٹظ….",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "âڑ ï¸ڈ طھظ… ط§طھط®ط§ط° ظ‚ط±ط§ط± ط¨ط´ط£ظ† ظ‡ط°ط§ ط§ظ„طھظ‚ط¯ظٹظ… ظ…ط³ط¨ظ‚ظ‹ط§.",
                ephemeral=True
            )
            return

        application["status"] = "accepted"
        application["decision_by"] = interaction.user.id
        application["decision_time"] = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M"
        )

        save_all_applications()

        member = interaction.guild.get_member(self.user_id)
        app_type = application.get("type")

        if member:
            for t in application_types.get(gid, []):
                if isinstance(t, dict) and t.get("name") == app_type:

                    role_id = t.get("role_id")

                    if role_id:
                        role = interaction.guild.get_role(role_id)

                        if role:
                            try:
                                await member.add_roles(
                                    role,
                                    reason="ظ‚ط¨ظˆظ„ ط§ظ„طھظ‚ط¯ظٹظ…"
                                )
                            except Exception as e:
                                print(f"Role error: {e}")

                    break

            try:
                await member.send(
                    f"ًںژ‰ طھظ… ظ‚ط¨ظˆظ„ طھظ‚ط¯ظٹظ…ظƒ!\n"
                    f"ًں“‹ ظ†ظˆط¹ ط§ظ„طھظ‚ط¯ظٹظ…: `{app_type}`"
                )
            except:
                pass

        if interaction.message and interaction.message.embeds:

            embed = interaction.message.embeds[0]

            embed.color = discord.Color.green()

            found = False

            for i, field in enumerate(embed.fields):

                if field.name == "ًں“Œ ط§ظ„ط­ط§ظ„ط©":

                    embed.set_field_at(
                        i,
                        name="ًں“Œ ط§ظ„ط­ط§ظ„ط©",
                        value=(
                            "ًںں¢ **ظ…ظ‚ط¨ظˆظ„**\n"
                            f"ًں‘® ط¨ظˆط§ط³ط·ط©: {interaction.user.mention}\n"
                            f"ًں•گ ط§ظ„ظˆظ‚طھ: {application['decision_time']}"
                        ),
                        inline=False
                    )

                    found = True
                    break

            if not found:
                embed.add_field(
                    name="ًں“Œ ط§ظ„ط­ط§ظ„ط©",
                    value=(
                        "ًںں¢ **ظ…ظ‚ط¨ظˆظ„**\n"
                        f"ًں‘® ط¨ظˆط§ط³ط·ط©: {interaction.user.mention}\n"
                        f"ًں•گ ط§ظ„ظˆظ‚طھ: {application['decision_time']}"
                    ),
                    inline=False
                )

            for item in self.children:
                item.disabled = True

            await interaction.message.edit(
                embed=embed,
                view=self
            )

        await interaction.response.send_message(
            "âœ… طھظ… ظ‚ط¨ظˆظ„ ط§ظ„طھظ‚ط¯ظٹظ… ظˆطھط­ط¯ظٹط« ط§ظ„ط¨ط§ظ†ظ„.",
            ephemeral=True
        )

    @discord.ui.button(
        label="ط±ظپط¶",
        emoji="â‌Œ",
        style=discord.ButtonStyle.red
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gid = str(interaction.guild.id)

        application = None

        for app in applications_data.get(gid, []):
            if app.get("id") == self.app_id:
                application = app
                break

        if not application:
            await interaction.response.send_message(
                "â‌Œ ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط§ظ„طھظ‚ط¯ظٹظ….",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "âڑ ï¸ڈ طھظ… ط§طھط®ط§ط° ظ‚ط±ط§ط± ط¨ط´ط£ظ† ظ‡ط°ط§ ط§ظ„طھظ‚ط¯ظٹظ… ظ…ط³ط¨ظ‚ظ‹ط§.",
                ephemeral=True
            )
            return

        application["status"] = "rejected"
        application["decision_by"] = interaction.user.id
        application["decision_time"] = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M"
        )

        save_all_applications()

        member = interaction.guild.get_member(self.user_id)

        if member:
            try:
                await member.send(
                    f"â‌Œ طھظ… ط±ظپط¶ طھظ‚ط¯ظٹظ…ظƒ.\n"
                    f"ًں“‹ ظ†ظˆط¹ ط§ظ„طھظ‚ط¯ظٹظ…: `{application.get('type')}`"
                )
            except:
                pass

        if interaction.message and interaction.message.embeds:

            embed = interaction.message.embeds[0]

            embed.color = discord.Color.red()

            found = False

            for i, field in enumerate(embed.fields):

                if field.name == "ًں“Œ ط§ظ„ط­ط§ظ„ط©":

                    embed.set_field_at(
                        i,
                        name="ًں“Œ ط§ظ„ط­ط§ظ„ط©",
                        value=(
                            "ًں”´ **ظ…ط±ظپظˆط¶**\n"
                            f"ًں‘® ط¨ظˆط§ط³ط·ط©: {interaction.user.mention}\n"
                            f"ًں•گ ط§ظ„ظˆظ‚طھ: {application['decision_time']}"
                        ),
                        inline=False
                    )

                    found = True
                    break

            if not found:
                embed.add_field(
                    name="ًں“Œ ط§ظ„ط­ط§ظ„ط©",
                    value=(
                        "ًں”´ **ظ…ط±ظپظˆط¶**\n"
                        f"ًں‘® ط¨ظˆط§ط³ط·ط©: {interaction.user.mention}\n"
                        f"ًں•گ ط§ظ„ظˆظ‚طھ: {application['decision_time']}"
                    ),
                    inline=False
                )

            for item in self.children:
                item.disabled = True

            await interaction.message.edit(
                embed=embed,
                view=self
            )

        await interaction.response.send_message(
            "â‌Œ طھظ… ط±ظپط¶ ط§ظ„طھظ‚ط¯ظٹظ… ظˆطھط­ط¯ظٹط« ط§ظ„ط¨ط§ظ†ظ„.",
            ephemeral=True
        )

# ==================================
# ط£ظˆط§ظ…ط± ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ (Slash Commands)
# ==================================

@bot.tree.command(
    name="application-panel",
    description="ط¥ظ†ط´ط§ط، ط¨ط§ظ†ظ„ طھظ‚ط¯ظٹظ… ظ…طھط·ظˆط±"
)
@app_commands.checks.has_permissions(administrator=True)
async def application_panel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    results_channel: discord.TextChannel,
    title: str,
    description: str,
    image: str = None
):
    gid = str(interaction.guild.id)

    config = application_config.get(gid, {})
    config.update({
        "channel": channel.id,
        "results_channel": results_channel.id,
        "title": title,
        "description": description,
        "image": image
    })
    application_config[gid] = config

    save_all_applications()

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )

    if image:
        embed.set_image(url=image)

    msg = await channel.send(
        embed=embed,
        view=ApplicationSelectView(interaction.guild.id)
    )

    persistent_panels.append({
        "type": "application",
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id
    })
    save_persistent()

    await interaction.response.send_message(
        "âœ… طھظ… ط¥ظ†ط´ط§ط، ط¨ط§ظ†ظ„ ط§ظ„طھظ‚ط¯ظٹظ… ط¨ظ†ط¬ط§ط­.",
        ephemeral=True
    )

@bot.tree.command(name="application-add-type", description="ط¥ط¶ط§ظپط© ظ†ظˆط¹ طھظ‚ط¯ظٹظ… ظ…ط¹ ط±طھط¨ط© ط®ط§طµط© ظˆطھط­ط¯ظٹط« ط§ظ„ط¨ط§ظ†ظ„ طھظ„ظ‚ط§ط¦ظٹط§ظ‹")
@app_commands.checks.has_permissions(administrator=True)
async def application_add_type(
    interaction: discord.Interaction,
    name: str,
    role: discord.Role,
    description: str = "ط¨ط¯ظˆظ† ظˆطµظپ"
):
    gid = str(interaction.guild.id)

    if gid not in application_types:
        application_types[gid] = []

    if isinstance(application_types[gid], dict):
        converted_list = []
        for k, v in application_types[gid].items():
            desc = v.get("description", "ط¨ط¯ظˆظ† ظˆطµظپ") if isinstance(v, dict) else "ط¨ط¯ظˆظ† ظˆطµظپ"
            r_id = v.get("role_id") if isinstance(v, dict) else None
            converted_list.append({"name": k, "description": desc, "role_id": r_id, "enabled": True})
        application_types[gid] = converted_list

    for app_type in application_types[gid]:
        if app_type["name"] == name:
            await interaction.response.send_message(
                "â‌Œ ظ‡ط°ط§ ط§ظ„ظ†ظˆط¹ ظ…ظˆط¬ظˆط¯ ظ…ط³ط¨ظ‚ط§ظ‹.",
                ephemeral=True
            )
            return

    application_types[gid].append({
        "name": name,
        "description": description,
        "role_id": role.id,
        "enabled": True
    })

    save_application_types()

    updated = 0

    for panel in persistent_panels:
        if panel.get("type") != "application":
            continue

        if str(panel.get("guild_id")) != gid:
            continue

        try:
            channel = interaction.guild.get_channel(
                panel["channel_id"]
            )

            if not channel:
                continue

            message = await channel.fetch_message(
                panel["message_id"]
            )

            cfg = application_config.get(gid, {})

            embed = discord.Embed(
                title=cfg.get("title", "ًں“‹ ط§ظ„طھظ‚ط¯ظٹظ…"),
                description=cfg.get("description", "ط§ط®طھط± ظ†ظˆط¹ ط§ظ„طھظ‚ط¯ظٹظ…"),
                color=discord.Color.blurple()
            )

            if cfg.get("image"):
                embed.set_image(url=cfg["image"])

            await message.edit(
                embed=embed,
                view=ApplicationSelectView(gid)
            )

            updated += 1

        except Exception as e:
            print(f"Panel update error: {e}")

    await interaction.response.send_message(
        f"âœ… طھظ…طھ ط¥ط¶ط§ظپط© ظ†ظˆط¹ ط§ظ„طھظ‚ط¯ظٹظ…: `{name}`\n"
        f"ًںژ­ ط§ظ„ط±طھط¨ط©: {role.mention}\n"
        f"ًں”„ طھظ… طھط­ط¯ظٹط« {updated} ط¨ط§ظ†ظ„ طھظ„ظ‚ط§ط¦ظٹط§ظ‹.",
        ephemeral=True
    )

@bot.tree.command(name="application-remove-type", description="ط­ط°ظپ ظ†ظˆط¹ طھظ‚ط¯ظٹظ…")
@app_commands.checks.has_permissions(administrator=True)
async def application_remove_type(interaction: discord.Interaction, name: str):
    gid = str(interaction.guild.id)
    types = application_types.get(gid, [])
    
    if isinstance(types, dict):
        if name in types:
            del types[name]
            save_all_applications()
            await interaction.response.send_message("âœ… طھظ… ط­ط°ظپ ط§ظ„ظ†ظˆط¹.", ephemeral=True)
            return
    elif isinstance(types, list):
        for i, t in enumerate(types):
            if isinstance(t, dict) and t.get("name") == name:
                types.pop(i)
                save_all_applications()
                await interaction.response.send_message("âœ… طھظ… ط­ط°ظپ ط§ظ„ظ†ظˆط¹.", ephemeral=True)
                return

    await interaction.response.send_message("â‌Œ ط§ظ„ظ†ظˆط¹ ط؛ظٹط± ظ…ظˆط¬ظˆط¯.", ephemeral=True)

@bot.tree.command(name="application-set-questions", description="طھط­ط¯ظٹط¯ ط£ط³ط¦ظ„ط© ظ†ظˆط¹ طھظ‚ط¯ظٹظ…")
@app_commands.checks.has_permissions(administrator=True)
async def application_set_questions(
    interaction: discord.Interaction,
    app_type: str,
    q1: str,
    q2: str,
    q3: str,
    q4: str = "ط§ط®طھظٹط§ط±ظٹ",
    q5: str = "ط§ط®طھظٹط§ط±ظٹ"
):
    gid = str(interaction.guild.id)
    if gid not in application_questions:
        application_questions[gid] = {}

    application_questions[gid][app_type] = [q1, q2, q3, q4, q5]
    save_all_applications()
    await interaction.response.send_message("âœ… طھظ… ط­ظپط¸ ط§ظ„ط£ط³ط¦ظ„ط©.", ephemeral=True)

@bot.tree.command(name="application-set-role", description="طھط­ط¯ظٹط¯ ط±طھط¨ط© ط§ظ„ظ…ظ‚ط¨ظˆظ„ظٹظ† ط§ظ„ط¹ط§ظ…ط© ظپظٹ ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ")
@app_commands.checks.has_permissions(administrator=True)
async def application_set_role(interaction: discord.Interaction, role: discord.Role):
    gid = str(interaction.guild.id)
    if gid not in application_config: 
        application_config[gid] = {}
    application_config[gid]["accepted_role"] = role.id
    save_all_applications()
    await interaction.response.send_message(f"âœ… ط³ظٹطھظ… ط¥ط¹ط·ط§ط، ط±طھط¨ط© {role.mention} ظ„ظ„ظ…ظ‚ط¨ظˆظ„ظٹظ† طھظ„ظ‚ط§ط¦ظٹط§ظ‹ (ط¹ط§ظ…)", ephemeral=True)

@bot.tree.command(name="application-description", description="طھط¹ط¯ظٹظ„ ظˆطµظپ ط¨ط§ظ†ظ„ ط§ظ„طھظ‚ط¯ظٹظ…")
@app_commands.checks.has_permissions(administrator=True)
async def application_description(interaction: discord.Interaction, description: str):
    gid = str(interaction.guild.id)
    application_config.setdefault(gid, {})
    application_config[gid]["description"] = description
    save_all_applications()
    await interaction.response.send_message("âœ… طھظ… طھط¹ط¯ظٹظ„ ط§ظ„ظˆطµظپ.", ephemeral=True)

@bot.tree.command(name="application-list", description="ط¹ط±ط¶ ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ ط§ظ„ط­ط§ظ„ظٹط©")
@app_commands.checks.has_permissions(administrator=True)
async def application_list(interaction: discord.Interaction):
    apps = applications_data.get(str(interaction.guild.id), [])
    if not apps:
        await interaction.response.send_message("â‌Œ ظ„ط§ ظٹظˆط¬ط¯ طھظ‚ط¯ظٹظ…ط§طھ ط­ط§ظ„ظٹط©", ephemeral=True)
        return
    embed = discord.Embed(title="ًں“‌ ظ‚ط§ط¦ظ…ط© ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ", color=discord.Color.blue())
    for app in apps[:10]:
        embed.add_field(name=f"#{app['id']} - {app['type']}", value=f"ًں‘¤ <@{app['user_id']}>\nًں“Œ ط§ظ„ط­ط§ظ„ط©: {app['status']}", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="reset-panels", description="ط¥ط¹ط§ط¯ط© طھط­ظ…ظٹظ„ ط¬ظ…ظٹط¹ ط§ظ„ط¨ط§ظ†ظ„ط§طھ")
@app_commands.checks.has_permissions(administrator=True)
async def reset_panels(interaction: discord.Interaction):
    count = 0
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=50):
                    if msg.author == bot.user:
                        if msg.components:
                            await msg.edit(view=None)
                            count += 1
            except:
                pass
    await interaction.response.send_message(f"â™»ï¸ڈ طھظ… Reset ط¹ط¯ط¯ `{count}` ط¨ط§ظ†ظ„.", ephemeral=True)

# ==================================
# Reaction Roles System
# ==================================

class ReactionRoleView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(
        label="âœ… ط£ط®ط° ط§ظ„ط±طھط¨ط©",
        style=discord.ButtonStyle.green,
        custom_id="take_role_btn"
    )
    async def take_role(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(self.role_id)

        if not role:
            await interaction.response.send_message(
                "â‌Œ ط§ظ„ط±طھط¨ط© ط؛ظٹط± ظ…ظˆط¬ظˆط¯ط©",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "âڑ ï¸ڈ ط£ظ†طھ طھظ…ظ„ظƒ ظ‡ط°ظ‡ ط§ظ„ط±طھط¨ط© ط¨ط§ظ„ظپط¹ظ„",
                ephemeral=True
            )
            return

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"âœ… طھظ… ط¥ط¹ط·ط§ط¤ظƒ ط±طھط¨ط© {role.mention}",
            ephemeral=True
        )

    @discord.ui.button(
        label="â‌Œ ط¥ط²ط§ظ„ط© ط§ظ„ط±طھط¨ط©",
        style=discord.ButtonStyle.red,
        custom_id="remove_role_btn"
    )
    async def remove_role(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(self.role_id)

        if not role:
            await interaction.response.send_message(
                "â‌Œ ط§ظ„ط±طھط¨ط© ط؛ظٹط± ظ…ظˆط¬ظˆط¯ط©",
                ephemeral=True
            )
            return

        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "âڑ ï¸ڈ ط£ظ†طھ ظ„ط§ طھظ…ظ„ظƒ ظ‡ط°ظ‡ ط§ظ„ط±طھط¨ط©",
                ephemeral=True
            )
            return

        await interaction.user.remove_roles(role)

        await interaction.response.send_message(
            f"â‌Œ طھظ… ط¥ط²ط§ظ„ط© ط±طھط¨ط© {role.mention}",
            ephemeral=True
        )

    @discord.ui.button(
        label="ًں‘¥ ط¹ط±ط¶ ط§ظ„ط£ط¹ط¶ط§ط،",
        style=discord.ButtonStyle.blurple,
        custom_id="show_role_members_btn"
    )
    async def show_members(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(self.role_id)

        if not role:
            await interaction.response.send_message(
                "â‌Œ ط§ظ„ط±طھط¨ط© ط؛ظٹط± ظ…ظˆط¬ظˆط¯ط©",
                ephemeral=True
            )
            return

        members = role.members

        if not members:
            text = "ظ„ط§ ظٹظˆط¬ط¯ ط£ط­ط¯ ظٹظ…ظ„ظƒ ظ‡ط°ظ‡ ط§ظ„ط±طھط¨ط©."
        else:
            text = "\n".join(
                [f"â€¢ {member.mention}" for member in members[:50]]
            )

            if len(members) > 50:
                text += f"\n\nظˆ {len(members) - 50} ط£ط¹ط¶ط§ط، ط¢ط®ط±ظٹظ†..."

        embed = discord.Embed(
            title=f"ًں‘¥ ط£ط¹ط¶ط§ط، ط±طھط¨ط© {role.name}",
            description=text,
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

# ==================================
# ط£ظ…ط± ط§ظ„ط³ظ„ط§ط´
# ==================================

@bot.tree.command(
    name="reaction-role",
    description="ط¥ظ†ط´ط§ط، ط¨ط§ظ†ظ„ ط£ط®ط°/ط¥ط²ط§ظ„ط© ط±طھط¨ط© ط¹ط¨ط± ط§ظ„ط£ط²ط±ط§ط±"
)
@app_commands.describe(
    channel="ط§ظ„ط±ظˆظ… ط§ظ„ظ…ط±ط§ط¯ ط¥ط±ط³ط§ظ„ ط§ظ„ط¨ط§ظ†ظ„ ط¥ظ„ظٹظ‡",
    role="ط§ظ„ط±طھط¨ط© ط§ظ„ظ…ط±ط§ط¯ ط¥ط¹ط·ط§ط¤ظ‡ط§ ظ„ظ„ط¹ط¶ظˆ",
    title="ط¹ظ†ظˆط§ظ† ط§ظ„ط±ط³ط§ظ„ط© (Embed)",
    description="ظˆطµظپ ط§ظ„ط±ط³ط§ظ„ط© (Embed)"
)
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role,
    title: str,
    description: str
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )

    view = ReactionRoleView(role.id)
    msg = await channel.send(embed=embed, view=view)

    global persistent_panels

    persistent_panels.append({
        "type": "reaction_role",
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id,
        "role_id": role.id
    })

    save_persistent()

    await interaction.response.send_message(
        f"âœ… طھظ… ط¥ظ†ط´ط§ط، ط¨ط§ظ†ظ„ ط§ظ„ط±طھط¨ط© ط¨ظ†ط¬ط§ط­ ظپظٹ {channel.mention} ظ„ط±طھط¨ط© {role.mention}",
        ephemeral=True
    )


# ==================================
# ط£ظˆط§ظ…ط± ط§ظ„ط¥ط¯ط§ط±ط© ظˆط§ظ„ط¹ظ‚ظˆط¨ط§طھ (Moderation)
# ==================================

@bot.tree.command(name="ban", description="ط­ط¸ط± ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "ظ„ط§ ظٹظˆط¬ط¯ ط³ط¨ط¨"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"ًں”¨ طھظ… ط­ط¸ط± {member.mention}")
    await send_log(interaction.guild, "ًں”¨ Ban", f"ط§ظ„ط¹ط¶ظˆ: {member.mention}\nط§ظ„ط³ط¨ط¨: {reason}", discord.Color.red())

@bot.tree.command(name="kick", description="ط·ط±ط¯ ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "ظ„ط§ ظٹظˆط¬ط¯ ط³ط¨ط¨"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"ًں‘¢ طھظ… ط·ط±ط¯ {member.mention}")

@bot.tree.command(name="mute", description="ظƒطھظ… ط¹ط¶ظˆ (Timeout)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "ظ„ط§ ظٹظˆط¬ط¯ ط³ط¨ط¨"):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(f"ًں”‡ طھظ… ظƒطھظ… {member.mention} ظ„ظ…ط¯ط© {minutes} ط¯ظ‚ظٹظ‚ط©.")

@bot.tree.command(name="unmute", description="ظپظƒ ظƒطھظ… ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None, reason="ظپظƒ ط§ظ„ظƒطھظ…")
    await interaction.response.send_message(f"ًں”ٹ طھظ… ظپظƒ ط§ظ„ظƒطھظ… ط¹ظ† {member.mention}")

@bot.tree.command(name="warn", description="طھط­ط°ظٹط± ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings = load_json(WARNINGS_FILE, {})
    gid, uid = str(interaction.guild.id), str(member.id)
    if gid not in warnings: warnings[gid] = {}
    if uid not in warnings[gid]: warnings[gid][uid] = []
    warnings[gid][uid].append({"reason": reason, "date": datetime.utcnow().strftime("%Y-%m-%d")})
    save_json(WARNINGS_FILE, warnings)
    await interaction.response.send_message(f"âڑ ï¸ڈ طھظ… طھط­ط°ظٹط± {member.mention}")

@bot.tree.command(name="clear", description="ظ…ط³ط­ ط§ظ„ط±ط³ط§ط¦ظ„")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"âœ… طھظ… ط­ط°ظپ {len(deleted)} ط±ط³ط§ظ„ط©.", ephemeral=True)

# ==================================
# ط§ظ„ط¥ط¯ط§ط±ط© ط§ظ„ظ…طھظ‚ط¯ظ…ط©
# ==================================

START_TIME = datetime.utcnow()

@bot.tree.command(name="move", description="ظ†ظ‚ظ„ ط¹ط¶ظˆ ط¥ظ„ظ‰ ط±ظˆظ… طµظˆطھظٹ")
@app_commands.checks.has_permissions(move_members=True)
async def move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
    if member.voice:
        await member.move_to(channel)
        await interaction.response.send_message(f"âœ… طھظ… ظ†ظ‚ظ„ {member.mention} ط¥ظ„ظ‰ {channel.mention}")
    else:
        await interaction.response.send_message("â‌Œ ط§ظ„ط¹ط¶ظˆ ظ„ظٹط³ ظپظٹ ط±ظˆظ… طµظˆطھظٹ.", ephemeral=True)

@bot.tree.command(name="deafen", description="طھط؛ظ…ظٹط¶ طµظˆطھ ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(deafen_members=True)
async def deafen(interaction: discord.Interaction, member: discord.Member):
    await member.edit(deafen=True)
    await interaction.response.send_message(f"ًں”‡ طھظ… طھط؛ظ…ظٹط¶ {member.mention}")

@bot.tree.command(name="undeafen", description="ط¥ظ„ط؛ط§ط، طھط؛ظ…ظٹط¶ طµظˆطھ ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(deafen_members=True)
async def undeafen(interaction: discord.Interaction, member: discord.Member):
    await member.edit(deafen=False)
    await interaction.response.send_message(f"ًں”ٹ طھظ… ط¥ظ„ط؛ط§ط، طھط؛ظ…ظٹط¶ {member.mention}")

@bot.tree.command(name="timeout", description="ط¥ط¹ط·ط§ط، طھط§ظٹظ… ط§ظˆطھ ظ„ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message(f"âڈ³ طھظ… ط¥ط¹ط·ط§ط، {member.mention} طھط§ظٹظ… ط§ظˆطھ ظ„ظ…ط¯ط© {minutes} ط¯ظ‚ظٹظ‚ط©")

@bot.tree.command(name="rolelist", description="ط¹ط±ط¶ ط±طھط¨ ط§ظ„ط³ظٹط±ظپط±")
async def rolelist(interaction: discord.Interaction):
    roles = interaction.guild.roles[1:]
    text = "\n".join([f"{r.mention}" for r in roles[:50]])
    embed = discord.Embed(title="ًں“‹ ط±طھط¨ ط§ظ„ط³ظٹط±ظپط±", description=text)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="channelinfo", description="ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ط±ظˆظ… ط§ظ„ط­ط§ظ„ظٹ")
async def channelinfo(interaction: discord.Interaction):
    channel = interaction.channel
    embed = discord.Embed(title="ًں“¢ ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ط±ظˆظ…")
    embed.add_field(name="ط§ظ„ط§ط³ظ…", value=channel.name)
    embed.add_field(name="ID", value=channel.id)
    embed.add_field(name="ط§ظ„ظ†ظˆط¹", value=str(channel.type))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="botinfo", description="ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ط¨ظˆطھ")
async def botinfo(interaction: discord.Interaction):
    embed = discord.Embed(title="ًں¤– ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ط¨ظˆطھ")
    embed.add_field(name="ط§ظ„ط§ط³ظ…", value=bot.user.name)
    embed.add_field(name="ط§ظ„ط³ظٹط±ظپط±ط§طھ", value=len(bot.guilds))
    embed.add_field(name="ط§ظ„ط£ط¹ط¶ط§ط،", value=sum(g.member_count for g in bot.guilds))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="uptime", description="ظ…ط¯ط© طھط´ط؛ظٹظ„ ط§ظ„ط¨ظˆطھ")
async def uptime(interaction: discord.Interaction):
    delta = datetime.utcnow() - START_TIME
    await interaction.response.send_message(f"âڈ±ï¸ڈ ط§ظ„ط¨ظˆطھ ظٹط¹ظ…ظ„ ظ…ظ†ط°: `{delta}`")

@bot.tree.command(name="stats", description="ط¥ط­طµط§ط¦ظٹط§طھ ط§ظ„ط³ظٹط±ظپط±")
async def stats(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title="ًں“ٹ ط¥ط­طµط§ط¦ظٹط§طھ ط§ظ„ط³ظٹط±ظپط±")
    embed.add_field(name="ط§ظ„ط£ط¹ط¶ط§ط،", value=guild.member_count)
    embed.add_field(name="ط§ظ„ط±ظˆظ…ط§طھ", value=len(guild.channels))
    embed.add_field(name="ط§ظ„ط±طھط¨", value=len(guild.roles))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="autorole", description="طھط­ط¯ظٹط¯ ط±طھط¨ط© طھظ„ظ‚ط§ط¦ظٹط©")
@app_commands.checks.has_permissions(administrator=True)
async def autorole(interaction: discord.Interaction, role: discord.Role):
    config = load_json(CONFIG_FILE, {})
    gid = str(interaction.guild.id)
    if gid not in config: config[gid] = {}
    config[gid]["autorole_id"] = role.id
    save_json(CONFIG_FILE, config)
    await interaction.response.send_message(f"âœ… طھظ… طھط­ط¯ظٹط¯ ط§ظ„ط±طھط¨ط© ط§ظ„طھظ„ظ‚ط§ط¦ظٹط© {role.mention}")

@bot.tree.command(name="set-mod-role", description="طھط­ط¯ظٹط¯ ط±طھط¨ط© ط§ظ„ط¥ط¯ط§ط±ط©")
@app_commands.checks.has_permissions(administrator=True)
async def set_mod_role(interaction: discord.Interaction, role: discord.Role):
    mod_roles[str(interaction.guild.id)] = role.id
    save_json(MOD_CONFIG_FILE, mod_roles)
    await interaction.response.send_message(f"âœ… طھظ… طھط­ط¯ظٹط¯ ط±طھط¨ط© ط§ظ„ط¥ط¯ط§ط±ط©: {role.mention}")

@bot.tree.command(name="rules", description="ط¥ط±ط³ط§ظ„ ط§ظ„ظ‚ظˆط§ظ†ظٹظ†")
@app_commands.checks.has_permissions(administrator=True)
async def rules(interaction: discord.Interaction, text: str):
    embed = discord.Embed(title="ًں“œ ط§ظ„ظ‚ظˆط§ظ†ظٹظ†", description=text, color=discord.Color.blue())
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("âœ… طھظ… ط¥ط±ط³ط§ظ„ ط§ظ„ظ‚ظˆط§ظ†ظٹظ†", ephemeral=True)

@bot.tree.command(name="poll", description="ط¥ظ†ط´ط§ط، طھطµظˆظٹطھ")
async def poll(interaction: discord.Interaction, question: str):
    embed = discord.Embed(title="ًں“ٹ طھطµظˆظٹطھ", description=question)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("âœ…")
    await msg.add_reaction("â‌Œ")
    await interaction.response.send_message("âœ… طھظ… ط¥ظ†ط´ط§ط، ط§ظ„طھطµظˆظٹطھ", ephemeral=True)

@bot.tree.command(name="nickname", description="طھط؛ظٹظٹط± ط§ط³ظ… ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, member: discord.Member, name: str):
    try:
        await member.edit(nick=name)
        await interaction.response.send_message(f"âœ… طھظ… طھط؛ظٹظٹط± ط§ط³ظ… {member.mention} ط¥ظ„ظ‰ `{name}`")
    except:
        await interaction.response.send_message("â‌Œ ظ„ط§ ط£ط³طھط·ظٹط¹ طھط؛ظٹظٹط± ط§ظ„ط§ط³ظ…", ephemeral=True)

@bot.tree.command(name="addrole", description="ط¥ط¹ط·ط§ط، ط±طھط¨ط© ظ„ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(manage_roles=True)
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"âœ… طھظ… ط¥ط¹ط·ط§ط، {member.mention} ط±طھط¨ط© {role.mention}")
    except:
        await interaction.response.send_message("â‌Œ ظ„ط§ ط£ط³طھط·ظٹط¹ ط¥ط¹ط·ط§ط، ظ‡ط°ظ‡ ط§ظ„ط±طھط¨ط©", ephemeral=True)

@bot.tree.command(name="removerole", description="ط¥ط²ط§ظ„ط© ط±طھط¨ط© ظ…ظ† ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(manage_roles=True)
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"â‌Œ طھظ… ط¥ط²ط§ظ„ط© ط±طھط¨ط© {role.mention} ظ…ظ† {member.mention}")
    except:
        await interaction.response.send_message("â‌Œ ظ„ط§ ط£ط³طھط·ظٹط¹ ط¥ط²ط§ظ„ط© ظ‡ط°ظ‡ ط§ظ„ط±طھط¨ط©", ephemeral=True)

@bot.tree.command(name="createrole", description="ط¥ظ†ط´ط§ط، ط±طھط¨ط© ط¬ط¯ظٹط¯ط©")
@app_commands.checks.has_permissions(manage_roles=True)
async def createrole(interaction: discord.Interaction, name: str):
    role = await interaction.guild.create_role(name=name)
    await interaction.response.send_message(f"âœ… طھظ… ط¥ظ†ط´ط§ط، ط§ظ„ط±طھط¨ط© {role.mention}")

@bot.tree.command(name="roleall", description="ط¥ط¹ط·ط§ط، ط±طھط¨ط© ظ„ظƒظ„ ط£ط¹ط¶ط§ط، ط§ظ„ط³ظٹط±ظپط±")
@app_commands.checks.has_permissions(administrator=True)
async def roleall(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for member in interaction.guild.members:
        if not member.bot:
            try:
                await member.add_roles(role)
                count += 1
            except:
                pass
    await interaction.followup.send(f"âœ… طھظ… ط¥ط¹ط·ط§ط، ط§ظ„ط±طھط¨ط© {role.mention} ظ„ظ€ {count} ط¹ط¶ظˆ")

@bot.tree.command(name="dm", description="ط¥ط±ط³ط§ظ„ ط±ط³ط§ظ„ط© ط®ط§طµط© ظ„ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(administrator=True)
async def dm(interaction: discord.Interaction, member: discord.Member, message: str):
    try:
        await member.send(message)
        await interaction.response.send_message("âœ… طھظ… ط¥ط±ط³ط§ظ„ ط§ظ„ط±ط³ط§ظ„ط©", ephemeral=True)
    except:
        await interaction.response.send_message("â‌Œ ظ„ط§ ظٹظ…ظƒظ† ط¥ط±ط³ط§ظ„ ط±ط³ط§ظ„ط© ظ„ظ‡ط°ط§ ط§ظ„ط¹ط¶ظˆ", ephemeral=True)

@bot.tree.command(name="announce", description="ط¥ط±ط³ط§ظ„ ط¥ط¹ظ„ط§ظ† Embed")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"ط¥ط¹ظ„ط§ظ† ط¨ظˆط§ط³ط·ط© {interaction.user}")
    await channel.send(embed=embed)
    await interaction.response.send_message("âœ… طھظ… ط¥ط±ط³ط§ظ„ ط§ظ„ط¥ط¹ظ„ط§ظ†", ephemeral=True)

@bot.tree.command(name="clearwarns", description="ظ…ط³ط­ طھط­ط°ظٹط±ط§طھ ط¹ط¶ظˆ")
@app_commands.checks.has_permissions(administrator=True)
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    warnings = load_json(WARNINGS_FILE, {})
    gid = str(interaction.guild.id)
    if gid in warnings and str(member.id) in warnings[gid]:
        del warnings[gid][str(member.id)]
        save_json(WARNINGS_FILE, warnings)
    await interaction.response.send_message("âœ… طھظ… ظ…ط³ط­ ط§ظ„طھط­ط°ظٹط±ط§طھ")

# ==================================
# ط¥ط¯ط§ط±ط© ط§ظ„ط±ظˆظ…ط§طھ (Channels)
# ==================================

@bot.tree.command(name="lock", description="ظ‚ظپظ„ ط§ظ„ط±ظˆظ…")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("ًں”’ طھظ… ظ‚ظپظ„ ط§ظ„ط±ظˆظ….")

@bot.tree.command(name="unlock", description="ظپطھط­ ط§ظ„ط±ظˆظ…")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("ًں”“ طھظ… ظپطھط­ ط§ظ„ط±ظˆظ….")

@bot.tree.command(name="slowmode", description="طھط­ط¯ظٹط¯ ط³ط±ط¹ط© ط§ظ„ط±ط³ط§ط¦ظ„")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"ًںگŒ طھظ… طھط¹ظٹظٹظ† Slowmode ط¥ظ„ظ‰ {seconds} ط«ط§ظ†ظٹط©.")

@bot.tree.command(name="hide", description="ط¥ط®ظپط§ط، ط§ظ„ط±ظˆظ…")
@app_commands.checks.has_permissions(manage_channels=True)
async def hide(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
    await interaction.response.send_message("ًں™ˆ طھظ… ط¥ط®ظپط§ط، ط§ظ„ط±ظˆظ….")

@bot.tree.command(name="unhide", description="ط¥ط¸ظ‡ط§ط± ط§ظ„ط±ظˆظ…")
@app_commands.checks.has_permissions(manage_channels=True)
async def unhide(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
    await interaction.response.send_message("ًں‘پï¸ڈ طھظ… ط¥ط¸ظ‡ط§ط± ط§ظ„ط±ظˆظ….")

# ==================================
# ظ†ط¸ط§ظ… ط§ظ„ط§ظ‚طھط±ط§ط­ط§طھ (Suggestions)
# ==================================

@bot.tree.command(name="suggestion-setup", description="ط¥ط¹ط¯ط§ط¯ ط±ظˆظ… ط§ظ„ط§ظ‚طھط±ط§ط­ط§طھ")
@app_commands.checks.has_permissions(administrator=True)
async def suggestion_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    suggestion_config[str(interaction.guild.id)] = channel.id
    save_suggestions_config()
    await interaction.response.send_message(f"âœ… طھظ… طھط¹ظٹظٹظ† ط±ظˆظ… ط§ظ„ط§ظ‚طھط±ط§ط­ط§طھ {channel.mention}", ephemeral=True)

@bot.tree.command(name="suggest", description="ط¥ط±ط³ط§ظ„ ط§ظ‚طھط±ط§ط­")
@app_commands.checks.has_permissions(manage_messages=True)
async def suggest(interaction: discord.Interaction, suggestion: str):
    channel_id = suggestion_config.get(str(interaction.guild.id))
    if not channel_id:
        await interaction.response.send_message("â‌Œ ظ„ظ… ظٹطھظ… ط¥ط¹ط¯ط§ط¯ ط±ظˆظ… ط§ظ„ط§ظ‚طھط±ط§ط­ط§طھ", ephemeral=True)
        return
    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("â‌Œ ط§ظ„ط±ظˆظ… ط؛ظٹط± ظ…ظˆط¬ظˆط¯", ephemeral=True)
        return
    embed = discord.Embed(title="ًں’، ط§ظ‚طھط±ط§ط­ ط¬ط¯ظٹط¯", description=suggestion, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    
    msg = await channel.send(embed=embed)
    await msg.add_reaction("âœ…")
    await msg.add_reaction("â‌Œ")
    
    await interaction.response.send_message("âœ… طھظ… ط¥ط±ط³ط§ظ„ ط§ظ‚طھط±ط§ط­ظƒ", ephemeral=True)

# ==================================
# ط£ظˆط§ظ…ط± ط§ظ„ط­ظ…ط§ظٹط© (Anti System)
# ==================================

@bot.tree.command(name="anti-links", description="ظ…ظ†ط¹ ط§ظ„ط±ظˆط§ط¨ط·")
@app_commands.checks.has_permissions(administrator=True)
async def anti_links(interaction: discord.Interaction, status: bool):
    gid = str(interaction.guild.id)
    if gid not in protection_config: protection_config[gid] = {}
    protection_config[gid]["anti_links"] = status
    save_json(PROTECTION_FILE, protection_config)
    await interaction.response.send_message(f"ًں”— ظ…ظ†ط¹ ط§ظ„ط±ظˆط§ط¨ط·: {'ظ…ظپط¹ظ„ âœ…' if status else 'ظ…طھظˆظ‚ظپ â‌Œ'}", ephemeral=True)

@bot.tree.command(name="anti-invite", description="ظ…ظ†ط¹ ط¯ط¹ظˆط§طھ ط§ظ„ط³ظٹط±ظپط±ط§طھ")
@app_commands.checks.has_permissions(administrator=True)
async def anti_invite(interaction: discord.Interaction, status: bool):
    gid = str(interaction.guild.id)
    if gid not in protection_config: protection_config[gid] = {}
    protection_config[gid]["anti_invite"] = status
    save_json(PROTECTION_FILE, protection_config)
    await interaction.response.send_message(f"ًںڑ« ظ…ظ†ط¹ ط§ظ„ط¯ط¹ظˆط§طھ: {'ظ…ظپط¹ظ„ âœ…' if status else 'ظ…طھظˆظ‚ظپ â‌Œ'}", ephemeral=True)

@bot.tree.command(name="badword-add", description="ط¥ط¶ط§ظپط© ظƒظ„ظ…ط© ظ…ظ…ظ†ظˆط¹ط©")
@app_commands.checks.has_permissions(administrator=True)
async def badword_add(interaction: discord.Interaction, word: str):
    if word.lower() not in bad_words:
        bad_words.append(word.lower())
        save_json(BAD_WORDS_FILE, bad_words)
    await interaction.response.send_message(f"âœ… طھظ…طھ ط¥ط¶ط§ظپط© ط§ظ„ظƒظ„ظ…ط© `{word}`", ephemeral=True)

# ==================================
# ط£ظˆط§ظ…ط± ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ (Information)
# ==================================

@bot.tree.command(name="avatar", description="ط¹ط±ط¶ طµظˆط±ط© ط§ظ„ط¹ط¶ظˆ")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"ًں–¼ï¸ڈ طµظˆط±ط© {member.name}", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="ط¹ط±ط¶ ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ط¹ط¶ظˆ")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"ًں‘¤ ظ…ط¹ظ„ظˆظ…ط§طھ {member}", color=discord.Color.blurple())
    embed.add_field(name="ًں†” ID", value=member.id, inline=False)
    embed.add_field(name="ًں“… ط¯ط®ظ„ ط§ظ„ط³ظٹط±ظپط±", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "ط؛ظٹط± ظ…ط¹ط±ظˆظپ", inline=False)
    embed.add_field(name="ًںژ­ ط§ظ„ط±طھط¨", value=" ".join([r.mention for r in member.roles[1:]]) or "ظ„ط§ ظٹظˆط¬ط¯", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="ط¹ط±ط¶ ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ط³ظٹط±ظپط±")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"ًںڈ  ظ…ط¹ظ„ظˆظ…ط§طھ {guild.name}", color=discord.Color.green())
    embed.add_field(name="ًں‘¥ ط§ظ„ط£ط¹ط¶ط§ط،", value=guild.member_count)
    embed.add_field(name="ًں“پ ط§ظ„ط±ظˆظ…ط§طھ", value=len(guild.channels))
    embed.add_field(name="ًںژ­ ط§ظ„ط±طھط¨", value=len(guild.roles))
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed)

# ==================================
# ط£ظˆط§ظ…ط± ط§ظ„ط±ط³ط§ط¦ظ„ (Say & Embed)
# ==================================

@bot.tree.command(name="say", description="ط¬ط¹ظ„ ط§ظ„ط¨ظˆطھ ظٹط±ط³ظ„ ط±ط³ط§ظ„ط©")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("âœ… طھظ… ط§ظ„ط¥ط±ط³ط§ظ„", ephemeral=True)
    await interaction.channel.send(message)

@bot.tree.command(name="embed", description="ط¥ط±ط³ط§ظ„ ط±ط³ط§ظ„ط© Embed ظ…ظ† ط§ظ„ط¨ظˆطھ")
@app_commands.checks.has_permissions(administrator=True)
async def embed_command(interaction: discord.Interaction, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), timestamp=datetime.utcnow())
    await interaction.response.send_message("âœ… طھظ… ط¥ط±ط³ط§ظ„ ط§ظ„ظ€ Embed", ephemeral=True)
    await interaction.channel.send(embed=embed)

# ==================================
# ط£ظˆط§ظ…ط± ط§ظ„ظ…ط³ط§ط¹ط¯ط© (Help)
# ==================================

@bot.tree.command(name="ping", description="ط³ط±ط¹ط© ط§ط³طھط¬ط§ط¨ط© ط§ظ„ط¨ظˆطھ")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"ًںڈ“ Pong! `{latency}ms`")

@bot.tree.command(name="help", description="ط¹ط±ط¶ ظ‚ط§ط¦ظ…ط© ط§ظ„ط£ظˆط§ظ…ط±")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="ًں¤– ط£ظˆط§ظ…ط± ط§ظ„ط¨ظˆطھ", description="ظ‚ط§ط¦ظ…ط© ط§ظ„ط£ظˆط§ظ…ط± ط§ظ„ظ…طھط§ط­ط©", color=discord.Color.blurple())
    embed.add_field(name="ًں›،ï¸ڈ ط§ظ„ط¥ط¯ط§ط±ط©", value="/ban, /kick, /mute, /warn, /clear, /lock, /unlock, /say, /embed", inline=False)
    embed.add_field(name="ًں‘‘ ط¥ط¯ط§ط±ط© ط§ظ„ط±طھط¨ ظˆط§ظ„ط£ط¹ط¶ط§ط،", value="/addrole, /removerole, /createrole, /roleall, /nickname, /dm, /announce", inline=False)
    embed.add_field(name="ًں“ٹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ", value="/avatar, /userinfo, /serverinfo, /ping", inline=False)
    embed.add_field(name="ًں“‌ ط§ظ„طھظ‚ط¯ظٹظ…ط§طھ ظˆط§ظ„طھط±ط­ظٹط¨", value="/application-panel, /application-add-type, /application-remove-type, /application-set-questions, /set-welcome, /member-count-setup", inline=False)
    embed.add_field(name="ًں›،ï¸ڈ ط§ظ„ط­ظ…ط§ظٹط©", value="/anti-links, /anti-invite, /badword-add", inline=False)
    embed.add_field(name="ًںژ® ط§ظ„ط§ظ‚طھطµط§ط¯ ظˆط§ظ„ظپط¹ط§ظ„ظٹط§طھ", value="/balance, /daily, /work, /pay, /economy-leaderboard, /profile, /achievements, /event-create, /event-info, /event-end", inline=False)
    await interaction.response.send_message(embed=embed)

# ==================================
# طھط´ط؛ظٹظ„ ط§ظ„ط¨ظˆطھ ظˆط§ظ„ط£ط­ط¯ط§ط« ط§ظ„ط¹ط§ظ…ط©
# ==================================

EVENTS_RESTORED = False

@bot.event
async def on_ready():
    global EVENTS_RESTORED

    if not EVENTS_RESTORED:
        EVENTS_RESTORED = True

        for event_id, event in events_data.items():
            if not event.get("ended") and event.get("message_id"):
                try:
                    bot.add_view(
                        EventView(event_id),
                        message_id=event["message_id"]
                    )
                except Exception as e:
                    print(f"Event View Error: {e}")

        asyncio.create_task(restore_events())

    print(f"ًں¤– Bot Online: {bot.user}")
    for panel in persistent_panels:
        try:
            ptype = panel.get("type")
            if ptype == "application":
                bot.add_view(ApplicationSelectView(panel["guild_id"]), message_id=panel["message_id"])
            elif ptype == "reaction_role":
                bot.add_view(ReactionRoleView(panel["role_id"]), message_id=panel["message_id"])
        except Exception as e:
            print(f"Failed persistent view: {e}")
            
    for panel in general_panels:
        try:
            bot.add_view(
                GeneralPanelView(
                    panel["button_name"],
                    panel["button_emoji"],
                    panel["button_description"]
                ),
                message_id=panel["message_id"]
            )
        except Exception as e:
            print(e)
            
    try:
        await bot.tree.sync()
        print("âœ… Synced Slash Commands successfully.")
    except Exception as e:
        print(f"Sync error: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("â‌Œ Token not found!")
