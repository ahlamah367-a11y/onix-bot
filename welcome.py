import os
from flask import Flask
import threading

# --- إعداد خادم الويب الوهمي لإرضاء منصة Render ---
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

# ملفات نظام التقديمات الجديد
APPLICATIONS_FILE = "applications_data.json"
APPLICATION_CONFIG_FILE = "applications_config.json"
APPLICATION_TYPES_FILE = "application_types.json"
APPLICATION_QUESTIONS_FILE = "application_questions.json"
APPLICATION_DECISIONS_FILE = "application_decisions.json"
APPLICATION_COOLDOWN_FILE = "application_cooldowns.json"

# نظام البانلات العامة الديناميكية
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

applications_data = load_json(APPLICATIONS_FILE, {})
application_config = load_json(APPLICATION_CONFIG_FILE, {})
application_types = load_json(APPLICATION_TYPES_FILE, {})
application_questions = load_json(APPLICATION_QUESTIONS_FILE, {})
application_decisions = load_json(APPLICATION_DECISIONS_FILE, {})
application_cooldowns = load_json(APPLICATION_COOLDOWN_FILE, {})

general_panels = load_json(GENERAL_PANELS_FILE, [])

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
# نظام البانلات العامة الديناميكية
# ==================================

class GeneralPanelButton(discord.ui.Button):
    def __init__(self, panel_id, button_data):
        self.panel_id = panel_id
        self.button_data = button_data

        label = button_data.get("name", "زر")
        emoji = button_data.get("emoji")

        super().__init__(
            label=label[:80],
            emoji=emoji if emoji else None,
            style=discord.ButtonStyle.secondary,
            custom_id=f"general_panel:{panel_id}:{button_data.get('id')}"
        )

    async def callback(self, interaction: discord.Interaction):
        data = general_panels

        panel = next(
            (p for p in data if p.get("id") == self.panel_id),
            None
        )

        if not panel:
            await interaction.response.send_message(
                "❌ هذا البانل لم يعد موجودًا.",
                ephemeral=True
            )
            return

        button = next(
            (
                b for b in panel.get("buttons", [])
                if b.get("id") == self.button_data.get("id")
            ),
            None
        )

        if not button:
            await interaction.response.send_message(
                "❌ هذا الزر لم يعد موجودًا.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=button.get("title", "بدون عنوان"),
            description=button.get("description", "بدون وصف"),
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )

        for field in button.get("fields", []):
            name = field.get("name")
            value = field.get("value")

            if name and value:
                embed.add_field(
                    name=name,
                    value=value,
                    inline=field.get("inline", False)
                )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class GeneralPanelView(discord.ui.View):
    def __init__(self, panel):
        super().__init__(timeout=None)

        panel_id = panel.get("id")

        for button_data in panel.get("buttons", []):
            self.add_item(
                GeneralPanelButton(
                    panel_id,
                    button_data
                )
            )


