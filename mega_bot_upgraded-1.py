import os
import json
import asyncio
import random
import time
import re
import threading
import sqlite3
from datetime import datetime, timedelta, timezone
from flask import Flask

import discord
from discord.ext import commands
from discord import app_commands

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
AFK_FILE = "afk.json"
REACTION_ROLES_FILE = "reaction_roles.json"
ANTI_CONFIG_FILE = "anti_config.json"
BAD_WORDS_FILE = "bad_words.json"
PANELS_FILE = "panels.json"
MEMBER_COUNT_FILE = "member_count.json"

# ملفات نظام التقديمات
APPLICATIONS_FILE = "applications_data.json"
APPLICATION_CONFIG_FILE = "applications_config.json"
APPLICATION_TYPES_FILE = "application_types.json"
APPLICATION_QUESTIONS_FILE = "application_questions.json"
APPLICATION_DECISIONS_FILE = "application_decisions.json"
APPLICATION_COOLDOWN_FILE = "application_cooldowns.json"

# ملف نظام البانلات العامة
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
            except Exception:
                return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_error(error):
    logs = load_json(ERROR_LOG_FILE, [])
    logs.append({
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "error": str(error)
    })
    save_json(ERROR_LOG_FILE, logs)

def parse_hex_color(hex_str, default_color=discord.Color.blurple()):
    if not hex_str:
        return default_color
    hex_str = hex_str.strip().lstrip('#').replace('0x', '')
    try:
        return discord.Color(int(hex_str, 16))
    except ValueError:
        return default_color

welcome_config = load_json(WELCOME_CONFIG_FILE, {})
mod_roles = load_json(MOD_CONFIG_FILE, {})
protection_config = load_json(PROTECTION_FILE, {})
suggestions = load_json(SUGGESTIONS_FILE, {})
suggestion_config = load_json(SUGGESTION_CONFIG_FILE, {})
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
                description=(
                    f"{message.author.mention} رجعت من وضع **AFK**.\n\n"
                    f"⏱️ **مدة الغياب:** `{format_afk_duration(duration)}`"
                ),
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text="تم إلغاء حالة AFK تلقائيًا")
            try:
                await message.channel.send(embed=embed, delete_after=8)
            except Exception:
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
            description=(
                f"👤 **العضو:** {member.mention}\n"
                f"💬 **السبب:** {reason}\n"
                f"⏱️ **منذ:** `{format_afk_duration(duration)}`"
            ),
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="قد يكون العضو غير متواجد حاليًا")
        try:
            await message.channel.send(embed=embed, delete_after=10)
        except Exception:
            pass

