import os
from flask import Flask
import threading
import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime, timedelta
import asyncio
import random
import time
import re

# --- إعداد خادم Web الوهمي لإرضاء منصة Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# تشغيل السيرفر في خلفية البوت
threading.Thread(target=run_flask, daemon=True).start()
# ---------------------------------------------

# ==================================
# إعداد البوت
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
# الملفات وقواعد البيانات
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

APPLICATIONS_FILE = "applications_data.json"
APPLICATION_CONFIG_FILE = "applications_config.json"
APPLICATION_TYPES_FILE = "application_types.json"
APPLICATION_QUESTIONS_FILE = "application_questions.json"
APPLICATION_DECISIONS_FILE = "application_decisions.json"
APPLICATION_COOLDOWN_FILE = "application_cooldowns.json"
GENERAL_PANELS_FILE = "general_panels.json"

# ==================================
# دوال التحميل والحفظ العامة
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

# تحميل البيانات عند بدء التشغيل
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
applications_data = load_json(APPLICATIONS_FILE, {})
application_config = load_json(APPLICATION_CONFIG_FILE, {})
application_types = load_json(APPLICATION_TYPES_FILE, {})
application_questions = load_json(APPLICATION_QUESTIONS_FILE, {})
application_decisions = load_json(APPLICATION_DECISIONS_FILE, {})
application_cooldowns = load_json(APPLICATION_COOLDOWN_FILE, {})
general_panels = load_json(GENERAL_PANELS_FILE, [])

def save_afk():
    save_json(AFK_FILE, afk_users)

def save_general_panels():
    save_json(GENERAL_PANELS_FILE, general_panels)

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
# نظام AFK المتكامل
# ==================================
def format_afk_duration(seconds: float):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days: parts.append(f"{days} يوم")
    if hours: parts.append(f"{hours} ساعة")
    if minutes: parts.append(f"{minutes} دقيقة")
    if seconds and not parts: parts.append(f"{seconds} ثانية")
    return " و".join(parts) if parts else "أقل من ثانية"

def get_guild_afk(guild_id):
    guild_id = str(guild_id)
    if guild_id not in afk_users:
        afk_users[guild_id] = {}
    return afk_users[guild_id]

def get_user_afk(guild_id, user_id):
    guild_data = get_guild_afk(guild_id)
    return guild_data.get(str(user_id))

def remove_user_afk(guild_id, user_id):
    guild_id = str(guild_id)
    user_id = str(user_id)
    if guild_id not in afk_users:
        return None
    data = afk_users[guild_id].pop(user_id, None)
    if not afk_users[guild_id]:
        afk_users.pop(guild_id, None)
    if data:
        save_afk()
    return data

async def handle_afk_message(message):
    if not message.guild or message.author.bot:
        return
    guild_id = str(message.guild.id)
    author_id = str(message.author.id)
    own_afk = get_user_afk(guild_id, author_id)
    if own_afk:
        removed = remove_user_afk(guild_id, author_id)
        if removed:
            started = removed.get("started_at", time.time())
            duration = max(0, time.time() - float(started))
            embed = discord.Embed(
                title="👋 أهلاً بعودتك!",
                description=f"{message.author.mention} رجعت من وضع **AFK**.\n\n⏱️ **مدة الغياب:** `{format_afk_duration(duration)}`",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text="تم إلغاء حالة AFK تلقائياً")
            try:
                await message.channel.send(embed=embed, delete_after=8)
            except:
                pass

    notified = set()
    for member in message.mentions:
        if member.bot or member.id in notified:
            continue
        notified.add(member.id)
        data = get_user_afk(guild_id, member.id)
        if not data:
            continue
        reason = data.get("reason", "لم يتم تحديد سبب")
        started = data.get("started_at", time.time())
        duration = max(0, time.time() - float(started))
        embed = discord.Embed(
            title="💤 هذا العضو في وضع AFK",
            description=f"👤 **العضو:** {member.mention}\n💬 **السبب:** {reason}\n⏱️ **منذ:** `{format_afk_duration(duration)}`",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        try:
            await message.channel.send(embed=embed, delete_after=10)
        except:
            pass

# ==================================
# أوامر AFK
# ==================================
@bot.tree.command(name="afk", description="تفعيل وضع AFK")
@app_commands.describe(reason="سبب الغياب - اختياري")
async def afk(interaction: discord.Interaction, reason: str = "غير متوفر"):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    guild_data = get_guild_afk(guild_id)
    
    if user_id in guild_data:
        await interaction.response.send_message("💤 أنت بالفعل في وضع **AFK**.", ephemeral=True)
        return

    now = time.time()
    guild_data[user_id] = {"reason": reason, "started_at": now}
    save_afk()
    
    embed = discord.Embed(
        title="💤 تم تفعيل وضع AFK",
        description=f"👤 **العضو:** {interaction.user.mention}\n💬 **السبب:** {reason}",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! `{latency}ms`")

# ==================================
# تشغيل البوت والأحداث العامة
# ==================================
@bot.event
async def on_ready():
    print(f"🤖 Bot Online: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Synced Slash Commands successfully.")
    except Exception as e:
        print(f"Sync error: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token not found!")