class GeneralButtonModal(discord.ui.Modal):
    def __init__(self, panel_data, button_number, total_buttons):
        super().__init__(
            title=f"إعداد الزر {button_number}/{total_buttons}"
        )

        self.panel_data = panel_data
        self.button_number = button_number
        self.total_buttons = total_buttons

        self.button_name = discord.ui.TextInput(
            label="اسم الزر",
            placeholder="مثال: شرح الرتب",
            max_length=80
        )

        self.button_emoji = discord.ui.TextInput(
            label="إيموجي الزر",
            placeholder="مثال: 📋",
            required=False,
            max_length=100
        )

        self.embed_title = discord.ui.TextInput(
            label="عنوان الـ Embed عند الضغط",
            placeholder="مثال: شرح الرتب",
            max_length=256
        )

        self.embed_description = discord.ui.TextInput(
            label="وصف الـ Embed",
            placeholder="اكتب المحتوى الذي سيظهر عند الضغط",
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.add_item(self.button_name)
        self.add_item(self.button_emoji)
        self.add_item(self.embed_title)
        self.add_item(self.embed_description)

    async def on_submit(self, interaction: discord.Interaction):
        button_data = {
            "id": str(random.randint(100000, 999999)),
            "name": self.button_name.value,
            "emoji": self.button_emoji.value or None,
            "title": self.embed_title.value,
            "description": self.embed_description.value,
            "fields": []
        }

        self.panel_data["buttons"].append(button_data)

        if len(self.panel_data["buttons"]) < self.total_buttons:
            next_number = len(self.panel_data["buttons"]) + 1
            await interaction.response.send_modal(
                GeneralButtonModal(
                    self.panel_data,
                    next_number,
                    self.total_buttons
                )
            )
            return

        panel_id = str(random.randint(100000000, 999999999))
        self.panel_data["id"] = panel_id
        self.panel_data["created_at"] = time.time()

        general_panels.append(self.panel_data)
        save_general_panels()

        view = GeneralPanelView(self.panel_data)

        embed = discord.Embed(
            title=self.panel_data["title"],
            description=self.panel_data["description"],
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            "✅ تم إنشاء البانل بنجاح!",
            ephemeral=True
        )

        await interaction.channel.send(
            embed=embed,
            view=view
        )

        bot.add_view(view)


class GeneralPanelModal(discord.ui.Modal):
    def __init__(self, button_count):
        super().__init__(title="إنشاء بانل عام")
        self.button_count = button_count

        self.panel_title = discord.ui.TextInput(
            label="عنوان البانل",
            placeholder="مثال: معلومات السيرفر",
            max_length=256
        )

        self.panel_description = discord.ui.TextInput(
            label="وصف البانل",
            placeholder="اكتب وصف البانل هنا",
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.add_item(self.panel_title)
        self.add_item(self.panel_description)

    async def on_submit(self, interaction: discord.Interaction):
        panel_data = {
            "id": None,
            "title": self.panel_title.value,
            "description": self.panel_description.value,
            "buttons": []
        }

        await interaction.response.send_modal(
            GeneralButtonModal(
                panel_data,
                1,
                self.button_count
            )
        )


@bot.tree.command(
    name="general-panel",
    description="إنشاء بانل عام بأزرار قابلة للتخصيص"
)
@app_commands.describe(
    buttons="عدد الأزرار التي تريدها من 1 إلى 5"
)
@app_commands.choices(
    buttons=[
        app_commands.Choice(name="1 زر", value=1),
        app_commands.Choice(name="2 أزرار", value=2),
        app_commands.Choice(name="3 أزرار", value=3),
        app_commands.Choice(name="4 أزرار", value=4),
        app_commands.Choice(name="5 أزرار", value=5)
    ]
)
@app_commands.checks.has_permissions(administrator=True)
async def general_panel(
    interaction: discord.Interaction,
    buttons: app_commands.Choice[int]
):
    await interaction.response.send_modal(
        GeneralPanelModal(buttons.value)
    )


async def restore_general_panels():
    for panel in general_panels:
        try:
            view = GeneralPanelView(panel)
            bot.add_view(view)
        except Exception as e:
            print(f"❌ Failed to restore general panel {panel.get('id')}: {e}")

# ==================================
# نظام AFK المتكامل
# ==================================

def save_afk():
    save_json(AFK_FILE, afk_users)

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
                title="👋 أهلًا بعودتك!",
                description=f"{message.author.mention} رجعت من وضع **AFK**.\n\n⏱️ **مدة الغياب:** `{format_afk_duration(duration)}`",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
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

@bot.tree.command(name="afk", description="تفعيل وضع AFK")
@app_commands.describe(reason="سبب الغياب - اختياري")
async def afk(interaction: discord.Interaction, reason: str = "غير متوفر"):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    guild_data = get_guild_afk(guild_id)
    if user_id in guild_data:
        await interaction.response.send_message("💤 أنت بالفعل في وضع AFK.", ephemeral=True)
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

@bot.tree.command(name="afk-status", description="عرض حالة AFK لعضو")
async def afk_status(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = get_user_afk(interaction.guild.id, member.id)
    if not data:
        await interaction.response.send_message(f"🟢 {member.mention} ليس في وضع AFK.", ephemeral=True)
        return
    started = float(data.get("started_at", time.time()))
    duration = max(0, time.time() - started)
    embed = discord.Embed(title="💤 حالة AFK", description=f"السبب: {data.get('reason')}\nالمدة: {format_afk_duration(duration)}", color=discord.Color.orange())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="afk-list", description="قائمة أعضاء AFK")
async def afk_list(interaction: discord.Interaction):
    guild_data = get_guild_afk(interaction.guild.id)
    if not guild_data:
        await interaction.response.send_message("💤 لا يوجد أعضاء في وضع AFK حالياً.", ephemeral=True)
        return
    lines = [f"👤 <@{uid}> - `{d.get('reason')}`" for uid, d in guild_data.items()]
    embed = discord.Embed(title="💤 قائمة AFK", description="\n".join(lines), color=discord.Color.orange())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="afk-remove", description="إزالة AFK عن عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def afk_remove(interaction: discord.Interaction, member: discord.Member):
    if remove_user_afk(interaction.guild.id, member.id):
        await interaction.response.send_message(f"✅ تم إزالة AFK عن {member.mention}")
    else:
        await interaction.response.send_message("❌ العضو ليس AFK.", ephemeral=True)

# ==================================
# نظام السجلات (Logs System)
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

@bot.tree.command(name="set-logs", description="تحديد روم السجلات")
@app_commands.checks.has_permissions(administrator=True)
async def set_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_json(LOGS_CONFIG_FILE, {})
    config[str(interaction.guild.id)] = channel.id
    save_json(LOGS_CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ تم ضبط روم السجلات في {channel.mention}", ephemeral=True)

@bot.tree.command(name="remove-logs", description="إلغاء روم السجلات")
@app_commands.checks.has_permissions(administrator=True)
async def remove_logs(interaction: discord.Interaction):
    config = load_json(LOGS_CONFIG_FILE, {})
    if str(interaction.guild.id) in config:
        del config[str(interaction.guild.id)]
        save_json(LOGS_CONFIG_FILE, config)
        await interaction.response.send_message("❌ تم إلغاء روم السجلات.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ الروم غير مفعل أساساً.", ephemeral=True)

# ==================================
# نظام الترحيب والعداد
# ==================================

@bot.tree.command(name="set-welcome", description="تخصيص رسالة الترحيب")
@app_commands.checks.has_permissions(administrator=True)
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str, show_user: str, show_count: str):
    welcome_config[str(interaction.guild.id)] = {
        "channel_id": channel.id,
        "message": message,
        "show_user": (show_user == "yes"),
        "show_count": (show_count == "yes")
    }
    save_json(WELCOME_CONFIG_FILE, welcome_config)
    await interaction.response.send_message(f"✅ تم حفظ الترحيب في {channel.mention}", ephemeral=True)

@bot.tree.command(name="member-count-setup", description="إعداد عداد الأعضاء")
@app_commands.checks.has_permissions(administrator=True)
async def member_count_setup(interaction: discord.Interaction, channel: discord.VoiceChannel, name: str = "👥 الأعضاء: {count}"):
    data = load_member_count()
    data[str(interaction.guild.id)] = {"channel_id": channel.id, "name": name}
    save_member_count(data)
    await channel.edit(name=name.replace("{count}", str(interaction.guild.member_count)))
    await interaction.response.send_message("✅ تم إعداد العداد بنجاح.", ephemeral=True)

async def update_member_count(guild):
    data = load_member_count()
    if str(guild.id) in data:
        channel = guild.get_channel(data[str(guild.id)]["channel_id"])
        if channel:
            await channel.edit(name=data[str(guild.id)]["name"].replace("{count}", str(guild.member_count)))

# ==================================
# الأحداث الأساسية والحماية
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
    gid = str(guild.id)
    if gid in welcome_config:
        data = welcome_config[gid]
        channel = guild.get_channel(data.get("channel_id"))
        if channel:
            msg = data.get("message", "").replace("{user}", member.mention).replace("{count}", str(guild.member_count))
            embed = discord.Embed(title="👋 عضو جديد", description=msg, color=discord.Color.green())
            await channel.send(embed=embed)
    await update_member_count(guild)

@bot.event
async def on_member_remove(member):
    await update_member_count(member.guild)

async def anti_check(message):
    if not message.guild or message.author.bot or has_mod_permission(message.author):
        return False
    return False

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    await handle_afk_message(message)
    await bot.process_commands(message)

# ==================================
# نظام التقديمات المتطور
# ==================================

def has_application(guild_id, user_id):
    for app in applications_data.get(str(guild_id), []):
        if app["user_id"] == user_id and app["status"] == "pending":
            return True
    return False

class ApplicationSelectView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = str(guild_id)
        types = application_types.get(self.guild_id, [])
        options = [discord.SelectOption(label=str(t.get("name", "تقديم"))[:100], value=str(t.get("name", "تقديم"))) for t in types if isinstance(t, dict)]
        if not options:
            options.append(discord.SelectOption(label="لا توجد أنواع تقديم", value="none"))
        
        select = discord.ui.Select(placeholder="📋 اختر نوع التقديم", options=options[:25], custom_id=f"app_select_{self.guild_id}")
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        val = interaction.data["values"][0]
        if val == "none":
            await interaction.response.send_message("❌ لا توجد أنواع تقديم متاحة.", ephemeral=True)
            return
        await interaction.response.send_modal(ApplyModal(interaction.guild.id, val))

class ApplyModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"تقديم {app_type}")
        self.guild_id = str(guild_id)
        self.app_type = app_type
        self.q1 = discord.ui.TextInput(label="السؤال الأول", style=discord.TextStyle.paragraph)
        self.add_item(self.q1)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ تم إرسال تقديمك بنجاح.", ephemeral=True)

@bot.tree.command(name="application-panel", description="إنشاء بانل التقديم")
@app_commands.checks.has_permissions(administrator=True)
async def application_panel(interaction: discord.Interaction, channel: discord.TextChannel, results_channel: discord.TextChannel, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
    msg = await channel.send(embed=embed, view=ApplicationSelectView(interaction.guild.id))
    persistent_panels.append({"type": "application", "guild_id": interaction.guild.id, "channel_id": channel.id, "message_id": msg.id})
    save_persistent()
    await interaction.response.send_message("✅ تم إنشاء بانل التقديم.", ephemeral=True)

# ==================================
# أوامر الإدارة العامة والمساعدة
# ==================================

@bot.tree.command(name="ping", description="سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! `{latency}ms`")

@bot.tree.command(name="help", description="عرض قائمة الأوامر")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 أوامر البوت", color=discord.Color.blurple())
    embed.add_field(name="📌 البانلات العامة", value="/general-panel", inline=False)
    embed.add_field(name="🛡️ الإدارة", value="/ban, /kick, /mute, /clear, /lock, /unlock", inline=False)
    embed.add_field(name="💤 نظام الـ AFK", value="/afk, /afk-status, /afk-list, /afk-remove", inline=False)
    embed.add_field(name="📝 التقديمات والترحيب", value="/application-panel, /set-welcome, /set-logs", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================================
# تشغيل البوت وإعادة تحميل الـ Views
# ==================================

@bot.event
async def on_ready():
    print(f"🤖 Bot Online: {bot.user}")

    # استعادة بانلات الأزرار العامة الديناميكية
    await restore_general_panels()

    # استعادة باقي البانلات الثابتة (مثل التقديمات وغيرها)
    for panel in persistent_panels:
        try:
            ptype = panel.get("type")
            if ptype == "application":
                bot.add_view(ApplicationSelectView(panel["guild_id"]), message_id=panel["message_id"])
        except Exception as e:
            print(f"Failed persistent view: {e}")

    try:
        await bot.tree.sync()
        print("✅ Synced Slash Commands successfully.")
        print(f"✅ Restored {len(general_panels)} general panels.")
    except Exception as e:
        print(f"Sync error: {e}")

TOKEN = os.getenv("DISTOKEN") or os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token not found!")