@bot.tree.command(name="afk", description="تفعيل وضع AFK")
@app_commands.describe(reason="سبب الغياب - اختياري")
async def afk(interaction: discord.Interaction, reason: str = "غير متوفر"):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    guild_data = get_guild_afk(guild_id)

    if user_id in guild_data:
        old_data = guild_data[user_id]
        old_reason = old_data.get("reason", "غير متوفر")
        embed = discord.Embed(
            title="💤 أنت بالفعل AFK",
            description=(
                f"أنت حاليًا في وضع **AFK**.\n\n"
                f"💬 **السبب الحالي:** {old_reason}\n\n"
                f"يمكنك فقط إرسال رسالة في الشات للعودة تلقائيًا."
            ),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    now = time.time()
    guild_data[user_id] = {
        "reason": reason,
        "started_at": now,
        "started_at_text": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }
    save_afk()

    embed = discord.Embed(
        title="💤 تم تفعيل وضع AFK",
        description=(
            f"👤 **العضو:** {interaction.user.mention}\n\n"
            f"💬 **السبب:** {reason}\n"
            f"🕐 **وقت التفعيل:** <t:{int(now)}:F>\n"
            f"⏱️ **منذ:** <t:{int(now)}:R>\n\n"
            f"📌 سيتم إلغاء AFK تلقائيًا عند إرسال رسالة."
        ),
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"AFK • {interaction.guild.name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="afk-status", description="عرض حالة AFK لعضو")
@app_commands.describe(member="العضو المراد فحص حالته")
async def afk_status(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = get_user_afk(interaction.guild.id, member.id)

    if not data:
        embed = discord.Embed(
            title="🟢 العضو غير AFK",
            description=f"{member.mention} ليس في وضع **AFK** حاليًا.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    started = float(data.get("started_at", time.time()))
    duration = max(0, time.time() - started)
    reason = data.get("reason", "غير متوفر")

    embed = discord.Embed(
        title="💤 حالة AFK",
        description=f"{member.mention} حاليًا في وضع **AFK**.",
        color=discord.Color.orange()
    )
    embed.add_field(name="💬 السبب", value=reason, inline=False)
    embed.add_field(name="⏱️ مدة الغياب", value=format_afk_duration(duration), inline=True)
    embed.add_field(name="🕐 بدأ AFK", value=f"<t:{int(started)}:R>", inline=True)
    embed.add_field(name="📅 الوقت", value=f"<t:{int(started)}:F>", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="نظام AFK")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="afk-list", description="عرض جميع الأعضاء الموجودين في وضع AFK")
async def afk_list(interaction: discord.Interaction):
    guild_data = get_guild_afk(interaction.guild.id)
    if not guild_data:
        embed = discord.Embed(
            title="💤 قائمة AFK",
            description="لا يوجد أي عضو في وضع AFK حاليًا.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        return

    lines = []
    for user_id, data in list(guild_data.items()):
        member = interaction.guild.get_member(int(user_id))
        if not member:
            continue

        started = float(data.get("started_at", time.time()))
        duration = max(0, time.time() - started)
        reason = data.get("reason", "غير متوفر")
        lines.append(f"👤 {member.mention}\n💬 `{reason}` • ⏱️ `{format_afk_duration(duration)}`")

    if not lines:
        embed = discord.Embed(
            title="💤 قائمة AFK",
            description="لا يوجد أي عضو في وضع AFK حاليًا.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        return

    text = "\n\n".join(lines[:20])
    if len(lines) > 20:
        text += f"\n\n📌 وهناك `{len(lines) - 20}` عضو آخر."

    embed = discord.Embed(
        title="💤 أعضاء AFK",
        description=text,
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"إجمالي AFK: {len(lines)}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="afk-remove", description="إزالة AFK عن عضو يدويًا")
@app_commands.describe(member="العضو المراد إزالة AFK عنه")
@app_commands.checks.has_permissions(manage_messages=True)
async def afk_remove(interaction: discord.Interaction, member: discord.Member):
    data = get_user_afk(interaction.guild.id, member.id)
    if not data:
        embed = discord.Embed(
            title="⚠️ العضو ليس AFK",
            description=f"{member.mention} ليس في وضع AFK حاليًا.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    started = float(data.get("started_at", time.time()))
    duration = max(0, time.time() - started)
    remove_user_afk(interaction.guild.id, member.id)

    embed = discord.Embed(
        title="✅ تم إزالة AFK",
        description=(
            f"👤 **العضو:** {member.mention}\n"
            f"⏱️ **مدة AFK:** `{format_afk_duration(duration)}`\n"
            f"👮 **بواسطة:** {interaction.user.mention}"
        ),
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)

# ==================================
# نظام البانلات العامة الديناميكية (المطورة)
# ==================================

STYLE_MAP = {
    "أزرق": discord.ButtonStyle.primary,
    "blue": discord.ButtonStyle.primary,
    "primary": discord.ButtonStyle.primary,
    "رمادي": discord.ButtonStyle.secondary,
    "grey": discord.ButtonStyle.secondary,
    "gray": discord.ButtonStyle.secondary,
    "secondary": discord.ButtonStyle.secondary,
    "أخضر": discord.ButtonStyle.success,
    "green": discord.ButtonStyle.success,
    "success": discord.ButtonStyle.success,
    "أحمر": discord.ButtonStyle.danger,
    "red": discord.ButtonStyle.danger,
    "danger": discord.ButtonStyle.danger,
}

class GeneralPanelButton(discord.ui.Button):
    def __init__(self, panel_id, button_data):
        self.panel_id = panel_id
        self.button_data = button_data

        label = button_data.get("name", "زر")
        emoji = button_data.get("emoji")
        style_key = str(button_data.get("style", "secondary")).lower()
        style = STYLE_MAP.get(style_key, discord.ButtonStyle.secondary)

        super().__init__(
            label=label[:80],
            emoji=emoji if emoji else None,
            style=style,
            custom_id=f"general_panel:{panel_id}:{button_data.get('id')}"
        )

    async def callback(self, interaction: discord.Interaction):
        data = general_panels
        panel = next((p for p in data if isinstance(p, dict) and p.get("id") == self.panel_id), None)

        if not panel:
            await interaction.response.send_message("❌ هذا البانل لم يعد موجودًا.", ephemeral=True)
            return

        button = next((b for b in panel.get("buttons", []) if b.get("id") == self.button_data.get("id")), None)

        if not button:
            await interaction.response.send_message("❌ هذا الزر لم يعد موجودًا.", ephemeral=True)
            return

        embed_color = parse_hex_color(panel.get("color"), discord.Color.blurple())
        embed = discord.Embed(
            title=button.get("title", "بدون عنوان"),
            description=button.get("description", "بدون وصف"),
            color=embed_color,
            timestamp=datetime.now(timezone.utc)
        )

        image_url = button.get("image")
        if image_url:
            embed.set_image(url=image_url)

        for field in button.get("fields", []):
            name = field.get("name")
            value = field.get("value")
            if name and value:
                embed.add_field(name=name, value=value, inline=field.get("inline", False))

        await interaction.response.send_message(embed=embed, ephemeral=True)


class GeneralPanelView(discord.ui.View):
    def __init__(self, panel):
        super().__init__(timeout=None)
        panel_id = panel.get("id")
        for button_data in panel.get("buttons", []):
            self.add_item(GeneralPanelButton(panel_id, button_data))


class OpenNextModalView(discord.ui.View):
    def __init__(self, panel_data, current_button, total_buttons):
        super().__init__(timeout=180)
        self.panel_data = panel_data
        self.current_button = current_button
        self.total_buttons = total_buttons

    @discord.ui.button(label="⚙️ متابعة إعداد الأزرار", style=discord.ButtonStyle.primary)
    async def open_modal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            GeneralButtonModal(self.panel_data, self.current_button, self.total_buttons)
        )
        self.stop()


class GeneralButtonModal(discord.ui.Modal):
    def __init__(self, panel_data, button_number, total_buttons):
        super().__init__(title=f"إعداد الزر {button_number}/{total_buttons}")
        self.panel_data = panel_data
        self.button_number = button_number
        self.total_buttons = total_buttons

        self.button_name = discord.ui.TextInput(label="اسم الزر", placeholder="مثال: شرح الرتب", max_length=80)
        self.button_emoji = discord.ui.TextInput(label="إيموجي الزر", placeholder="مثال: 📋", required=False, max_length=100)
        self.button_style = discord.ui.TextInput(
            label="لون الزر",
            placeholder="أزرق / رمادي / أخضر / أحمر (الافتراضي: رمادي)",
            required=False,
            max_length=20
        )
        self.embed_title = discord.ui.TextInput(label="عنوان الـ Embed عند الضغط", placeholder="مثال: شرح الرتب", max_length=256)
        self.embed_description = discord.ui.TextInput(
            label="وصف الـ Embed + رابط الصورة اختيارياً",
            placeholder="اكتب وصف الرسالة التي تظهر عند النقر...",
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.add_item(self.button_name)
        self.add_item(self.button_emoji)
        self.add_item(self.button_style)
        self.add_item(self.embed_title)
        self.add_item(self.embed_description)

    async def on_submit(self, interaction: discord.Interaction):
        # البحث عن رابط صورة داخل الوصف تلقائيًا إذا وُجد
        desc_text = self.embed_description.value
        button_image = None
        urls = re.findall(r'https?://\S+\.(?:png|jpg|jpeg|gif|webp)', desc_text, re.IGNORECASE)
        if urls:
            button_image = urls[0]

        button_data = {
            "id": str(random.randint(100000, 999999)),
            "name": self.button_name.value,
            "emoji": self.button_emoji.value or None,
            "style": self.button_style.value or "secondary",
            "title": self.embed_title.value,
            "description": desc_text,
            "image": button_image,
            "fields": []
        }

        self.panel_data["buttons"].append(button_data)

        if len(self.panel_data["buttons"]) < self.total_buttons:
            next_number = len(self.panel_data["buttons"]) + 1
            await interaction.response.send_message(
                f"✅ تم حفظ بيانات الزر {self.button_number}. اضغط للبدء في الزر {next_number}:",
                view=OpenNextModalView(self.panel_data, next_number, self.total_buttons),
                ephemeral=True
            )
            return

        panel_id = str(random.randint(100000000, 999999999))
        self.panel_data["id"] = panel_id
        self.panel_data["created_at"] = time.time()

        general_panels.append(self.panel_data)
        save_general_panels()

        view = GeneralPanelView(self.panel_data)
        panel_color = parse_hex_color(self.panel_data.get("color"), discord.Color.blurple())

        embed = discord.Embed(
            title=self.panel_data["title"],
            description=self.panel_data["description"],
            color=panel_color
        )
        if self.panel_data.get("image"):
            embed.set_image(url=self.panel_data["image"])

        await interaction.response.send_message("✅ تم إنشاء البانل بنجاح!", ephemeral=True)
        await interaction.channel.send(embed=embed, view=view)
        bot.add_view(view)


class GeneralPanelModal(discord.ui.Modal):
    def __init__(self, button_count):
        super().__init__(title="إنشاء بانل عام")
        self.button_count = button_count

        self.panel_title = discord.ui.TextInput(label="عنوان البانل", placeholder="مثال: معلومات السيرفر", max_length=256)
        self.panel_description = discord.ui.TextInput(
            label="وصف البانل",
            placeholder="اكتب وصف البانل هنا...",
            style=discord.TextStyle.paragraph,
            max_length=4000
        )
        self.panel_color = discord.ui.TextInput(
            label="لون البانل (Hex Code)",
            placeholder="مثال: #3498db أو ff0000 (اختياري)",
            required=False,
            max_length=10
        )
        self.panel_image = discord.ui.TextInput(
            label="رابط صورة البانل (Image URL)",
            placeholder="https://example.com/image.png (اختياري)",
            required=False,
            max_length=500
        )

        self.add_item(self.panel_title)
        self.add_item(self.panel_description)
        self.add_item(self.panel_color)
        self.add_item(self.panel_image)

    async def on_submit(self, interaction: discord.Interaction):
        panel_data = {
            "id": None,
            "title": self.panel_title.value,
            "description": self.panel_description.value,
            "color": self.panel_color.value or None,
            "image": self.panel_image.value or None,
            "buttons": []
        }
        await interaction.response.send_message(
            "✅ تم حفظ تفاصيل البانل! اضغط الزر أدناه للبدء بتعيين إعدادات الأزرار:",
            view=OpenNextModalView(panel_data, 1, self.button_count),
            ephemeral=True
        )


@bot.tree.command(name="general-panel", description="إنشاء بانل عام بأزرار قابلة للتخصيص والألوان والصور")
@app_commands.describe(buttons="عدد الأزرار التي تريدها من 1 إلى 5")
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
async def general_panel(interaction: discord.Interaction, buttons: app_commands.Choice[int]):
    await interaction.response.send_modal(GeneralPanelModal(buttons.value))


# ==================================
# البانل السريع (Single-Button Panel)
# ==================================

class LegacyGeneralPanelView(discord.ui.View):
    def __init__(self, button_name, button_emoji, button_description, color=None):
        super().__init__(timeout=None)

        button = discord.ui.Button(
            label=button_name,
            emoji=button_emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"general_panel_{button_name[:30]}"
        )
        button.callback = self.button_callback
        self.add_item(button)

        self.button_label = button_name
        self.button_description = button_description
        self.color = parse_hex_color(color, discord.Color.blurple())

    async def button_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.button_label,
            description=self.button_description,
            color=self.color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="panel", description="إنشاء بانل عام سريع مع تحديد الألوان والصورة")
@app_commands.describe(
    channel="الروم المراد الإرسال إليه",
    description="وصف البانل",
    button_name="اسم الزر",
    button_emoji="إيموجي الزر",
    button_description="الوصف الظاهر بعد الضغط على الزر",
    image="رابط صورة البانل - اختياري",
    color="كود اللون Hex - اختياري (مثال: #ff0000)"
)
@app_commands.checks.has_permissions(administrator=True)
async def panel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    description: str,
    button_name: str,
    button_emoji: str,
    button_description: str,
    image: str = None,
    color: str = None
):
    embed_color = parse_hex_color(color, discord.Color.blurple())
    embed = discord.Embed(title="📌 Panel", description=description, color=embed_color)
    if image:
        embed.set_image(url=image)

    view = LegacyGeneralPanelView(button_name, button_emoji, button_description, color)
    msg = await channel.send(embed=embed, view=view)

    general_panels.append({
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id,
        "button_name": button_name,
        "button_emoji": button_emoji,
        "button_description": button_description,
        "color": color
    })

    save_general_panels()
    await interaction.response.send_message("✅ تم إنشاء البانل وحفظه بنجاح", ephemeral=True)

# ==================================
# نظام السجلات (Logs System)
# ==================================

async def send_log(guild, title, description, color):
    config = load_json(LOGS_CONFIG_FILE, {})
    log_channel_id = config.get(str(guild.id))
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if channel:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

@bot.tree.command(name="set-logs", description="تحديد روم السجلات (Logs)")
@app_commands.describe(channel="روم السجلات")
@app_commands.checks.has_permissions(administrator=True)
async def set_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_json(LOGS_CONFIG_FILE, {})
    config[str(interaction.guild.id)] = channel.id
    save_json(LOGS_CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ تم ضبط روم السجلات بنجاح في {channel.mention}", ephemeral=True)

@bot.tree.command(name="remove-logs", description="إلغاء وتفريغ إعداد روم السجلات")
@app_commands.checks.has_permissions(administrator=True)
async def remove_logs(interaction: discord.Interaction):
    config = load_json(LOGS_CONFIG_FILE, {})
    gid = str(interaction.guild.id)
    if gid in config:
        del config[gid]
        save_json(LOGS_CONFIG_FILE, config)
        await interaction.response.send_message("❌ تم إلغاء روم السجلات بنجاح.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ روم السجلات غير مفعل أساساً.", ephemeral=True)

# ==================================
# نظام الترحيب والعداد
# ==================================

@bot.tree.command(name="set-welcome", description="تعداد وتخصيص رسالة الترحيب وأعضاء السيرفر")
@app_commands.describe(
    channel="روم الترحيب",
    message="نص رسالة الترحيب (يمكن استخدام المتغيرات)",
    show_user="هل تريد منشن العضو؟",
    show_count="هل تريد إظهار العدد؟"
)
@app_commands.choices(
    show_user=[
        app_commands.Choice(name="نعم", value="yes"),
        app_commands.Choice(name="لا", value="no")
    ],
    show_count=[
        app_commands.Choice(name="نعم", value="yes"),
        app_commands.Choice(name="لا", value="no")
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
    await interaction.response.send_message(f"✅ تم حفظ إعدادات الترحيب بنجاح في روم {channel.mention}!", ephemeral=True)

@bot.tree.command(name="welcome-test", description="تجربة رسالة الترحيب")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_test(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in welcome_config:
        await interaction.response.send_message("❌ لم يتم إعداد الترحيب بعد.", ephemeral=True)
        return
    data = welcome_config[guild_id]
    channel = interaction.guild.get_channel(data.get("channel_id"))
    if not channel:
        await interaction.response.send_message("❌ روم الترحيب غير موجود.", ephemeral=True)
        return
    message = data.get("message", "أهلاً بك {user} في السيرفر!").replace("{user}", interaction.user.mention)
    embed = discord.Embed(title="👋 تجربة ترحيب", description=message, color=discord.Color.green())
    await channel.send(content=interaction.user.mention, embed=embed)
    await interaction.response.send_message("✅ تم إرسال تجربة الترحيب.", ephemeral=True)

@bot.tree.command(name="welcome-remove", description="حذف إعداد الترحيب")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_remove(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id in welcome_config:
        del welcome_config[guild_id]
        save_json(WELCOME_CONFIG_FILE, welcome_config)
        await interaction.response.send_message("✅ تم حذف نظام الترحيب.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ نظام الترحيب غير مفعل.", ephemeral=True)

@bot.tree.command(name="member-count-setup", description="إعداد عداد الأعضاء")
@app_commands.checks.has_permissions(administrator=True)
async def member_count_setup(interaction: discord.Interaction, channel: discord.VoiceChannel, name: str = "👥 الأعضاء: {count}"):
    data = load_member_count()
    data[str(interaction.guild.id)] = {"channel_id": channel.id, "name": name}
    save_member_count(data)
    count = interaction.guild.member_count
    await channel.edit(name=name.replace("{count}", str(count)))
    await interaction.response.send_message(f"✅ تم إعداد عداد الأعضاء الحالي: `{count}`", ephemeral=True)

@bot.tree.command(name="member-count-remove", description="حذف عداد الأعضاء")
@app_commands.checks.has_permissions(administrator=True)
async def member_count_remove(interaction: discord.Interaction):
    data = load_member_count()
    guild_id = str(interaction.guild.id)
    if guild_id in data:
        del data[guild_id]
        save_member_count(data)
        await interaction.response.send_message("✅ تم حذف عداد الأعضاء.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ لا يوجد عداد أعضاء مفعل.", ephemeral=True)

async def update_member_count(guild):
    data = load_member_count()
    guild_id = str(guild.id)
    if guild_id not in data:
        return
    channel = guild.get_channel(data[guild_id]["channel_id"])
    if channel:
        try:
            await channel.edit(name=data[guild_id]["name"].replace("{count}", str(guild.member_count)))
        except Exception:
            pass

# ==================================
# التحقق من الصلاحيات والأحداث الأساسية
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
            raw_message = data.get("message", "أهلاً بك {user} في السيرفر!")
            show_user = data.get("show_user", True)
            count = guild.member_count

            formatted_message = raw_message.replace("{count}", str(count))\
                                          .replace("{user}", member.mention if show_user else member.name)\
                                          .replace("{username}", member.name)\
                                          .replace("{server}", guild.name)

            embed = discord.Embed(title="👋 عضو جديد!", description=formatted_message, color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await channel.send(content=member.mention if show_user else None, embed=embed)
            except Exception:
                pass

    cfg = load_json(CONFIG_FILE, {})
    role_id = cfg.get(guild_id, {}).get("autorole_id")
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try: await member.add_roles(role)
            except Exception: pass

    await update_member_count(guild)
    await send_log(guild, "📥 دخول عضو", f"العضو: {member.mention} (`{member.id}`)", discord.Color.green())

@bot.event
async def on_member_remove(member):
    guild_id = str(member.guild.id)
    user_id = str(member.id)

    if guild_id in afk_users:
        if user_id in afk_users[guild_id]:
            del afk_users[guild_id][user_id]
            if not afk_users[guild_id]:
                del afk_users[guild_id]
            save_afk()

    await update_member_count(member.guild)

    await send_log(
        member.guild,
        "📤 خروج عضو",
        f"العضو: {member.mention} (`{member.id}`)",
        discord.Color.dark_red()
    )

# ==================================
# فحص الحماية المتقدم (Anti Check)
# ==================================

async def anti_check(message):
    if (
        not message.guild
        or message.author.bot
        or has_mod_permission(message.author)
    ):
        return False

    config = anti_config.get(str(message.guild.id), {})
    content = message.content.lower()
    prot = protection_config.get(str(message.guild.id), {})

    if config.get("massmention") and message.mention_everyone:
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="Mass Mention")
        except Exception:
            pass
        return True

    if config.get("mention") and len(message.mentions) >= 5:
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=3), reason="Spam Mentions")
        except Exception:
            pass
        return True

    if config.get("badwords"):
        for word in bad_words:
            if word in content:
                try:
                    await message.delete()
                    await message.author.timeout(timedelta(minutes=2), reason="Bad Words")
                except Exception:
                    pass
                return True

    if (prot.get("anti_links") or prot.get("links")) and re.findall(r"https?://\S+", content):
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=2), reason="رابط ممنوع")
        except Exception:
            pass
        return True

    if (prot.get("anti_invite") or prot.get("invites")) and ("discord.gg/" in content or "discord.com/invite/" in content):
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="دعوة ديسكورد")
        except Exception:
            pass
        return True

    return False


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if await anti_check(message):
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

        if isinstance(types, dict):
            options = []
            for name, data in types.items():
                description = data.get("description", "بدون وصف") if isinstance(data, dict) else "بدون وصف"
                options.append(discord.SelectOption(label=str(name)[:100], description=str(description)[:100], value=str(name)))
        else:
            options = []
            for app_type in types:
                if not isinstance(app_type, dict) or not app_type.get("enabled", True):
                    continue
                name = app_type.get("name", "تقديم")
                description = app_type.get("description", "بدون وصف")
                options.append(discord.SelectOption(label=str(name)[:100], description=str(description)[:100], value=str(name)))

        options = options[:25]
        if not options:
            options.append(discord.SelectOption(label="لا توجد أنواع تقديم", description="لم تتم إضافة أي نوع تقديم بعد", value="none"))

        select = discord.ui.Select(
            placeholder="📋 اختر نوع التقديم",
            options=options,
            custom_id=f"application_select_{self.guild_id}"
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_type = interaction.data["values"][0]

        if selected_type == "none":
            await interaction.response.send_message("❌ لا توجد أنواع تقديم متاحة حاليًا.", ephemeral=True)
            return

        if has_application(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("❌ لديك تقديم قيد المراجعة بالفعل.", ephemeral=True)
            return

        await interaction.response.send_modal(ApplyModal(interaction.guild.id, selected_type))


class ApplyModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"تقديم {app_type}")
        self.guild_id = str(guild_id)
        self.app_type = app_type

        type_questions = application_questions.get(self.guild_id, {}).get(
            app_type, ["اسمك؟", "عمرك؟", "خبرتك؟", "لماذا تريد الانضمام؟", "أي معلومات إضافية؟"]
        )

        self.inputs = []
        for q in type_questions[:5]:
            if q and q != "اختياري":
                item = discord.ui.TextInput(label=str(q)[:45], style=discord.TextStyle.paragraph, required=False)
                self.inputs.append(item)
                self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)

        if has_application(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("❌ لديك تقديم قيد المراجعة بالفعل.", ephemeral=True)
            return

        app_id = random.randint(100000, 999999)
        answers = [item.value or "لم يكتب" for item in self.inputs]

        if gid not in applications_data:
            applications_data[gid] = []

        applications_data[gid].append({
            "id": app_id,
            "user_id": interaction.user.id,
            "type": self.app_type,
            "answers": answers,
            "status": "pending",
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        })

        save_all_applications()

        config = application_config.get(gid, {})
        result_channel_id = config.get("results_channel") or config.get("channel")
        result_channel = interaction.guild.get_channel(result_channel_id) if result_channel_id else None

        if result_channel:
            embed = discord.Embed(title="📩 تقديم جديد", color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
            embed.add_field(name="👤 العضو", value=interaction.user.mention, inline=False)
            embed.add_field(name="📌 النوع", value=self.app_type, inline=False)

            type_questions = application_questions.get(gid, {}).get(
                self.app_type, ["السؤال 1", "السؤال 2", "السؤال 3", "السؤال 4", "السؤال 5"]
            )

            for i, answer in enumerate(answers):
                q_name = type_questions[i] if i < len(type_questions) else f"السؤال {i + 1}"
                embed.add_field(name=str(q_name)[:256], value=str(answer)[:1024], inline=False)

            embed.add_field(name="📌 الحالة", value="🟡 **قيد المراجعة**", inline=False)
            await result_channel.send(embed=embed, view=ApplicationControlView(interaction.user.id, app_id))

        await interaction.response.send_message("✅ تم إرسال التقديم بنجاح.", ephemeral=True)


class ApplicationControlView(discord.ui.View):
    def __init__(self, user_id: int = 0, app_id: int = 0):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.app_id = app_id

        if app_id and user_id:
            self.accept_btn.custom_id = f"app_accept:{app_id}:{user_id}"
            self.reject_btn.custom_id = f"app_reject:{app_id}:{user_id}"

    @discord.ui.button(label="قبول", emoji="✅", style=discord.ButtonStyle.green, custom_id="app_accept_default")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        parts = button.custom_id.split(":")
        if len(parts) == 3:
            app_id = int(parts[1])
            user_id = int(parts[2])
        else:
            app_id = self.app_id
            user_id = self.user_id

        gid = str(interaction.guild.id)
        application = next((app for app in applications_data.get(gid, []) if app.get("id") == app_id), None)

        if not application:
            await interaction.response.send_message("❌ لم يتم العثور على التقديم.", ephemeral=True)
            return

        if application.get("status") != "pending":
            await interaction.response.send_message("⚠️ تم اتخاذ قرار بشأن هذا التقديم مسبقًا.", ephemeral=True)
            return

        application["status"] = "accepted"
        application["decision_by"] = interaction.user.id
        application["decision_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        save_all_applications()

        member = interaction.guild.get_member(user_id)
        app_type = application.get("type")

        if member:
            types = application_types.get(gid, [])
            if isinstance(types, dict):
                types = [{"name": name, **(data if isinstance(data, dict) else {})} for name, data in types.items()]

            for app_type_data in types:
                if not isinstance(app_type_data, dict) or app_type_data.get("name") != app_type:
                    continue
                role_id = app_type_data.get("role_id")
                if role_id:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        try:
                            await member.add_roles(role, reason="قبول التقديم")
                        except Exception as e:
                            print(f"Role error: {e}")
                break

            try:
                await member.send(f"🎉 تم قبول تقديمك!\n📋 نوع التقديم: `{app_type}`")
            except Exception:
                pass

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            status_text = f"🟢 **مقبول**\n👮 بواسطة: {interaction.user.mention}\n🕐 الوقت: {application['decision_time']}"

            found = False
            for i, field in enumerate(embed.fields):
                if field.name == "📌 الحالة":
                    embed.set_field_at(i, name="📌 الحالة", value=status_text, inline=False)
                    found = True
                    break

            if not found:
                embed.add_field(name="📌 الحالة", value=status_text, inline=False)

            for item in self.children:
                item.disabled = True

            await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message("✅ تم قبول التقديم وتحديث البانل.", ephemeral=True)

    @discord.ui.button(label="رفض", emoji="❌", style=discord.ButtonStyle.red, custom_id="app_reject_default")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        parts = button.custom_id.split(":")
        if len(parts) == 3:
            app_id = int(parts[1])
            user_id = int(parts[2])
        else:
            app_id = self.app_id
            user_id = self.user_id

        gid = str(interaction.guild.id)
        application = next((app for app in applications_data.get(gid, []) if app.get("id") == app_id), None)

        if not application:
            await interaction.response.send_message("❌ لم يتم العثور على التقديم.", ephemeral=True)
            return

        if application.get("status") != "pending":
            await interaction.response.send_message("⚠️ تم اتخاذ قرار بشأن هذا التقديم مسبقًا.", ephemeral=True)
            return

        application["status"] = "rejected"
        application["decision_by"] = interaction.user.id
        application["decision_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        save_all_applications()

        member = interaction.guild.get_member(user_id)
        if member:
            try:
                await member.send(f"❌ تم رفض تقديمك.\n📋 نوع التقديم: `{application.get('type')}`")
            except Exception:
                pass

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            status_text = f"🔴 **مرفوض**\n👮 بواسطة: {interaction.user.mention}\n🕐 الوقت: {application['decision_time']}"

            found = False
            for i, field in enumerate(embed.fields):
                if field.name == "📌 الحالة":
                    embed.set_field_at(i, name="📌 الحالة", value=status_text, inline=False)
                    found = True
                    break

            if not found:
                embed.add_field(name="📌 الحالة", value=status_text, inline=False)

            for item in self.children:
                item.disabled = True

            await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message("❌ تم رفض التقديم وتحديث البانل.", ephemeral=True)

# ================================
# أوامر نظام التقديمات (Slash Commands)
# ================================

@bot.tree.command(name="application-panel", description="إنشاء بانل تقديم متطور")
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

    embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
    if image:
        embed.set_image(url=image)

    msg = await channel.send(embed=embed, view=ApplicationSelectView(interaction.guild.id))

    persistent_panels.append({
        "type": "application",
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id
    })
    save_persistent()

    await interaction.response.send_message("✅ تم إنشاء بانل التقديم بنجاح.", ephemeral=True)

@bot.tree.command(name="application-add-type", description="إضافة نوع تقديم مع رتبة خاصة وتحديث البانل تلقائياً")
@app_commands.checks.has_permissions(administrator=True)
async def application_add_type(interaction: discord.Interaction, name: str, role: discord.Role, description: str = "بدون وصف"):
    gid = str(interaction.guild.id)
    if gid not in application_types:
        application_types[gid] = []

    if isinstance(application_types[gid], dict):
        converted_list = []
        for k, v in application_types[gid].items():
            desc = v.get("description", "بدون وصف") if isinstance(v, dict) else "بدون وصف"
            r_id = v.get("role_id") if isinstance(v, dict) else None
            converted_list.append({"name": k, "description": desc, "role_id": r_id, "enabled": True})
        application_types[gid] = converted_list

    for app_type in application_types[gid]:
        if app_type["name"] == name:
            await interaction.response.send_message("❌ هذا النوع موجود مسبقاً.", ephemeral=True)
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
        if panel.get("type") != "application" or str(panel.get("guild_id")) != gid:
            continue
        try:
            channel = interaction.guild.get_channel(panel["channel_id"])
            if not channel:
                continue
            message = await channel.fetch_message(panel["message_id"])
            cfg = application_config.get(gid, {})

            embed = discord.Embed(
                title=cfg.get("title", "📋 التقديم"),
                description=cfg.get("description", "اختر نوع التقديم"),
                color=discord.Color.blurple()
            )
            if cfg.get("image"):
                embed.set_image(url=cfg["image"])

            await message.edit(embed=embed, view=ApplicationSelectView(gid))
            updated += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Panel update error: {e}")

    await interaction.response.send_message(
        f"✅ تمت إضافة نوع التقديم: `{name}`\n🎭 الرتبة: {role.mention}\n🔄 تم تحديث {updated} بانل تلقائياً.",
        ephemeral=True
    )

@bot.tree.command(name="application-remove-type", description="حذف نوع تقديم")
@app_commands.checks.has_permissions(administrator=True)
async def application_remove_type(interaction: discord.Interaction, name: str):
    gid = str(interaction.guild.id)
    types = application_types.get(gid, [])

    if isinstance(types, dict):
        if name in types:
            del types[name]
            save_all_applications()
            await interaction.response.send_message("✅ تم حذف النوع.", ephemeral=True)
            return
    elif isinstance(types, list):
        for i, t in enumerate(types):
            if isinstance(t, dict) and t.get("name") == name:
                types.pop(i)
                save_all_applications()
                await interaction.response.send_message("✅ تم حذف النوع.", ephemeral=True)
                return

    await interaction.response.send_message("❌ النوع غير موجود.", ephemeral=True)

@bot.tree.command(name="application-set-questions", description="تحديد أسئلة نوع تقديم")
@app_commands.checks.has_permissions(administrator=True)
async def application_set_questions(
    interaction: discord.Interaction,
    app_type: str,
    q1: str,
    q2: str,
    q3: str,
    q4: str = "اختياري",
    q5: str = "اختياري"
):
    gid = str(interaction.guild.id)
    if gid not in application_questions:
        application_questions[gid] = {}

    application_questions[gid][app_type] = [q1, q2, q3, q4, q5]
    save_all_applications()
    await interaction.response.send_message("✅ تم حفظ الأسئلة.", ephemeral=True)

@bot.tree.command(name="application-set-role", description="تحديد رتبة المقبولين العامة في التقديمات")
@app_commands.checks.has_permissions(administrator=True)
async def application_set_role(interaction: discord.Interaction, role: discord.Role):
    gid = str(interaction.guild.id)
    if gid not in application_config:
        application_config[gid] = {}
    application_config[gid]["accepted_role"] = role.id
    save_all_applications()
    await interaction.response.send_message(f"✅ سيتم إعطاء رتبة {role.mention} للمقبولين تلقائياً (عام)", ephemeral=True)

@bot.tree.command(name="application-description", description="تعديل وصف بانل التقديم")
@app_commands.checks.has_permissions(administrator=True)
async def application_description(interaction: discord.Interaction, description: str):
    gid = str(interaction.guild.id)
    application_config.setdefault(gid, {})
    application_config[gid]["description"] = description
    save_all_applications()
    await interaction.response.send_message("✅ تم تعديل الوصف.", ephemeral=True)

@bot.tree.command(name="application-list", description="عرض التقديمات الحالية")
@app_commands.checks.has_permissions(administrator=True)
async def application_list(interaction: discord.Interaction):
    apps = applications_data.get(str(interaction.guild.id), [])
    if not apps:
        await interaction.response.send_message("❌ لا يوجد تقديمات حالية", ephemeral=True)
        return
    embed = discord.Embed(title="📝 قائمة التقديمات", color=discord.Color.blue())
    for app in apps[:10]:
        embed.add_field(name=f"#{app['id']} - {app['type']}", value=f"👤 <@{app['user_id']}>\n📌 الحالة: {app['status']}", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="reset-panels", description="إزالة الأزرار من البانلات القديمة بأمان")
@app_commands.checks.has_permissions(administrator=True)
async def reset_panels(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    checked = 0

    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=50):
                    checked += 1
                    if msg.author != bot.user or not msg.components:
                        continue
                    try:
                        await msg.edit(view=None)
                        count += 1
                        await asyncio.sleep(0.5)
                    except discord.HTTPException as e:
                        if e.status == 429:
                            await asyncio.sleep(5)
                        else:
                            print(f"Panel edit error: {e}")
            except discord.Forbidden:
                continue
            except Exception as e:
                print(f"Reset error in #{channel.name}: {e}")

    await interaction.followup.send(f"♻️ تم Reset عدد `{count}` بانل.\n🔎 تم فحص `{checked}` رسالة.", ephemeral=True)

# ==================================
# Reaction Roles System
# ==================================

class ReactionRoleView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="✅ أخذ الرتبة", style=discord.ButtonStyle.green, custom_id="take_role_btn")
    async def take_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("⚠️ أنت تملك هذه الرتبة بالفعل", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ تم إعطاؤك رتبة {role.mention}", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ ليس لدي صلاحيات لإعطائك هذه الرتبة", ephemeral=True)

    @discord.ui.button(label="❌ إزالة الرتبة", style=discord.ButtonStyle.red, custom_id="remove_role_btn")
    async def remove_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)
            return

        if role not in interaction.user.roles:
            await interaction.response.send_message("⚠️ أنت لا تملك هذه الرتبة", ephemeral=True)
            return

        try:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ تم إزالة رتبة {role.mention}", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ ليس لدي صلاحيات لإزالة هذه الرتبة", ephemeral=True)

    @discord.ui.button(label="👥 عرض الأعضاء", style=discord.ButtonStyle.blurple, custom_id="show_role_members_btn")
    async def show_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)
            return

        members = role.members
        if not members:
            text = "لا يوجد أحد يملك هذه الرتبة."
        else:
            text = "\n".join([f"• {member.mention}" for member in members[:50]])
            if len(members) > 50:
                text += f"\n\nو {len(members) - 50} أعضاء آخرين..."

        embed = discord.Embed(title=f"👥 أعضاء رتبة {role.name}", description=text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="reaction-role", description="إنشاء بانل أخذ/إزالة رتبة عبر الأزرار")
@app_commands.describe(
    channel="الروم المراد إرسال البانل إليه",
    role="الرتبة المراد إعطاؤها للعضو",
    title="عنوان الرسالة (Embed)",
    description="وصف الرسالة (Embed)"
)
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
    view = ReactionRoleView(role.id)
    msg = await channel.send(embed=embed, view=view)

    persistent_panels.append({
        "type": "reaction_role",
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id,
        "role_id": role.id
    })
    save_persistent()

    await interaction.response.send_message(f"✅ تم إنشاء بانل الرتبة بنجاح في {channel.mention} لرتبة {role.mention}", ephemeral=True)

# ==================================
# أوامر الإدارة والعقوبات (Moderation)
# ==================================

@bot.tree.command(name="ban", description="حظر عضو")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 تم حظر {member.mention}")
        await send_log(interaction.guild, "🔨 Ban", f"العضو: {member.mention}\nالسبب: {reason}", discord.Color.red())
    except Exception:
        await interaction.response.send_message("❌ لا أمتلك الصلاحيات الكافية لحظر هذا العضو.", ephemeral=True)

@bot.tree.command(name="kick", description="طرد عضو")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👢 تم طرد {member.mention}")
    except Exception:
        await interaction.response.send_message("❌ لا أمتلك الصلاحيات الكافية لطرد هذا العضو.", ephemeral=True)

@bot.tree.command(name="mute", description="كتم عضو (Timeout)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "لا يوجد سبب"):
    try:
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await interaction.response.send_message(f"🔇 تم كتم {member.mention} لمدة {minutes} دقيقة.")
    except Exception:
        await interaction.response.send_message("❌ لا أمتلك الصلاحيات الكافية لكتم هذا العضو.", ephemeral=True)

@bot.tree.command(name="unmute", description="فك كتم عضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.timeout(None, reason="فك الكتم")
        await interaction.response.send_message(f"🔊 تم فك الكتم عن {member.mention}")
    except Exception:
        await interaction.response.send_message("❌ لا أمتلك الصلاحيات الكافية لفك كتم هذا العضو.", ephemeral=True)

@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings = load_json(WARNINGS_FILE, {})
    gid, uid = str(interaction.guild.id), str(member.id)
    if gid not in warnings: warnings[gid] = {}
    if uid not in warnings[gid]: warnings[gid][uid] = []
    warnings[gid][uid].append({"reason": reason, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")})
    save_json(WARNINGS_FILE, warnings)
    await interaction.response.send_message(f"⚠️ تم تحذير {member.mention}")

@bot.tree.command(name="clear", description="مسح الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم حذف {len(deleted)} رسالة.", ephemeral=True)

# ==================================
# الإدارة المتقدمة
# ==================================

START_TIME = datetime.now(timezone.utc)

@bot.tree.command(name="move", description="نقل عضو إلى روم صوتي")
@app_commands.checks.has_permissions(move_members=True)
async def move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
    if member.voice:
        try:
            await member.move_to(channel)
            await interaction.response.send_message(f"✅ تم نقل {member.mention} إلى {channel.mention}")
        except Exception:
            await interaction.response.send_message("❌ لا يملك البوت الصلاحيات لنقل العضو.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي.", ephemeral=True)

@bot.tree.command(name="deafen", description="تغميض صوت عضو")
@app_commands.checks.has_permissions(deafen_members=True)
async def deafen(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.edit(deafen=True)
        await interaction.response.send_message(f"🔇 تم تغميض {member.mention}")
    except Exception:
        await interaction.response.send_message("❌ لا أملك صلاحية تغميض العضو.", ephemeral=True)

@bot.tree.command(name="undeafen", description="إلغاء تغميض صوت عضو")
@app_commands.checks.has_permissions(deafen_members=True)
async def undeafen(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.edit(deafen=False)
        await interaction.response.send_message(f"🔊 تم إلغاء تغميض {member.mention}")
    except Exception:
        await interaction.response.send_message("❌ لا أملك صلاحية إلغاء تغميض العضو.", ephemeral=True)

@bot.tree.command(name="timeout", description="إعطاء تايم اوت لعضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    try:
        await member.timeout(timedelta(minutes=minutes))
        await interaction.response.send_message(f"⏳ تم إعطاء {member.mention} تايم اوت لمدة {minutes} دقيقة")
    except Exception:
        await interaction.response.send_message("❌ فشل إعطاء تايم اوت للعضو.", ephemeral=True)

@bot.tree.command(name="rolelist", description="عرض رتب السيرفر")
async def rolelist(interaction: discord.Interaction):
    roles = interaction.guild.roles[1:]
    text = "\n".join([f"{r.mention}" for r in roles[:50]])
    embed = discord.Embed(title="📋 رتب السيرفر", description=text or "لا توجد رتب.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="channelinfo", description="معلومات الروم الحالي")
async def channelinfo(interaction: discord.Interaction):
    channel = interaction.channel
    embed = discord.Embed(title="📢 معلومات الروم")
    embed.add_field(name="الاسم", value=channel.name)
    embed.add_field(name="ID", value=channel.id)
    embed.add_field(name="النوع", value=str(channel.type))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="botinfo", description="معلومات البوت")
async def botinfo(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 معلومات البوت")
    embed.add_field(name="الاسم", value=bot.user.name)
    embed.add_field(name="السيرفرات", value=len(bot.guilds))
    embed.add_field(name="الأعضاء", value=sum(g.member_count for g in bot.guilds))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="uptime", description="مدة تشغيل البوت")
async def uptime(interaction: discord.Interaction):
    delta = datetime.now(timezone.utc) - START_TIME
    await interaction.response.send_message(f"⏱️ البوت يعمل منذ: `{delta}`")

@bot.tree.command(name="stats", description="إحصائيات السيرفر")
async def stats(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title="📊 إحصائيات السيرفر")
    embed.add_field(name="الأعضاء", value=guild.member_count)
    embed.add_field(name="الرومات", value=len(guild.channels))
    embed.add_field(name="الرتب", value=len(guild.roles))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="autorole", description="تحديد رتبة تلقائية")
@app_commands.checks.has_permissions(administrator=True)
async def autorole(interaction: discord.Interaction, role: discord.Role):
    config = load_json(CONFIG_FILE, {})
    gid = str(interaction.guild.id)
    if gid not in config: config[gid] = {}
    config[gid]["autorole_id"] = role.id
    save_json(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ تم تحديد الرتبة التلقائية {role.mention}")

@bot.tree.command(name="set-mod-role", description="تحديد رتبة الإدارة")
@app_commands.checks.has_permissions(administrator=True)
async def set_mod_role(interaction: discord.Interaction, role: discord.Role):
    mod_roles[str(interaction.guild.id)] = role.id
    save_json(MOD_CONFIG_FILE, mod_roles)
    await interaction.response.send_message(f"✅ تم تحديد رتبة الإدارة: {role.mention}")

@bot.tree.command(name="rules", description="إرسال القوانين")
@app_commands.checks.has_permissions(administrator=True)
async def rules(interaction: discord.Interaction, text: str):
    embed = discord.Embed(title="📜 القوانين", description=text, color=discord.Color.blue())
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ تم إرسال القوانين", ephemeral=True)

@bot.tree.command(name="poll", description="إنشاء تصويت")
async def poll(interaction: discord.Interaction, question: str):
    embed = discord.Embed(title="📊 تصويت", description=question)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    await interaction.response.send_message("✅ تم إنشاء التصويت", ephemeral=True)

@bot.tree.command(name="nickname", description="تغيير اسم عضو")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, member: discord.Member, name: str):
    try:
        await member.edit(nick=name)
        await interaction.response.send_message(f"✅ تم تغيير اسم {member.mention} إلى `{name}`")
    except Exception:
        await interaction.response.send_message("❌ لا أستطيع تغيير الاسم", ephemeral=True)

@bot.tree.command(name="addrole", description="إعطاء رتبة لعضو")
@app_commands.checks.has_permissions(manage_roles=True)
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ تم إعطاء {member.mention} رتبة {role.mention}")
    except Exception:
        await interaction.response.send_message("❌ لا أستطيع إعطاء هذه الرتبة", ephemeral=True)

@bot.tree.command(name="removerole", description="إزالة رتبة من عضو")
@app_commands.checks.has_permissions(manage_roles=True)
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"❌ تم إزالة رتبة {role.mention} من {member.mention}")
    except Exception:
        await interaction.response.send_message("❌ لا أستطيع إزالة هذه الرتبة", ephemeral=True)

@bot.tree.command(name="createrole", description="إنشاء رتبة جديدة")
@app_commands.checks.has_permissions(manage_roles=True)
async def createrole(interaction: discord.Interaction, name: str):
    try:
        role = await interaction.guild.create_role(name=name)
        await interaction.response.send_message(f"✅ تم إنشاء الرتبة {role.mention}")
    except Exception:
        await interaction.response.send_message("❌ فشل إنشاء الرتبة.", ephemeral=True)

@bot.tree.command(name="roleall", description="إعطاء رتبة لكل أعضاء السيرفر")
@app_commands.checks.has_permissions(administrator=True)
async def roleall(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for member in interaction.guild.members:
        if not member.bot:
            try:
                await member.add_roles(role)
                count += 1
            except Exception:
                pass
    await interaction.followup.send(f"✅ تم إعطاء الرتبة {role.mention} لـ {count} عضو")

@bot.tree.command(name="dm", description="إرسال رسالة خاصة لعضو")
@app_commands.checks.has_permissions(administrator=True)
async def dm(interaction: discord.Interaction, member: discord.Member, message: str):
    try:
        await member.send(message)
        await interaction.response.send_message("✅ تم إرسال الرسالة", ephemeral=True)
    except Exception:
        await interaction.response.send_message("❌ لا يمكن إرسال رسالة لهذا العضو", ephemeral=True)

@bot.tree.command(name="announce", description="إرسال إعلان Embed")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
    embed.set_footer(text=f"إعلان بواسطة {interaction.user}")
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ تم إرسال الإعلان", ephemeral=True)

@bot.tree.command(name="warnings", description="عرض تحذيرات عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def warnings_command(interaction: discord.Interaction, member: discord.Member):
    warnings = load_json(WARNINGS_FILE, {})
    gid, uid = str(interaction.guild.id), str(member.id)
    member_warnings = warnings.get(gid, {}).get(uid, [])

    embed = discord.Embed(
        title="⚠️ تحذيرات العضو",
        description=f"👤 **العضو:** {member.mention}\n🔢 **عدد التحذيرات:** `{len(member_warnings)}`",
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    if not member_warnings:
        embed.description += "\n\n✅ لا يوجد على هذا العضو أي تحذيرات."
    else:
        for i, warning in enumerate(member_warnings[:25], 1):
            reason = warning.get("reason", "لا يوجد سبب") if isinstance(warning, dict) else str(warning)
            date = warning.get("date", "غير معروف") if isinstance(warning, dict) else "غير معروف"
            embed.add_field(
                name=f"⚠️ التحذير رقم {i}",
                value=f"📝 **السبب:** {reason}\n📅 **التاريخ:** `{date}`",
                inline=False
            )

        if len(member_warnings) > 25:
            embed.set_footer(text=f"تم عرض أول 25 تحذير من أصل {len(member_warnings)}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="clearwarns", description="مسح تحذيرات عضو")
@app_commands.checks.has_permissions(administrator=True)
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    warnings = load_json(WARNINGS_FILE, {})
    gid = str(interaction.guild.id)
    if gid in warnings and str(member.id) in warnings[gid]:
        del warnings[gid][str(member.id)]
        save_json(WARNINGS_FILE, warnings)
    await interaction.response.send_message("✅ تم مسح التحذيرات")

# ==================================
# إدارة الرومات (Channels)
# ==================================

@bot.tree.command(name="lock", description="قفل الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل الروم.")

@bot.tree.command(name="unlock", description="فتح الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح الروم.")

@bot.tree.command(name="slowmode", description="تحديد سرعة الرسائل")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"🐌 تم تعيين Slowmode إلى {seconds} ثانية.")

@bot.tree.command(name="hide", description="إخفاء الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def hide(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
    await interaction.response.send_message("🙈 تم إخفاء الروم.")

@bot.tree.command(name="unhide", description="إظهار الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def unhide(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
    await interaction.response.send_message("👁️ تم إظهار الروم.")

# ==================================
# نظام الاقتراحات (Suggestions)
# ==================================

@bot.tree.command(name="suggestion-setup", description="إعداد روم الاقتراحات")
@app_commands.checks.has_permissions(administrator=True)
async def suggestion_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    suggestion_config[str(interaction.guild.id)] = channel.id
    save_suggestions_config()
    await interaction.response.send_message(f"✅ تم تعيين روم الاقتراحات {channel.mention}", ephemeral=True)

@bot.tree.command(name="suggest", description="إرسال اقتراح")
async def suggest(interaction: discord.Interaction, suggestion: str):
    channel_id = suggestion_config.get(str(interaction.guild.id))
    if not channel_id:
        await interaction.response.send_message("❌ لم يتم إعداد روم الاقتراحات", ephemeral=True)
        return
    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ الروم غير موجود", ephemeral=True)
        return

    embed = discord.Embed(title="💡 اقتراح جديد", description=suggestion, color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    await interaction.response.send_message("✅ تم إرسال اقتراحك", ephemeral=True)

# ==================================
# أوامر الحماية (Anti System)
# ==================================

@bot.tree.command(name="anti-links", description="منع الروابط")
@app_commands.checks.has_permissions(administrator=True)
async def anti_links(interaction: discord.Interaction, status: bool):
    gid = str(interaction.guild.id)
    if gid not in protection_config: protection_config[gid] = {}
    protection_config[gid]["anti_links"] = status
    save_json(PROTECTION_FILE, protection_config)
    await interaction.response.send_message(f"🔗 منع الروابط: {'مفعل ✅' if status else 'متوقف ❌'}", ephemeral=True)

@bot.tree.command(name="anti-invite", description="منع دعوات السيرفرات")
@app_commands.checks.has_permissions(administrator=True)
async def anti_invite(interaction: discord.Interaction, status: bool):
    gid = str(interaction.guild.id)
    if gid not in protection_config: protection_config[gid] = {}
    protection_config[gid]["anti_invite"] = status
    save_json(PROTECTION_FILE, protection_config)
    await interaction.response.send_message(f"🚫 منع الدعوات: {'مفعل ✅' if status else 'متوقف ❌'}", ephemeral=True)

@bot.tree.command(name="badword-add", description="إضافة كلمة ممنوعة")
@app_commands.checks.has_permissions(administrator=True)
async def badword_add(interaction: discord.Interaction, word: str):
    if word.lower() not in bad_words:
        bad_words.append(word.lower())
        save_json(BAD_WORDS_FILE, bad_words)
    await interaction.response.send_message(f"✅ تمت إضافة الكلمة `{word}`", ephemeral=True)

# ==================================
# أوامر المعلومات (Information)
# ==================================

@bot.tree.command(name="avatar", description="عرض صورة العضو")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"🖼️ صورة {member.name}", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="عرض معلومات العضو")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"👤 معلومات {member}", color=discord.Color.blurple())
    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📅 دخل السيرفر", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "غير معروف", inline=False)
    embed.add_field(name="🎭 الرتب", value=" ".join([r.mention for r in member.roles[1:]]) or "لا يوجد", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="عرض معلومات السيرفر")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"🏠 معلومات {guild.name}", color=discord.Color.green())
    embed.add_field(name="👥 الأعضاء", value=guild.member_count)
    embed.add_field(name="📁 الرومات", value=len(guild.channels))
    embed.add_field(name="🎭 الرتب", value=len(guild.roles))
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed)

# ==================================
# أوامر الرسائل (Say & Embed)
# ==================================

@bot.tree.command(name="say", description="جعل البوت يرسل رسالة")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("✅ تم الإرسال", ephemeral=True)
    await interaction.channel.send(message)

@bot.tree.command(name="embed", description="إرسال رسالة Embed من البوت")
@app_commands.checks.has_permissions(administrator=True)
async def embed_command(interaction: discord.Interaction, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
    await interaction.response.send_message("✅ تم إرسال الـ Embed", ephemeral=True)
    await interaction.channel.send(embed=embed)

# ==================================
# أوامر المساعدة (Help)
# ==================================

@bot.tree.command(name="ping", description="سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! `{latency}ms`")

@bot.tree.command(name="help", description="عرض قائمة الأوامر")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 أوامر البوت", description="قائمة الأوامر المتاحة", color=discord.Color.blurple())
    embed.add_field(name="🛡️ الإدارة", value="/ban, /kick, /mute, /warn, /clear, /lock, /unlock, /say, /embed", inline=False)
    embed.add_field(name="👑 إدارة الرتب والأعضاء", value="/addrole, /removerole, /createrole, /roleall, /nickname, /dm, /announce", inline=False)
    embed.add_field(name="📊 المعلومات", value="/avatar, /userinfo, /serverinfo, /ping", inline=False)
    embed.add_field(name="📝 التقديمات والترحيب", value="/application-panel, /application-add-type, /application-remove-type, /application-set-questions, /set-welcome, /member-count-setup", inline=False)
    embed.add_field(name="🔘 البانلات العامة", value="/general-panel, /panel", inline=False)
    embed.add_field(name="🛡️ الحماية", value="/anti-links, /anti-invite, /badword-add", inline=False)
    embed.add_field(name="💤 نظام الـ AFK", value="/afk, /afk-status, /afk-list, /afk-remove", inline=False)
    await interaction.response.send_message(embed=embed)

# ==================================
# تشغيل البوت والأحداث العامة
# ==================================

@bot.event
async def on_ready():
    print(f"🤖 Bot Online: {bot.user}")

    # إضافة Persistent View الخاصة بأزرار قبول/رفض التقديمات عامة
    bot.add_view(ApplicationControlView())

    # استعادة البانلات المعتادة للتقديمات والتفاعل
    for panel_item in persistent_panels:
        try:
            ptype = panel_item.get("type")
            if ptype == "application":
                bot.add_view(ApplicationSelectView(panel_item["guild_id"]), message_id=panel_item["message_id"])
            elif ptype == "reaction_role":
                bot.add_view(ReactionRoleView(panel_item["role_id"]), message_id=panel_item["message_id"])
        except Exception as e:
            print(f"Failed persistent view: {e}")

    # استعادة البانلات العامة (القديمة والديناميكية)
    for panel_item in general_panels:
        try:
            if isinstance(panel_item, dict):
                if "button_name" in panel_item:
                    bot.add_view(
                        LegacyGeneralPanelView(
                            panel_item["button_name"],
                            panel_item["button_emoji"],
                            panel_item["button_description"],
                            panel_item.get("color")
                        ),
                        message_id=panel_item.get("message_id")
                    )
                elif "id" in panel_item and "buttons" in panel_item:
                    bot.add_view(GeneralPanelView(panel_item))
        except Exception as e:
            print(f"Failed panel view restoration: {e}")

    # المزامنة مع سيرفرات الديسكورد
    try:
        await bot.tree.sync()
        print("✅ Synced Slash Commands successfully.")
    except Exception as e:
        print(f"Sync error: {e}")

# معالجة أخطاء الصلاحيات العامة لأوامر Slash
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ لا تمتلك الصلاحيات الكافية لاستخدام هذا الأمر.", ephemeral=True)
    else:
        save_error(error)


# ============================================================
# 🚀 ONIX MEGA EXTENSION — Tickets / SQLite / Logs / Economy
# ============================================================

MEGA_DB = os.getenv("MEGA_DB_FILE", "mega_bot.db")
_mega_db_lock = threading.Lock()

def mega_db():
    con = sqlite3.connect(MEGA_DB, timeout=30)
    con.row_factory = sqlite3.Row
    return con

def mega_init_db():
    with _mega_db_lock:
        con = mega_db()
        cur = con.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            ticket_category_id INTEGER,
            ticket_support_role_id INTEGER,
            ticket_log_channel_id INTEGER,
            ticket_open_log_channel_id INTEGER,
            ticket_close_log_channel_id INTEGER,
            ticket_note_log_channel_id INTEGER,
            ticket_action_log_channel_id INTEGER,
            ticket_claim_log_channel_id INTEGER,
            evidence_channel_id INTEGER,
            ticket_pattern TEXT DEFAULT '🎫・{count}',
            log_message_channel_id INTEGER,
            log_member_channel_id INTEGER,
            log_mod_channel_id INTEGER,
            log_ticket_channel_id INTEGER,
            log_command_channel_id INTEGER,
            automod_enabled INTEGER DEFAULT 0,
            spam_limit INTEGER DEFAULT 5,
            spam_window INTEGER DEFAULT 8
        );
        CREATE TABLE IF NOT EXISTS ticket_counters (
            guild_id INTEGER PRIMARY KEY,
            counter INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS tickets (
            guild_id INTEGER,
            channel_id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            number INTEGER,
            status TEXT DEFAULT 'open',
            claimed_by INTEGER,
            created_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS autoreplies (
            guild_id INTEGER,
            trigger TEXT,
            response TEXT,
            PRIMARY KEY(guild_id, trigger)
        );
        CREATE TABLE IF NOT EXISTS economy (
            guild_id INTEGER,
            user_id INTEGER,
            balance INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            PRIMARY KEY(guild_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS shop (
            guild_id INTEGER,
            item TEXT,
            price INTEGER,
            PRIMARY KEY(guild_id, item)
        );
        CREATE TABLE IF NOT EXISTS inventory (
            guild_id INTEGER,
            user_id INTEGER,
            item TEXT,
            amount INTEGER DEFAULT 0,
            PRIMARY KEY(guild_id, user_id, item)
        );
        CREATE TABLE IF NOT EXISTS giveaways (
            message_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            channel_id INTEGER,
            prize TEXT,
            winners INTEGER,
            end_at INTEGER,
            host_id INTEGER,
            ended INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS moderation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            moderator_id INTEGER,
            action TEXT,
            reason TEXT,
            created_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS automod_violations (
            guild_id INTEGER,
            user_id INTEGER,
            violations INTEGER DEFAULT 0,
            last_violation INTEGER DEFAULT 0,
            PRIMARY KEY(guild_id, user_id)
        );
        """)
        con.commit()
        con.close()

mega_init_db()

# إضافة أعمدة جديدة تلقائيًا لقواعد البيانات القديمة بدون حذف بياناتها.
def mega_migrate_schema():
    con = mega_db()
    existing = {row[1] for row in con.execute("PRAGMA table_info(guild_settings)").fetchall()}
    additions = {
        "ticket_open_log_channel_id": "INTEGER",
        "ticket_close_log_channel_id": "INTEGER",
        "ticket_note_log_channel_id": "INTEGER",
        "ticket_action_log_channel_id": "INTEGER",
        "ticket_claim_log_channel_id": "INTEGER",
        "evidence_channel_id": "INTEGER",
    }
    for name, typ in additions.items():
        if name not in existing:
            con.execute(f"ALTER TABLE guild_settings ADD COLUMN {name} {typ}")
    con.commit()
    con.close()

mega_migrate_schema()

def mega_setting(guild_id, key, default=None):
    con = mega_db()
    row = con.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)).fetchone()
    con.close()
    return row[key] if row and key in row.keys() and row[key] is not None else default

def mega_set_settings(guild_id, **values):
    con = mega_db()
    con.execute("INSERT OR IGNORE INTO guild_settings(guild_id) VALUES(?)", (guild_id,))
    for key, value in values.items():
        con.execute(f"UPDATE guild_settings SET {key}=? WHERE guild_id=?", (value, guild_id))
    con.commit()
    con.close()

def mega_embed(title, description="", color=discord.Color.blurple(), image=None, thumbnail=None):
    e = discord.Embed(title=title, description=description, color=color,
                      timestamp=datetime.now(timezone.utc))
    if image:
        e.set_image(url=image)
    if thumbnail:
        e.set_thumbnail(url=thumbnail)
    return e

async def mega_log(guild, kind, title, description, color=discord.Color.blurple(), channel_override=None):
    if channel_override is not None:
        channel = channel_override
    else:
        key = {
            "message": "log_message_channel_id",
            "member": "log_member_channel_id",
            "mod": "log_mod_channel_id",
            "ticket": "log_ticket_channel_id",
            "command": "log_command_channel_id",
        }.get(kind)
        if not key:
            return
        cid = mega_setting(guild.id, key)
        channel = guild.get_channel(cid) if cid else None
    if channel:
        try:
            await channel.send(embed=mega_embed(title, description, color))
        except Exception:
            pass

def ticket_log_channel(guild, event_name):
    key = {
        "open": "ticket_open_log_channel_id",
        "close": "ticket_close_log_channel_id",
        "note": "ticket_note_log_channel_id",
        "action": "ticket_action_log_channel_id",
        "claim": "ticket_claim_log_channel_id",
    }.get(event_name)
    cid = mega_setting(guild.id, key) if key else None
    return guild.get_channel(cid) if cid else None

async def mega_ticket_log(guild, event_name, title, description, color=discord.Color.blurple()):
    channel = ticket_log_channel(guild, event_name)
    if channel:
        await mega_log(guild, "ticket", title, description, color, channel_override=channel)
    else:
        await mega_log(guild, "ticket", title, description, color)

# ------------------------- LOGS -------------------------

@bot.tree.command(name="logs-setup", description="إعداد لوقات مستقلة للرسائل والأعضاء والإدارة والتكتات والأوامر")
@app_commands.checks.has_permissions(administrator=True)
async def mega_logs_setup(
    interaction: discord.Interaction,
    message_logs: discord.TextChannel = None,
    member_logs: discord.TextChannel = None,
    moderation_logs: discord.TextChannel = None,
    ticket_logs: discord.TextChannel = None,
    command_logs: discord.TextChannel = None
):
    mega_set_settings(
        interaction.guild.id,
        log_message_channel_id=message_logs.id if message_logs else None,
        log_member_channel_id=member_logs.id if member_logs else None,
        log_mod_channel_id=moderation_logs.id if moderation_logs else None,
        log_ticket_channel_id=ticket_logs.id if ticket_logs else None,
        log_command_channel_id=command_logs.id if command_logs else None
    )
    e = mega_embed("📚 تم إعداد اللوقات",
                   "تم حفظ إعدادات اللوقات بشكل مستقل لكل سيرفر.")
    for name, ch in [
        ("📝 الرسائل", message_logs), ("👥 الأعضاء", member_logs),
        ("🛡️ الإدارة", moderation_logs), ("🎫 التكتات", ticket_logs),
        ("⚡ الأوامر", command_logs)
    ]:
        e.add_field(name=name, value=ch.mention if ch else "غير مفعل", inline=True)
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.listen("on_message_delete")
async def mega_message_delete(message):
    if message.guild and not message.author.bot:
        content = message.content[:1500] or "رسالة بدون نص / تحتوي مرفقات فقط"
        await mega_log(message.guild, "message", "🗑️ حذف رسالة",
                        f"👤 **العضو:** {message.author.mention}\n📢 **الروم:** {message.channel.mention}\n💬 **المحتوى:** {content}",
                        discord.Color.red())

@bot.listen("on_message_edit")
async def mega_message_edit(before, after):
    if before.guild and not before.author.bot and before.content != after.content:
        e = mega_embed("✏️ تعديل رسالة",
                        f"👤 **العضو:** {before.author.mention}\n📢 **الروم:** {before.channel.mention}\n\n"
                        f"**قبل:** {before.content[:700] or 'فارغ'}\n"
                        f"**بعد:** {after.content[:700] or 'فارغ'}",
                        discord.Color.orange())
        cid = mega_setting(before.guild.id, "log_message_channel_id")
        ch = before.guild.get_channel(cid) if cid else None
        if ch:
            try: await ch.send(embed=e)
            except Exception: pass

@bot.listen("on_member_join")
async def mega_member_join(member):
    await mega_log(member.guild, "member", "📥 دخول عضو",
                    f"👤 {member.mention}\n🆔 `{member.id}`\n👥 العدد: `{member.guild.member_count}`",
                    discord.Color.green())

@bot.listen("on_member_remove")
async def mega_member_leave(member):
    await mega_log(member.guild, "member", "📤 خروج عضو",
                    f"👤 **{member}**\n🆔 `{member.id}`",
                    discord.Color.dark_red())

@bot.listen("on_interaction")
async def mega_command_log(interaction):
    if interaction.guild and interaction.type == discord.InteractionType.application_command:
        try:
            name = interaction.data.get("name", "unknown")
            await mega_log(interaction.guild, "command", "⚡ استخدام أمر",
                            f"👤 {interaction.user.mention}\n🔧 `/{name}`\n📢 {interaction.channel.mention}",
                            discord.Color.blurple())
        except Exception:
            pass

# ------------------------- TICKET EVENT LOGS -------------------------

@bot.tree.command(name="ticket-logs-setup", description="تحديد روم مستقل لكل نوع من لوقات التذاكر")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_logs_setup(
    interaction: discord.Interaction,
    open_log: discord.TextChannel = None,
    close_log: discord.TextChannel = None,
    note_log: discord.TextChannel = None,
    action_log: discord.TextChannel = None,
    claim_log: discord.TextChannel = None
):
    mega_set_settings(
        interaction.guild.id,
        ticket_open_log_channel_id=open_log.id if open_log else None,
        ticket_close_log_channel_id=close_log.id if close_log else None,
        ticket_note_log_channel_id=note_log.id if note_log else None,
        ticket_action_log_channel_id=action_log.id if action_log else None,
        ticket_claim_log_channel_id=claim_log.id if claim_log else None
    )
    e = mega_embed(
        "📚 لوقات التذاكر",
        "تم حفظ كل نوع في روم مستقل.",
        discord.Color.green()
    )
    for label, ch in [
        ("🎫 فتح تذكرة", open_log),
        ("🔒 إغلاق تذكرة", close_log),
        ("📝 ملاحظات التذكرة", note_log),
        ("⚙️ إجراءات الإدارة", action_log),
        ("🙋 استلام التذكرة", claim_log),
    ]:
        e.add_field(name=label, value=ch.mention if ch else "غير محدد", inline=False)
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="evidence-setup", description="تحديد روم دلائل الإدارة")
@app_commands.checks.has_permissions(administrator=True)
async def evidence_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    mega_set_settings(interaction.guild.id, evidence_channel_id=channel.id)
    await interaction.response.send_message(
        embed=mega_embed("📁 تم إعداد دلائل الإدارة", f"كل أدلة الإدارة الجديدة ستظهر في {channel.mention}.", discord.Color.green()),
        ephemeral=True
    )

# ------------------------- TICKETS -------------------------

class MegaTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تذكرة", emoji="🎫", style=discord.ButtonStyle.green, custom_id="mega_ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = interaction.guild.id
        existing = mega_db().execute(
            "SELECT channel_id FROM tickets WHERE guild_id=? AND owner_id=? AND status='open'",
            (gid, interaction.user.id)).fetchone()
        con = mega_db()
        if existing:
            con.close()
            ch = interaction.guild.get_channel(existing["channel_id"])
            await interaction.response.send_message(
                f"⚠️ لديك تذكرة مفتوحة بالفعل: {ch.mention if ch else 'غير موجودة'}", ephemeral=True)
            return

        category_id = mega_setting(gid, "ticket_category_id")
        support_id = mega_setting(gid, "ticket_support_role_id")
        category = interaction.guild.get_channel(category_id) if category_id else None
        support = interaction.guild.get_role(support_id) if support_id else None

        row = con.execute("SELECT counter FROM ticket_counters WHERE guild_id=?", (gid,)).fetchone()
        number = (row["counter"] if row else 0) + 1
        con.execute("INSERT OR REPLACE INTO ticket_counters(guild_id,counter) VALUES(?,?)", (gid, number))

        pattern = mega_setting(gid, "ticket_pattern", "🎫・{count}")
        name = pattern.replace("{count}", str(number)).replace("{user}", interaction.user.name.lower()[:20])

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        if support:
            overwrites[support] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        overwrites[interaction.guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True)

        try:
            channel = await interaction.guild.create_text_channel(name, category=category, overwrites=overwrites)
            con.execute("""INSERT INTO tickets(guild_id,channel_id,owner_id,number,status,created_at)
                           VALUES(?,?,?,?,?,?)""",
                        (gid, channel.id, interaction.user.id, number, "open", int(time.time())))
            con.commit()
            con.close()
            embed = mega_embed("🎫 تذكرتك جاهزة",
                               f"👤 صاحب التذكرة: {interaction.user.mention}\n"
                               f"🔢 رقم التذكرة: `{number}`\n\nاستخدم الأزرار بالأسفل لإدارة التذكرة.",
                               discord.Color.green(), thumbnail=interaction.user.display_avatar.url)
            await channel.send(content=interaction.user.mention, embed=embed, view=MegaTicketControls())
            await interaction.response.send_message(f"✅ تم إنشاء تذكرتك: {channel.mention}", ephemeral=True)
            await mega_ticket_log(interaction.guild, "open", "🎫 فتح تذكرة",
                                   f"👤 {interaction.user.mention}\n📢 {channel.mention}\n🔢 `{number}`", discord.Color.green())
        except Exception as ex:
            con.close()
            await interaction.response.send_message(f"❌ فشل إنشاء التذكرة: `{str(ex)[:300]}`", ephemeral=True)

class MegaTicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _get_ticket(self, interaction):
        con = mega_db()
        row = con.execute("SELECT * FROM tickets WHERE channel_id=?", (interaction.channel.id,)).fetchone()
        con.close()
        return row

    @discord.ui.button(label="إغلاق", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="mega_ticket_close")
    async def close(self, interaction, button):
        row = await self._get_ticket(interaction)
        if not row:
            return await interaction.response.send_message("❌ هذه ليست تذكرة.", ephemeral=True)
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        owner = interaction.guild.get_member(row["owner_id"])
        if owner:
            await interaction.channel.set_permissions(owner, view_channel=True, send_messages=False)
        con=mega_db(); con.execute("UPDATE tickets SET status='closed' WHERE channel_id=?", (interaction.channel.id,)); con.commit(); con.close()
        await interaction.response.send_message(embed=mega_embed("🔒 تم إغلاق التذكرة", "يمكن للإدارة إعادة فتحها أو حذفها.", discord.Color.orange()))
        await mega_ticket_log(interaction.guild, "close", "🔒 إغلاق تذكرة", f"📢 {interaction.channel.mention}\n👤 بواسطة {interaction.user.mention}", discord.Color.orange())

    @discord.ui.button(label="إعادة فتح", emoji="🔓", style=discord.ButtonStyle.green, custom_id="mega_ticket_reopen")
    async def reopen(self, interaction, button):
        row = await self._get_ticket(interaction)
        if not row:
            return await interaction.response.send_message("❌ هذه ليست تذكرة.", ephemeral=True)
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        owner = interaction.guild.get_member(row["owner_id"])
        if owner:
            await interaction.channel.set_permissions(owner, view_channel=True, send_messages=True, read_message_history=True)
        support_id=mega_setting(interaction.guild.id,"ticket_support_role_id")
        support=interaction.guild.get_role(support_id) if support_id else None
        if support:
            await interaction.channel.set_permissions(support, view_channel=True, send_messages=True, read_message_history=True)
        con=mega_db(); con.execute("UPDATE tickets SET status='open' WHERE channel_id=?", (interaction.channel.id,)); con.commit(); con.close()
        await interaction.response.send_message("🔓 تم إعادة فتح التذكرة.")
        await mega_ticket_log(interaction.guild, "action", "🔓 إعادة فتح تذكرة", f"📢 {interaction.channel.mention}\n👤 بواسطة {interaction.user.mention}", discord.Color.green())

    @discord.ui.button(label="حذف", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="mega_ticket_delete")
    async def delete(self, interaction, button):
        row=await self._get_ticket(interaction)
        if not row:
            return await interaction.response.send_message("❌ هذه ليست تذكرة.", ephemeral=True)
        await interaction.response.send_message("🗑️ سيتم حذف التذكرة بعد لحظات.")
        await mega_ticket_log(interaction.guild, "action", "🗑️ حذف تذكرة",
                               f"📢 {interaction.channel.mention}\n👤 بواسطة {interaction.user.mention}", discord.Color.red())
        con=mega_db(); con.execute("DELETE FROM tickets WHERE channel_id=?", (interaction.channel.id,)); con.commit(); con.close()
        await asyncio.sleep(2)
        try: await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")
        except Exception: pass

    @discord.ui.button(label="استلام", emoji="🙋", style=discord.ButtonStyle.success, custom_id="mega_ticket_claim")
    async def claim(self, interaction, button):
        row=current_ticket(interaction)
        if not row:
            return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.", ephemeral=True)
        con=mega_db(); con.execute("UPDATE tickets SET claimed_by=? WHERE channel_id=?",(interaction.user.id,interaction.channel.id)); con.commit(); con.close()
        await interaction.response.send_message(embed=mega_embed("🙋 تم استلام التذكرة",f"👮 المستلم: {interaction.user.mention}",discord.Color.green()))
        await mega_ticket_log(interaction.guild,"claim","🙋 استلام التذكرة",f"🎫 {interaction.channel.mention}\n👮 {interaction.user.mention}",discord.Color.green())

    @discord.ui.button(label="إضافة عضو", emoji="➕", style=discord.ButtonStyle.primary, custom_id="mega_ticket_add")
    async def add_member(self, interaction, button):
        await interaction.response.send_message("استخدم `/ticket-add` لإضافة عضو للتذكرة.", ephemeral=True)

    @discord.ui.button(label="إزالة عضو", emoji="➖", style=discord.ButtonStyle.secondary, custom_id="mega_ticket_remove")
    async def remove_member(self, interaction, button):
        await interaction.response.send_message("استخدم `/ticket-remove` لإزالة عضو من التذكرة.", ephemeral=True)

@bot.tree.command(name="ticket-setup", description="إعداد نظام التكتات والكاتيجوري والرتبة واللوق وصيغة الاسم")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, category: discord.CategoryChannel, support_role: discord.Role,
                       log_channel: discord.TextChannel = None, pattern: str = "🎫・{count}"):
    mega_set_settings(interaction.guild.id,
                      ticket_category_id=category.id,
                      ticket_support_role_id=support_role.id,
                      ticket_log_channel_id=log_channel.id if log_channel else None,
                      log_ticket_channel_id=log_channel.id if log_channel else None,
                      ticket_pattern=pattern[:90])
    await interaction.response.send_message(embed=mega_embed(
        "🎫 تم إعداد نظام التكتات",
        f"📁 الكاتيجوري: {category.mention}\n🎭 الدعم: {support_role.mention}\n"
        f"📚 اللوق العام: {log_channel.mention if log_channel else 'غير محدد'}\n🏷️ الصيغة: `{pattern}`\n\n"
        "المتغيرات: `{count}` للعداد و `{user}` لاسم العضو.",
        discord.Color.green()), ephemeral=True)

@bot.tree.command(name="ticket-panel", description="إرسال بانل فتح التذاكر مع Embed وصورة")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction, channel: discord.TextChannel,
                       title: str = "🎫 الدعم الفني", description: str = "اضغط الزر بالأسفل لفتح تذكرة.", image: str = None):
    e=mega_embed(title, description, discord.Color.blurple(), image=image)
    await channel.send(embed=e, view=MegaTicketView())
    await interaction.response.send_message(f"✅ تم إرسال بانل التكت في {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket-add", description="إضافة عضو إلى التذكرة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_add(interaction: discord.Interaction, member: discord.Member):
    row=mega_db().execute("SELECT * FROM tickets WHERE channel_id=?", (interaction.channel.id,)).fetchone()
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.", ephemeral=True)
    await interaction.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
    await interaction.response.send_message(embed=mega_embed("➕ تمت إضافة عضو", f"👤 {member.mention} أصبح لديه وصول للتذكرة.", discord.Color.green()))
    await mega_ticket_log(interaction.guild,"action","➕ إضافة عضو",f"📢 {interaction.channel.mention}\n👤 {member.mention}\n🛡️ {interaction.user.mention}")

@bot.tree.command(name="ticket-remove", description="إزالة عضو من التذكرة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_remove(interaction: discord.Interaction, member: discord.Member):
    row=mega_db().execute("SELECT * FROM tickets WHERE channel_id=?", (interaction.channel.id,)).fetchone()
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.", ephemeral=True)
    if member.id == row["owner_id"]:
        return await interaction.response.send_message("❌ لا يمكن إزالة صاحب التذكرة.", ephemeral=True)
    await interaction.channel.set_permissions(member, overwrite=None)
    await interaction.response.send_message(embed=mega_embed("➖ تمت إزالة عضو", f"👤 {member.mention} لم يعد لديه وصول.", discord.Color.orange()))
    await mega_ticket_log(interaction.guild,"action","➖ إزالة عضو",f"📢 {interaction.channel.mention}\n👤 {member.mention}\n🛡️ {interaction.user.mention}")

@bot.tree.command(name="ticket-close", description="إغلاق التذكرة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_close(interaction: discord.Interaction):
    row=mega_db().execute("SELECT * FROM tickets WHERE channel_id=?", (interaction.channel.id,)).fetchone()
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.", ephemeral=True)
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
    owner=interaction.guild.get_member(row["owner_id"])
    if owner: await interaction.channel.set_permissions(owner, view_channel=True, send_messages=False)
    con=mega_db(); con.execute("UPDATE tickets SET status='closed' WHERE channel_id=?", (interaction.channel.id,)); con.commit(); con.close()
    await interaction.response.send_message("🔒 تم إغلاق التذكرة.")
    await mega_ticket_log(interaction.guild,"close","🔒 إغلاق تذكرة",f"📢 {interaction.channel.mention}\n👤 بواسطة {interaction.user.mention}",discord.Color.orange())

@bot.tree.command(name="ticket-reopen", description="إعادة فتح التذكرة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_reopen(interaction: discord.Interaction):
    row=mega_db().execute("SELECT * FROM tickets WHERE channel_id=?", (interaction.channel.id,)).fetchone()
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.", ephemeral=True)
    owner=interaction.guild.get_member(row["owner_id"])
    if owner: await interaction.channel.set_permissions(owner, view_channel=True, send_messages=True)
    support_id=mega_setting(interaction.guild.id,"ticket_support_role_id")
    support=interaction.guild.get_role(support_id) if support_id else None
    if support: await interaction.channel.set_permissions(support, view_channel=True, send_messages=True)
    con=mega_db(); con.execute("UPDATE tickets SET status='open' WHERE channel_id=?", (interaction.channel.id,)); con.commit(); con.close()
    await interaction.response.send_message("🔓 تم إعادة فتح التذكرة.")
    await mega_ticket_log(interaction.guild,"action","🔓 إعادة فتح تذكرة",f"📢 {interaction.channel.mention}\n👤 بواسطة {interaction.user.mention}",discord.Color.green())

# ------------------------- AUTO REPLIES + AUTOMOD -------------------------

@bot.tree.command(name="autoreply-add", description="إضافة رد تلقائي")
@app_commands.checks.has_permissions(administrator=True)
async def autoreply_add(interaction: discord.Interaction, trigger: str, response: str):
    con=mega_db(); con.execute("INSERT OR REPLACE INTO autoreplies VALUES(?,?,?)",(interaction.guild.id,trigger.lower(),response)); con.commit(); con.close()
    await interaction.response.send_message(embed=mega_embed("🤖 تمت إضافة الرد التلقائي", f"🔑 `{trigger}`\n💬 {response}", discord.Color.green()), ephemeral=True)

@bot.tree.command(name="autoreply-remove", description="حذف رد تلقائي")
@app_commands.checks.has_permissions(administrator=True)
async def autoreply_remove(interaction: discord.Interaction, trigger: str):
    con=mega_db(); con.execute("DELETE FROM autoreplies WHERE guild_id=? AND trigger=?",(interaction.guild.id,trigger.lower())); con.commit(); con.close()
    await interaction.response.send_message("🗑️ تم حذف رد تلقائي.", ephemeral=True)

@bot.tree.command(name="automod", description="إعداد حماية السبام والروابط والتكرار مع ميوت متدرج")
@app_commands.checks.has_permissions(administrator=True)
async def automod(interaction: discord.Interaction, enabled: bool=True, limit: int=5, window: int=8):
    limit=max(2,min(limit,20)); window=max(3,min(window,30))
    mega_set_settings(interaction.guild.id, automod_enabled=int(enabled), spam_limit=limit, spam_window=window)
    await interaction.response.send_message(embed=mega_embed(
        "🛡️ إعداد AutoMod",
        f"الحالة: {'🟢 مفعّل' if enabled else '🔴 متوقف'}\n"
        f"📨 السبام: `{limit}` رسائل خلال `{window}` ثوانٍ\n"
        "🔗 يمنع الروابط أيضًا\n"
        "⏱️ أول مخالفة: 5 دقائق، وكل مخالفة لاحقة تزيد مدة الميوت.",
        discord.Color.green() if enabled else discord.Color.red()), ephemeral=True)

_mega_spam_cache = {}
_mega_repeat_cache = {}
_MEGA_URL_RE = re.compile(r"(?:https?://|www\.|discord\.gg/|discord\.com/invite/|t\.me/|bit\.ly/|tinyurl\.com/)", re.I)

def mega_timeout_minutes(violations: int) -> int:
    # 5, 10, 20, 40... capped at Discord's 28-day timeout limit.
    return min(5 * (2 ** max(0, violations - 1)), 40320)

def mega_record_violation(guild_id: int, user_id: int) -> int:
    con=mega_db()
    now=int(time.time())
    con.execute("INSERT OR IGNORE INTO automod_violations(guild_id,user_id,violations,last_violation) VALUES(?,?,0,0)",(guild_id,user_id))
    con.execute("UPDATE automod_violations SET violations=violations+1,last_violation=? WHERE guild_id=? AND user_id=?",(now,guild_id,user_id))
    row=con.execute("SELECT violations FROM automod_violations WHERE guild_id=? AND user_id=?",(guild_id,user_id)).fetchone()
    con.commit(); con.close()
    return int(row["violations"]) if row else 1

async def mega_apply_automod(message, reason: str):
    if not message.guild or message.author.bot or has_mod_permission(message.author):
        return False
    violations=mega_record_violation(message.guild.id,message.author.id)
    minutes=mega_timeout_minutes(violations)
    try: await message.delete()
    except Exception: pass
    try:
        await message.author.timeout(timedelta(minutes=minutes), reason=f"AutoMod: {reason}")
    except Exception:
        return True
    await message.channel.send(embed=mega_embed(
        "🛡️ AutoMod",
        f"👤 {message.author.mention}\n"
        f"⚠️ السبب: **{reason}**\n"
        f"🔢 المخالفة رقم: `{violations}`\n"
        f"⏱️ الميوت: `{minutes} دقيقة`",
        discord.Color.red(), thumbnail=message.author.display_avatar.url), delete_after=10)
    await mega_log(message.guild,"mod","🛡️ AutoMod",
                    f"👤 {message.author.mention}\n⚠️ {reason}\n🔢 المخالفة: `{violations}`\n⏱️ الميوت: `{minutes} دقيقة`",discord.Color.red())
    return True

@bot.listen("on_message")
async def mega_message_listener(message):
    if not message.guild or message.author.bot:
        return
    gid=message.guild.id; uid=message.author.id

    # الردود التلقائية
    con=mega_db(); rows=con.execute("SELECT trigger,response FROM autoreplies WHERE guild_id=?",(gid,)).fetchall(); con.close()
    content=message.content.lower().strip()
    for row in rows:
        if row["trigger"] and row["trigger"] in content:
            try: await message.channel.send(row["response"])
            except Exception: pass
            break

    enabled=mega_setting(gid,"automod_enabled",0)
    if not enabled or has_mod_permission(message.author):
        return

    # روابط ودعوات: تعامل معها كمخالفة مباشرة.
    if _MEGA_URL_RE.search(message.content or ""):
        await mega_apply_automod(message,"إرسال رابط أو دعوة")
        return

    now=time.time(); key=(gid,uid)
    bucket=_mega_spam_cache.setdefault(key,[])
    window=int(mega_setting(gid,"spam_window",8))
    bucket[:]=[t for t in bucket if now-t <= window]
    bucket.append(now)
    if len(bucket)>=int(mega_setting(gid,"spam_limit",5)):
        _mega_spam_cache[key]=[]
        await mega_apply_automod(message,"سبام سريع")
        return

    rep=_mega_repeat_cache.get(key)
    if rep and rep["content"]==message.content and now-rep["time"]<10:
        rep["count"]+=1
    else:
        _mega_repeat_cache[key]={"content":message.content,"time":now,"count":1}
    rep=_mega_repeat_cache[key]
    if rep["count"]>=3:
        rep["count"]=0
        await mega_apply_automod(message,"تكرار نفس الرسالة")

# ------------------------- ECONOMY -------------------------

def economy_row(gid, uid):
    con=mega_db()
    con.execute("INSERT OR IGNORE INTO economy(guild_id,user_id,balance,last_daily) VALUES(?,?,0,0)",(gid,uid))
    con.commit()
    row=con.execute("SELECT * FROM economy WHERE guild_id=? AND user_id=?",(gid,uid)).fetchone()
    con.close()
    return row

@bot.tree.command(name="balance", description="عرض رصيدك أو رصيد عضو")
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    member=member or interaction.user
    row=economy_row(interaction.guild.id,member.id)
    e=mega_embed("💰 الرصيد",f"👤 {member.mention}\n💵 **{row['balance']:,}** عملة",discord.Color.gold(),thumbnail=member.display_avatar.url)
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="daily", description="استلام المكافأة اليومية")
async def daily(interaction: discord.Interaction):
    gid,uid=interaction.guild.id,interaction.user.id
    row=economy_row(gid,uid); now=int(time.time())
    if now-row["last_daily"]<86400:
        remain=86400-(now-row["last_daily"])
        return await interaction.response.send_message(f"⏳ عد بعد `{remain//3600}س {(remain%3600)//60}د`.",ephemeral=True)
    amount=random.randint(100,300)
    con=mega_db(); con.execute("UPDATE economy SET balance=balance+?,last_daily=? WHERE guild_id=? AND user_id=?",(amount,now,gid,uid)); con.commit(); con.close()
    await interaction.response.send_message(embed=mega_embed("🎁 المكافأة اليومية",f"ربحت **{amount:,}** عملة 💰",discord.Color.gold()))

@bot.tree.command(name="pay", description="تحويل عملات إلى عضو")
async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):
    if member.bot or member.id==interaction.user.id or amount<=0:
        return await interaction.response.send_message("❌ اختر عضوًا صالحًا ومبلغًا أكبر من صفر.",ephemeral=True)
    sender=economy_row(interaction.guild.id,interaction.user.id)
    if sender["balance"]<amount:
        return await interaction.response.send_message("❌ رصيدك غير كافٍ.",ephemeral=True)
    economy_row(interaction.guild.id,member.id)
    con=mega_db()
    con.execute("UPDATE economy SET balance=balance-? WHERE guild_id=? AND user_id=?",(amount,interaction.guild.id,interaction.user.id))
    con.execute("UPDATE economy SET balance=balance+? WHERE guild_id=? AND user_id=?",(amount,interaction.guild.id,member.id))
    con.commit(); con.close()
    await interaction.response.send_message(embed=mega_embed("💸 تم التحويل",f"{interaction.user.mention} ➜ {member.mention}\n💰 المبلغ: **{amount:,}**",discord.Color.green()))

@bot.tree.command(name="shop", description="عرض متجر الاقتصاد")
async def shop(interaction: discord.Interaction):
    con=mega_db(); rows=con.execute("SELECT item,price FROM shop WHERE guild_id=? ORDER BY price",(interaction.guild.id,)).fetchall(); con.close()
    if not rows:
        e=mega_embed("🛒 المتجر","المتجر فارغ حاليًا.\nاستخدم `/shop-add` لإضافة منتج.",discord.Color.blurple())
    else:
        e=mega_embed("🛒 المتجر")
        for r in rows[:25]: e.add_field(name=f"📦 {r['item']}",value=f"💰 {r['price']:,}",inline=True)
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="shop-add", description="إضافة منتج للمتجر")
@app_commands.checks.has_permissions(administrator=True)
async def shop_add(interaction: discord.Interaction,item:str,price:int):
    if price<0: return await interaction.response.send_message("❌ السعر غير صالح.",ephemeral=True)
    con=mega_db(); con.execute("INSERT OR REPLACE INTO shop VALUES(?,?,?)",(interaction.guild.id,item,price)); con.commit(); con.close()
    await interaction.response.send_message(f"✅ تمت إضافة `{item}` بسعر `{price:,}`.",ephemeral=True)

@bot.tree.command(name="buy", description="شراء منتج من المتجر")
async def buy(interaction: discord.Interaction,item:str):
    con=mega_db(); product=con.execute("SELECT * FROM shop WHERE guild_id=? AND item=?",(interaction.guild.id,item)).fetchone()
    if not product:
        con.close(); return await interaction.response.send_message("❌ المنتج غير موجود.",ephemeral=True)
    economy_row(interaction.guild.id,interaction.user.id)
    bal=con.execute("SELECT balance FROM economy WHERE guild_id=? AND user_id=?",(interaction.guild.id,interaction.user.id)).fetchone()
    if bal["balance"]<product["price"]:
        con.close(); return await interaction.response.send_message("❌ رصيدك غير كافٍ.",ephemeral=True)
    con.execute("UPDATE economy SET balance=balance-? WHERE guild_id=? AND user_id=?",(product["price"],interaction.guild.id,interaction.user.id))
    con.execute("""INSERT INTO inventory(guild_id,user_id,item,amount) VALUES(?,?,?,1)
                   ON CONFLICT(guild_id,user_id,item) DO UPDATE SET amount=amount+1""",
                (interaction.guild.id,interaction.user.id,item))
    con.commit(); con.close()
    await interaction.response.send_message(embed=mega_embed("🛍️ تم الشراء",f"📦 **{item}**\n💰 السعر: `{product['price']:,}`",discord.Color.green()))

# ------------------------- ADMIN EVIDENCE -------------------------

def evidence_channel(guild):
    cid=mega_setting(guild.id,"evidence_channel_id")
    return guild.get_channel(cid) if cid else None

async def send_admin_evidence(interaction, action_name, member, reason, image=None, duration=None):
    channel=evidence_channel(interaction.guild)
    if not channel:
        await interaction.response.send_message("❌ لم يتم إعداد روم دلائل الإدارة. استخدم `/evidence-setup` أولًا.", ephemeral=True)
        return
    extra = f"\n⏱️ **مدة التايم:** {duration}" if duration else ""
    e=mega_embed(
        f"📁 دليل إداري — {action_name}",
        f"👤 **العضو:** {member.mention} (`{member.id}`)\n"
        f"👮 **الإداري:** {interaction.user.mention} (`{interaction.user.id}`)\n"
        f"📝 **السبب:** {reason}{extra}",
        discord.Color.red()
    )
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=f"ONIX • {action_name}")
    if image:
        if image.content_type and not image.content_type.startswith("image/"):
            await interaction.response.send_message("❌ الملف المرفق لازم يكون صورة.", ephemeral=True)
            return
        e.set_image(url=image.url)
    await channel.send(embed=e)
    await interaction.response.send_message(embed=mega_embed("✅ تم حفظ الدليل",f"تم إرسال دليل **{action_name}** إلى {channel.mention}.",discord.Color.green()), ephemeral=True)

@bot.tree.command(name="evidence-time", description="حفظ دليل تايم على عضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def evidence_time(interaction: discord.Interaction, member: discord.Member, reason: str, duration: str="غير محدد", image: discord.Attachment=None):
    await send_admin_evidence(interaction,"TIME / تايم",member,reason,image,duration)

@bot.tree.command(name="evidence-warn", description="حفظ دليل تحذير على عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def evidence_warn(interaction: discord.Interaction, member: discord.Member, reason: str, image: discord.Attachment=None):
    await send_admin_evidence(interaction,"WARN / تحذير",member,reason,image)

@bot.tree.command(name="evidence-ban", description="حفظ دليل باند على عضو")
@app_commands.checks.has_permissions(ban_members=True)
async def evidence_ban(interaction: discord.Interaction, member: discord.Member, reason: str, image: discord.Attachment=None):
    await send_admin_evidence(interaction,"BAN / باند",member,reason,image)

@bot.tree.command(name="evidence-kick", description="حفظ دليل كيك على عضو")
@app_commands.checks.has_permissions(kick_members=True)
async def evidence_kick(interaction: discord.Interaction, member: discord.Member, reason: str, image: discord.Attachment=None):
    await send_admin_evidence(interaction,"KICK / كيك",member,reason,image)

# ------------------------- TICKET ACTIONS / NOTES / CLAIM -------------------------

def current_ticket(interaction):
    con=mega_db(); row=con.execute("SELECT * FROM tickets WHERE channel_id=?",(interaction.channel.id,)).fetchone(); con.close()
    return row

@bot.tree.command(name="ticket-claim", description="استلام التذكرة وتسجيل الإداري المستلم")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_claim(interaction: discord.Interaction):
    row=current_ticket(interaction)
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.",ephemeral=True)
    con=mega_db(); con.execute("UPDATE tickets SET claimed_by=? WHERE channel_id=?",(interaction.user.id,interaction.channel.id)); con.commit(); con.close()
    await interaction.response.send_message(embed=mega_embed("🙋 تم استلام التذكرة",f"🎫 {interaction.channel.mention}\n👮 المستلم: {interaction.user.mention}",discord.Color.green(),thumbnail=interaction.user.display_avatar.url))
    await mega_ticket_log(interaction.guild,"claim","🙋 استلام التذكرة",f"🎫 {interaction.channel.mention}\n👮 المستلم: {interaction.user.mention}",discord.Color.green())

@bot.tree.command(name="ticket-note", description="إضافة ملاحظة إدارية إلى التذكرة")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_note(interaction: discord.Interaction, note: str):
    row=current_ticket(interaction)
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.",ephemeral=True)
    await interaction.response.send_message(embed=mega_embed("📝 ملاحظة التذكرة",f"🎫 {interaction.channel.mention}\n👮 {interaction.user.mention}\n\n**الملاحظة:**\n{note}",discord.Color.blurple()))
    await mega_ticket_log(interaction.guild,"note","📝 ملاحظات التذكرة",f"🎫 {interaction.channel.mention}\n👮 {interaction.user.mention}\n📝 {note}",discord.Color.blurple())

@bot.tree.command(name="ticket-action", description="تسجيل إجراء إداري على التذكرة")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_action(interaction: discord.Interaction, action: str, details: str=None):
    row=current_ticket(interaction)
    if not row: return await interaction.response.send_message("❌ هذا الروم ليس تذكرة.",ephemeral=True)
    details=details or "بدون تفاصيل إضافية"
    await interaction.response.send_message(embed=mega_embed("⚙️ إجراء إداري",f"🎫 {interaction.channel.mention}\n👮 {interaction.user.mention}\n⚙️ **الإجراء:** {action}\n📝 **التفاصيل:** {details}",discord.Color.orange()))
    await mega_ticket_log(interaction.guild,"action","⚙️ إجراءات الإدارة",f"🎫 {interaction.channel.mention}\n👮 {interaction.user.mention}\n⚙️ {action}\n📝 {details}",discord.Color.orange())

# ------------------------- GIVEAWAYS -------------------------

async def mega_finish_giveaway(message_id):
    con=mega_db(); row=con.execute("SELECT * FROM giveaways WHERE message_id=?",(message_id,)).fetchone(); con.close()
    if not row or row["ended"]: return
    channel=bot.get_channel(row["channel_id"])
    if not channel: return
    try: msg=await channel.fetch_message(message_id)
    except Exception: return
    reaction=discord.utils.get(msg.reactions,emoji="🎉")
    users=[]
    if reaction:
        try: users=[u async for u in reaction.users() if not u.bot]
        except Exception: users=[]
    winners=random.sample(users,min(row["winners"],len(users))) if users else []
    text=", ".join(u.mention for u in winners) if winners else "لا يوجد فائزون."
    e=mega_embed("🎉 انتهى القيف أواي",f"🎁 الجائزة: **{row['prize']}**\n🏆 الفائزون: {text}",discord.Color.gold())
    try: await msg.edit(embed=e)
    except Exception: pass
    con=mega_db(); con.execute("UPDATE giveaways SET ended=1 WHERE message_id=?",(message_id,)); con.commit(); con.close()
    await mega_log(channel.guild,"command","🎉 انتهاء Giveaway",f"🎁 {row['prize']}\n🏆 {text}",discord.Color.gold())

@bot.tree.command(name="giveaway", description="إنشاء قيف أواي بسهولة بالمدة والجائزة والفائزين")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway(interaction: discord.Interaction, prize: str, minutes: int, winners: int=1, image: str=None):
    if minutes<=0 or winners<=0 or winners>20:
        return await interaction.response.send_message("❌ المدة والفائزون يجب أن يكونوا أكبر من صفر.",ephemeral=True)
    end=int(time.time())+minutes*60
    e=mega_embed("🎉 GIVEAWAY",f"🎁 **الجائزة:** {prize}\n⏳ **ينتهي:** <t:{end}:R>\n🏆 **عدد الفائزين:** `{winners}`\n\nاضغط 🎉 للدخول!",discord.Color.gold(),image=image)
    e.set_footer(text=f"بدأ بواسطة {interaction.user}")
    await interaction.response.send_message("🎉 تم إنشاء القيف أواي!",ephemeral=True)
    msg=await interaction.channel.send(embed=e)
    await msg.add_reaction("🎉")
    con=mega_db(); con.execute("INSERT OR REPLACE INTO giveaways VALUES(?,?,?,?,?,?,?,0)",
                               (msg.id,interaction.guild.id,interaction.channel.id,prize,winners,end,interaction.user.id)); con.commit(); con.close()
    await asyncio.sleep(minutes*60)
    await mega_finish_giveaway(msg.id)

@bot.tree.command(name="giveaway-reroll", description="إعادة سحب قيف أواي منتهي")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_reroll(interaction: discord.Interaction, message_id: str):
    try: mid=int(message_id)
    except: return await interaction.response.send_message("❌ Message ID غير صحيح.",ephemeral=True)
    con=mega_db(); row=con.execute("SELECT * FROM giveaways WHERE message_id=?",(mid,)).fetchone(); con.close()
    if not row: return await interaction.response.send_message("❌ القيف أواي غير موجود.",ephemeral=True)
    ch=interaction.guild.get_channel(row["channel_id"])
    if not ch: return await interaction.response.send_message("❌ الروم غير موجود.",ephemeral=True)
    try: msg=await ch.fetch_message(mid)
    except: return await interaction.response.send_message("❌ الرسالة غير موجودة.",ephemeral=True)
    reaction=discord.utils.get(msg.reactions,emoji="🎉"); users=[]
    if reaction:
        try: users=[u async for u in reaction.users() if not u.bot]
        except: pass
    winners=random.sample(users,min(row["winners"],len(users))) if users else []
    text=", ".join(u.mention for u in winners) if winners else "لا يوجد فائز جديد."
    await interaction.response.send_message(embed=mega_embed("🔄 إعادة السحب",f"🎁 {row['prize']}\n🏆 {text}",discord.Color.gold()))

# ------------------------- BAN / KICK AUDIT LOG HELPERS -------------------------

@bot.listen("on_member_ban")
async def mega_member_ban(guild, user):
    await mega_log(guild,"mod","🔨 حظر عضو",f"👤 {user.mention if hasattr(user,'mention') else user}\n🆔 `{user.id}`",discord.Color.red())

@bot.listen("on_member_unban")
async def mega_member_unban(guild, user):
    await mega_log(guild,"mod","🔓 فك حظر عضو",f"👤 {user}\n🆔 `{user.id}`",discord.Color.green())

# إعادة إضافة الـ Views بعد إعادة تشغيل البوت
@bot.listen("on_ready")
async def mega_restore_views():
    try:
        bot.add_view(MegaTicketView())
        bot.add_view(MegaTicketControls())
    except Exception:
        pass

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token not found!")
