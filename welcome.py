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

    if days:
        parts.append(f"{days} يوم")
    if hours:
        parts.append(f"{hours} ساعة")
    if minutes:
        parts.append(f"{minutes} دقيقة")
    if seconds and not parts:
        parts.append(f"{seconds} ثانية")

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

    own_afk = get_user_afk(
        guild_id,
        author_id
    )

    if own_afk:
        removed = remove_user_afk(
            guild_id,
            author_id
        )

        if removed:
            started = removed.get("started_at", time.time())
            duration = max(
                0,
                time.time() - float(started)
            )

            embed = discord.Embed(
                title="👋 أهلًا بعودتك!",
                description=(
                    f"{message.author.mention} رجعت من وضع **AFK**.\n\n"
                    f"⏱️ **مدة الغياب:** `{format_afk_duration(duration)}`"
                ),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            embed.set_thumbnail(
                url=message.author.display_avatar.url
            )

            embed.set_footer(
                text="تم إلغاء حالة AFK تلقائيًا"
            )

            try:
                await message.channel.send(
                    embed=embed,
                    delete_after=8
                )
            except:
                pass

    notified = set()

    for member in message.mentions:
        if member.bot:
            continue

        if member.id in notified:
            continue

        notified.add(member.id)

        data = get_user_afk(
            guild_id,
            member.id
        )

        if not data:
            continue

        reason = data.get(
            "reason",
            "لم يتم تحديد سبب"
        )

        started = data.get(
            "started_at",
            time.time()
        )

        duration = max(
            0,
            time.time() - float(started)
        )

        embed = discord.Embed(
            title="💤 هذا العضو في وضع AFK",
            description=(
                f"👤 **العضو:** {member.mention}\n"
                f"💬 **السبب:** {reason}\n"
                f"⏱️ **منذ:** `{format_afk_duration(duration)}`"
            ),
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        embed.set_footer(
            text="قد يكون العضو غير متواجد حاليًا"
        )

        try:
            await message.channel.send(
                embed=embed,
                delete_after=10
            )
        except:
            pass


# ==================================
# /afk
# ==================================

@bot.tree.command(
    name="afk",
    description="تفعيل وضع AFK"
)
@app_commands.describe(
    reason="سبب الغياب - اختياري"
)
async def afk(
    interaction: discord.Interaction,
    reason: str = "غير متوفر"
):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    guild_data = get_guild_afk(
        guild_id
    )

    if user_id in guild_data:
        old_data = guild_data[user_id]
        old_reason = old_data.get(
            "reason",
            "غير متوفر"
        )

        embed = discord.Embed(
            title="💤 أنت بالفعل AFK",
            description=(
                f"أنت حاليًا في وضع **AFK**.\n\n"
                f"💬 **السبب الحالي:** {old_reason}\n\n"
                f"يمكنك فقط إرسال رسالة في الشات للعودة تلقائيًا."
            ),
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
        return

    now = time.time()

    guild_data[user_id] = {
        "reason": reason,
        "started_at": now,
        "started_at_text": datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
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
        timestamp=datetime.utcnow()
    )

    embed.set_thumbnail(
        url=interaction.user.display_avatar.url
    )

    embed.set_footer(
        text=f"AFK • {interaction.guild.name}"
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# /afk-status
# ==================================

@bot.tree.command(
    name="afk-status",
    description="عرض حالة AFK لعضو"
)
@app_commands.describe(
    member="العضو المراد فحص حالته"
)
async def afk_status(
    interaction: discord.Interaction,
    member: discord.Member = None
):
    member = member or interaction.user

    data = get_user_afk(
        interaction.guild.id,
        member.id
    )

    if not data:
        embed = discord.Embed(
            title="🟢 العضو غير AFK",
            description=(
                f"{member.mention} ليس في وضع **AFK** حاليًا."
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(
            url=member.display_avatar.url
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
        return

    started = float(
        data.get(
            "started_at",
            time.time()
        )
    )

    duration = max(
        0,
        time.time() - started
    )

    reason = data.get(
        "reason",
        "غير متوفر"
    )

    embed = discord.Embed(
        title="💤 حالة AFK",
        description=f"{member.mention} حاليًا في وضع **AFK**.",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="💬 السبب",
        value=reason,
        inline=False
    )

    embed.add_field(
        name="⏱️ مدة الغياب",
        value=format_afk_duration(duration),
        inline=True
    )

    embed.add_field(
        name="🕐 بدأ AFK",
        value=f"<t:{int(started)}:R>",
        inline=True
    )

    embed.add_field(
        name="📅 الوقت",
        value=f"<t:{int(started)}:F>",
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text="نظام AFK"
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# /afk-list
# ==================================

@bot.tree.command(
    name="afk-list",
    description="عرض جميع الأعضاء الموجودين في وضع AFK"
)
async def afk_list(
    interaction: discord.Interaction
):
    guild_data = get_guild_afk(
        interaction.guild.id
    )

    if not guild_data:
        embed = discord.Embed(
            title="💤 قائمة AFK",
            description="لا يوجد أي عضو في وضع AFK حاليًا.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(
            embed=embed
        )
        return

    lines = []

    for user_id, data in list(guild_data.items()):
        member = interaction.guild.get_member(
            int(user_id)
        )

        if not member:
            continue

        started = float(
            data.get(
                "started_at",
                time.time()
            )
        )

        duration = max(
            0,
            time.time() - started
        )

        reason = data.get(
            "reason",
            "غير متوفر"
        )

        lines.append(
            f"👤 {member.mention}\n"
            f"💬 `{reason}` • ⏱️ `{format_afk_duration(duration)}`"
        )

    if not lines:
        embed = discord.Embed(
            title="💤 قائمة AFK",
            description="لا يوجد أي عضو في وضع AFK حاليًا.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(
            embed=embed
        )
        return

    text = "\n\n".join(lines[:20])

    if len(lines) > 20:
        text += f"\n\n📌 وهناك `{len(lines) - 20}` عضو آخر."

    embed = discord.Embed(
        title="💤 أعضاء AFK",
        description=text,
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )

    embed.set_footer(
        text=f"إجمالي AFK: {len(lines)}"
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================
# /afk-remove
# ==================================

@bot.tree.command(
    name="afk-remove",
    description="إزالة AFK عن عضو يدويًا"
)
@app_commands.describe(
    member="العضو المراد إزالة AFK عنه"
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
async def afk_remove(
    interaction: discord.Interaction,
    member: discord.Member
):
    data = get_user_afk(
        interaction.guild.id,
        member.id
    )

    if not data:
        embed = discord.Embed(
            title="⚠️ العضو ليس AFK",
            description=(
                f"{member.mention} ليس في وضع AFK حاليًا."
            ),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
        return

    started = float(
        data.get(
            "started_at",
            time.time()
        )
    )

    duration = max(
        0,
        time.time() - started
    )

    remove_user_afk(
        interaction.guild.id,
        member.id
    )

    embed = discord.Embed(
        title="✅ تم إزالة AFK",
        description=(
            f"👤 **العضو:** {member.mention}\n"
            f"⏱️ **مدة AFK:** `{format_afk_duration(duration)}`\n"
            f"👮 **بواسطة:** {interaction.user.mention}"
        ),
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )

    await interaction.response.send_message(
        embed=embed
    )


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

# ==================================
# General Panel Builder System
# /panel
# ==================================

GENERAL_PANELS_FILE = "general_panels.json"

general_panels = load_json(GENERAL_PANELS_FILE, [])

def save_general_panels():
    save_json(GENERAL_PANELS_FILE, general_panels)


# ==================================
# ألوان البانلات
# ==================================

PANEL_COLORS = {
    "أزرق": discord.Color.blue(),
    "أخضر": discord.Color.green(),
    "أحمر": discord.Color.red(),
    "بنفسجي": discord.Color.purple(),
    "ذهبي": discord.Color.gold(),
    "برتقالي": discord.Color.orange(),
    "وردي": discord.Color.magenta(),
    "رمادي": discord.Color.light_grey(),
    "أسود": discord.Color.from_rgb(0, 0, 0),
}


def panel_color(name):
    return PANEL_COLORS.get(
        name,
        discord.Color.blurple()
    )


# ==================================
# إنشاء Embed
# ==================================

def build_panel_embed(data):
    embed = discord.Embed(
        title=data.get("title") or None,
        description=data.get("description") or None,
        color=panel_color(
            data.get("color", "أزرق")
        )
    )

    image = data.get("image")

    if image:
        try:
            embed.set_image(url=image)
        except:
            pass

    return embed


# ==================================
# مدير إنشاء البانل
# ==================================

class PanelBuilder:

    def __init__(self, user_id):
        self.user_id = user_id

        self.data = {
            "title": "",
            "description": "",
            "image": "",
            "color": "أزرق",
            "buttons": []
        }

        self.current_button = 0
        self.current_inner_button = 0


# ==================================
# التحقق من صاحب العملية
# ==================================

def panel_owner(interaction, builder):

    return interaction.user.id == builder.user_id


# ==================================
# Modal معلومات البانل
# ==================================

class MainPanelModal(discord.ui.Modal):

    def __init__(self, builder):
        super().__init__(
            title="معلومات البانل"
        )

        self.builder = builder

        self.title_input = discord.ui.TextInput(
            label="عنوان",
            placeholder="عنوان البانل",
            required=False,
            max_length=256
        )

        self.description_input = discord.ui.TextInput(
            label="وصف",
            placeholder="وصف البانل",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.image_input = discord.ui.TextInput(
            label="رابط الصورة",
            placeholder="https://example.com/image.png",
            required=False,
            max_length=1000
        )

        self.add_item(
            self.title_input
        )

        self.add_item(
            self.description_input
        )

        self.add_item(
            self.image_input
        )

    async def on_submit(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        self.builder.data["title"] = str(
            self.title_input.value
        )

        self.builder.data["description"] = str(
            self.description_input.value
        )

        self.builder.data["image"] = str(
            self.image_input.value
        )

        await interaction.response.send_message(
            "🎨 **اختر لون البانل:**",
            view=PanelColorView(
                self.builder
            ),
            ephemeral=True
        )


# ==================================
# اختيار لون البانل
# ==================================

class PanelColorSelect(discord.ui.Select):

    def __init__(self, builder):

        options = []

        for name in PANEL_COLORS:

            options.append(
                discord.SelectOption(
                    label=name,
                    value=name
                )
            )

        super().__init__(
            placeholder="اختر لون البانل",
            options=options
        )

        self.builder = builder

    async def callback(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        self.builder.data["color"] = self.values[0]

        await interaction.response.send_message(
            "🔘 **هل تريد إضافة أزرار للبانل؟**",
            view=YesNoMainButtonsView(
                self.builder
            ),
            ephemeral=True
        )


class PanelColorView(discord.ui.View):

    def __init__(self, builder):

        super().__init__(
            timeout=600
        )

        self.add_item(
            PanelColorSelect(builder)
        )


# ==================================
# نعم / لا للأزرار الرئيسية
# ==================================

class YesNoMainButtonsView(discord.ui.View):

    def __init__(self, builder):

        super().__init__(
            timeout=600
        )

        self.builder = builder

    @discord.ui.button(
        label="نعم",
        emoji="✅",
        style=discord.ButtonStyle.green
    )
    async def yes(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_message(
            "🔢 **كم زر تريد؟**",
            view=ButtonCountView(
                self.builder,
                main=True
            ),
            ephemeral=True
        )

    @discord.ui.button(
        label="لا",
        emoji="❌",
        style=discord.ButtonStyle.red
    )
    async def no(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        self.builder.data["buttons"] = []

        await publish_built_panel(
            interaction,
            self.builder
        )


# ==================================
# عدد الأزرار
# ==================================

class ButtonCountSelect(discord.ui.Select):

    def __init__(
        self,
        builder,
        main=True,
        parent_index=None
    ):

        options = []

        for number in range(0, 9):

            options.append(
                discord.SelectOption(
                    label=f"{number} زر",
                    value=str(number)
                )
            )

        super().__init__(
            placeholder="اختر عدد الأزرار",
            options=options
        )

        self.builder = builder
        self.main = main
        self.parent_index = parent_index

    async def callback(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        count = int(
            self.values[0]
        )

        # ==============================
        # أزرار البانل الرئيسي
        # ==============================

        if self.main:

            self.builder.data["buttons"] = []

            for i in range(count):

                self.builder.data["buttons"].append({
                    "label": "",
                    "emoji": "",
                    "panel": {
                        "title": "",
                        "description": "",
                        "image": "",
                        "color": "أزرق",
                        "buttons": []
                    }
                })

            if count == 0:

                await publish_built_panel(
                    interaction,
                    self.builder
                )

                return

            self.builder.current_button = 0

            await interaction.response.send_message(
                f"📝 **اسم الزر 1 من {count}**\n"
                f"اكتب اسم الزر:",
                ephemeral=True
            )

            await interaction.followup.send(
                "اضغط الزر التالي لكتابة اسم الزر:",
                view=ButtonNameStartView(
                    self.builder,
                    0
                ),
                ephemeral=True
            )

        # ==============================
        # أزرار داخل بانل الزر
        # ==============================

        else:

            parent = self.builder.data[
                "buttons"
            ][self.parent_index]

            parent["panel"]["buttons"] = []

            for i in range(count):

                parent["panel"]["buttons"].append({
                    "label": "",
                    "emoji": ""
                })

            if count == 0:

                await finish_main_button(
                    interaction,
                    self.builder,
                    self.parent_index
                )

                return

            self.builder.current_inner_button = 0

            await interaction.response.send_message(
                f"📝 **اسم الزر الداخلي 1 من {count}**",
                view=InnerButtonNameView(
                    self.builder,
                    self.parent_index,
                    0
                ),
                ephemeral=True
            )


class ButtonCountView(discord.ui.View):

    def __init__(
        self,
        builder,
        main=True,
        parent_index=None
    ):

        super().__init__(
            timeout=600
        )

        self.add_item(
            ButtonCountSelect(
                builder,
                main,
                parent_index
            )
        )


# ==================================
# إدخال اسم الزر
# ==================================

class ButtonNameModal(discord.ui.Modal):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            title=f"اسم الزر {index + 1}"
        )

        self.builder = builder
        self.index = index

        self.name_input = discord.ui.TextInput(
            label="اسم الزر",
            placeholder="مثال: التقديم",
            required=True,
            max_length=80
        )

        self.add_item(
            self.name_input
        )

    async def on_submit(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        self.builder.data["buttons"][
            self.index
        ]["label"] = str(
            self.name_input.value
        )

        await interaction.response.send_message(
            f"😀 **إيموجي الزر {self.index + 1}**\n"
            f"اكتب الإيموجي في الرسالة التالية.",
            view=EmojiInputView(
                self.builder,
                self.index
            ),
            ephemeral=True
        )


class ButtonNameStartView(discord.ui.View):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder
        self.index = index

    @discord.ui.button(
        label="كتابة اسم الزر",
        emoji="✏️",
        style=discord.ButtonStyle.primary
    )
    async def start(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_modal(
            ButtonNameModal(
                self.builder,
                self.index
            )
        )


# ==================================
# إيموجي الزر
# ==================================

class EmojiInputModal(discord.ui.Modal):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            title=f"إيموجي الزر {index + 1}"
        )

        self.builder = builder
        self.index = index

        self.emoji_input = discord.ui.TextInput(
            label="الإيموجي",
            placeholder="مثال: 🎫",
            required=False,
            max_length=100
        )

        self.add_item(
            self.emoji_input
        )

    async def on_submit(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        emoji = str(
            self.emoji_input.value
        ).strip()

        self.builder.data["buttons"][
            self.index
        ]["emoji"] = emoji

        await start_button_panel_setup(
            interaction,
            self.builder,
            self.index
        )


class EmojiInputView(discord.ui.View):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder
        self.index = index

    @discord.ui.button(
        label="كتابة الإيموجي",
        emoji="😀",
        style=discord.ButtonStyle.primary
    )
    async def start(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_modal(
            EmojiInputModal(
                self.builder,
                self.index
            )
        )


# ==================================
# بداية إعداد بانل الزر
# ==================================

async def start_button_panel_setup(
    interaction,
    builder,
    index
):

    button_number = index + 1

    await interaction.response.send_message(
        f"📋 **إعداد بانل الزر {button_number}**\n\n"
        f"أدخل العنوان والوصف ورابط الصورة:",
        view=ButtonPanelInfoView(
            builder,
            index
        ),
        ephemeral=True
    )


# ==================================
# معلومات بانل الزر
# ==================================

class ButtonPanelInfoModal(discord.ui.Modal):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            title=f"بانل الزر {index + 1}"
        )

        self.builder = builder
        self.index = index

        self.title_input = discord.ui.TextInput(
            label="عنوان",
            required=False,
            max_length=256
        )

        self.description_input = discord.ui.TextInput(
            label="وصف",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.image_input = discord.ui.TextInput(
            label="رابط الصورة",
            required=False,
            max_length=1000
        )

        self.add_item(
            self.title_input
        )

        self.add_item(
            self.description_input
        )

        self.add_item(
            self.image_input
        )

    async def on_submit(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        panel = self.builder.data[
            "buttons"
        ][self.index]["panel"]

        panel["title"] = str(
            self.title_input.value
        )

        panel["description"] = str(
            self.description_input.value
        )

        panel["image"] = str(
            self.image_input.value
        )

        await interaction.response.send_message(
            "🎨 **اختر لون بانل هذا الزر:**",
            view=ButtonPanelColorView(
                self.builder,
                self.index
            ),
            ephemeral=True
        )


class ButtonPanelInfoView(discord.ui.View):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder
        self.index = index

    @discord.ui.button(
        label="إدخال المعلومات",
        emoji="📝",
        style=discord.ButtonStyle.primary
    )
    async def start(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_modal(
            ButtonPanelInfoModal(
                self.builder,
                self.index
            )
        )


# ==================================
# لون بانل الزر
# ==================================

class ButtonPanelColorSelect(
    discord.ui.Select
):

    def __init__(
        self,
        builder,
        index
    ):

        options = [
            discord.SelectOption(
                label=name,
                value=name
            )
            for name in PANEL_COLORS
        ]

        super().__init__(
            placeholder="اختر اللون",
            options=options
        )

        self.builder = builder
        self.index = index

    async def callback(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        panel = self.builder.data[
            "buttons"
        ][self.index]["panel"]

        panel["color"] = self.values[0]

        await interaction.response.send_message(
            "🔘 **هل تريد أزرار داخل هذا البانل؟**",
            view=InnerButtonsYesNoView(
                self.builder,
                self.index
            ),
            ephemeral=True
        )


class ButtonPanelColorView(discord.ui.View):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            timeout=600
        )

        self.add_item(
            ButtonPanelColorSelect(
                builder,
                index
            )
        )


# ==================================
# نعم / لا للأزرار الداخلية
# ==================================

class InnerButtonsYesNoView(
    discord.ui.View
):

    def __init__(
        self,
        builder,
        index
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder
        self.index = index

    @discord.ui.button(
        label="نعم",
        emoji="✅",
        style=discord.ButtonStyle.green
    )
    async def yes(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_message(
            "🔢 **كم زر تريد داخل هذا البانل؟**",
            view=ButtonCountView(
                self.builder,
                main=False,
                parent_index=self.index
            ),
            ephemeral=True
        )

    @discord.ui.button(
        label="لا",
        emoji="❌",
        style=discord.ButtonStyle.red
    )
    async def no(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await finish_main_button(
            interaction,
            self.builder,
            self.index
        )


# ==================================
# إنهاء الزر الحالي والانتقال للي بعده
# ==================================

async def finish_main_button(
    interaction,
    builder,
    index
):

    total = len(
        builder.data["buttons"]
    )

    next_index = index + 1

    if next_index < total:

        builder.current_button = next_index

        await interaction.response.send_message(
            f"✅ تم الانتهاء من إعداد **الزر {index + 1}**.\n\n"
            f"➡️ الآن ننتقل إلى **الزر {next_index + 1} من {total}**.",
            view=ButtonNameStartView(
                builder,
                next_index
            ),
            ephemeral=True
        )

    else:

        await publish_built_panel(
            interaction,
            builder
        )


# ==================================
# الأزرار الداخلية
# ==================================

class InnerButtonNameView(
    discord.ui.View
):

    def __init__(
        self,
        builder,
        parent_index,
        inner_index
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder
        self.parent_index = parent_index
        self.inner_index = inner_index

    @discord.ui.button(
        label="كتابة اسم الزر",
        emoji="✏️",
        style=discord.ButtonStyle.primary
    )
    async def start(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_modal(
            InnerButtonNameModal(
                self.builder,
                self.parent_index,
                self.inner_index
            )
        )


class InnerButtonNameModal(
    discord.ui.Modal
):

    def __init__(
        self,
        builder,
        parent_index,
        inner_index
    ):

        super().__init__(
            title=f"اسم الزر الداخلي {inner_index + 1}"
        )

        self.builder = builder
        self.parent_index = parent_index
        self.inner_index = inner_index

        self.name_input = discord.ui.TextInput(
            label="اسم الزر",
            required=True,
            max_length=80
        )

        self.add_item(
            self.name_input
        )

    async def on_submit(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        inner = self.builder.data[
            "buttons"
        ][self.parent_index][
            "panel"
        ]["buttons"][self.inner_index]

        inner["label"] = str(
            self.name_input.value
        )

        await interaction.response.send_message(
            "😀 **إيموجي الزر:**",
            view=InnerEmojiView(
                self.builder,
                self.parent_index,
                self.inner_index
            ),
            ephemeral=True
        )


class InnerEmojiView(
    discord.ui.View
):

    def __init__(
        self,
        builder,
        parent_index,
        inner_index
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder
        self.parent_index = parent_index
        self.inner_index = inner_index

    @discord.ui.button(
        label="كتابة الإيموجي",
        emoji="😀",
        style=discord.ButtonStyle.primary
    )
    async def start(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_modal(
            InnerEmojiModal(
                self.builder,
                self.parent_index,
                self.inner_index
            )
        )


class InnerEmojiModal(
    discord.ui.Modal
):

    def __init__(
        self,
        builder,
        parent_index,
        inner_index
    ):

        super().__init__(
            title=f"إيموجي الزر الداخلي {inner_index + 1}"
        )

        self.builder = builder
        self.parent_index = parent_index
        self.inner_index = inner_index

        self.emoji_input = discord.ui.TextInput(
            label="الإيموجي",
            required=False,
            max_length=100
        )

        self.add_item(
            self.emoji_input
        )

    async def on_submit(self, interaction):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        inner = self.builder.data[
            "buttons"
        ][self.parent_index][
            "panel"
        ]["buttons"][self.inner_index]

        inner["emoji"] = str(
            self.emoji_input.value
        ).strip()

        total = len(
            self.builder.data[
                "buttons"
            ][self.parent_index][
                "panel"
            ]["buttons"]
        )

        next_inner = self.inner_index + 1

        if next_inner < total:

            await interaction.response.send_message(
                f"➡️ الآن **الزر الداخلي {next_inner + 1} من {total}**",
                view=InnerButtonNameView(
                    self.builder,
                    self.parent_index,
                    next_inner
                ),
                ephemeral=True
            )

        else:

            await finish_main_button(
                interaction,
                self.builder,
                self.parent_index
            )


# ==================================
# View النهائي للبانل الرئيسي
# ==================================

class BuiltPanelView(
    discord.ui.View
):

    def __init__(
        self,
        panel_id
    ):

        super().__init__(
            timeout=None
        )

        self.panel_id = str(
            panel_id
        )

        panel = None

        for p in general_panels:

            if str(p.get("id")) == self.panel_id:
                panel = p
                break

        if not panel:
            return

        for index, button_data in enumerate(
            panel.get("buttons", [])
        ):

            if not button_data:
                continue

            label = button_data.get(
                "label",
                f"زر {index + 1}"
            )

            emoji = button_data.get(
                "emoji"
            )

            button = discord.ui.Button(
                label=label[:80],
                style=discord.ButtonStyle.primary,
                custom_id=(
                    f"general_panel_main_"
                    f"{self.panel_id}_{index}"
                )
            )

            if emoji:
                try:
                    button.emoji = emoji
                except:
                    pass

            button.callback = self.make_callback(
                index
            )

            self.add_item(button)

    def make_callback(self, index):

        async def callback(
            interaction
        ):

            panel = None

            for p in general_panels:

                if str(p.get("id")) == self.panel_id:
                    panel = p
                    break

            if not panel:
                await interaction.response.send_message(
                    "❌ البانل غير موجود.",
                    ephemeral=True
                )
                return

            buttons = panel.get(
                "buttons",
                []
            )

            if index >= len(buttons):
                await interaction.response.send_message(
                    "❌ الزر غير موجود.",
                    ephemeral=True
                )
                return

            button_data = buttons[index]

            button_panel = button_data.get(
                "panel",
                {}
            )

            embed = build_panel_embed(
                button_panel
            )

            inner_view = BuiltInnerView(
                self.panel_id,
                index
            )

            if len(inner_view.children) > 0:

                await interaction.response.send_message(
                    embed=embed,
                    view=inner_view,
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

        return callback


# ==================================
# View الأزرار الداخلية
# ==================================

class BuiltInnerView(
    discord.ui.View
):

    def __init__(
        self,
        panel_id,
        parent_index
    ):

        super().__init__(
            timeout=None
        )

        panel = None

        for p in general_panels:

            if str(p.get("id")) == str(panel_id):
                panel = p
                break

        if not panel:
            return

        buttons = panel.get(
            "buttons",
            []
        )

        if parent_index >= len(buttons):
            return

        inner_buttons = buttons[
            parent_index
        ].get(
            "panel",
            {}
        ).get(
            "buttons",
            []
        )

        for index, data in enumerate(
            inner_buttons
        ):

            button = discord.ui.Button(
                label=data.get(
                    "label",
                    f"زر {index + 1}"
                )[:80],
                style=discord.ButtonStyle.secondary,
                custom_id=(
                    f"general_panel_inner_"
                    f"{panel_id}_{parent_index}_{index}"
                )
            )

            emoji = data.get(
                "emoji"
            )

            if emoji:
                try:
                    button.emoji = emoji
                except:
                    pass

            button.callback = self.make_callback(
                panel_id,
                parent_index,
                index
            )

            self.add_item(button)

    def make_callback(
        self,
        panel_id,
        parent_index,
        index
    ):

        async def callback(
            interaction
        ):

            panel = None

            for p in general_panels:

                if str(p.get("id")) == str(panel_id):
                    panel = p
                    break

            if not panel:
                await interaction.response.send_message(
                    "❌ البانل غير موجود.",
                    ephemeral=True
                )
                return

            try:

                data = panel[
                    "buttons"
                ][parent_index][
                    "panel"
                ]["buttons"][index]

            except:
                await interaction.response.send_message(
                    "❌ الزر غير موجود.",
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                f"🔘 **{data.get('label', 'زر')}**",
                ephemeral=True
            )

        return callback


# ==================================
# إرسال البانل النهائي
# ==================================

async def publish_built_panel(
    interaction,
    builder
):

    panel_id = (
        int(time.time() * 1000)
    )

    panel_data = {
        "id": panel_id,
        "guild_id": interaction.guild.id,
        "channel_id": interaction.channel.id,
        "message_id": None,
        "title": builder.data.get(
            "title",
            ""
        ),
        "description": builder.data.get(
            "description",
            ""
        ),
        "image": builder.data.get(
            "image",
            ""
        ),
        "color": builder.data.get(
            "color",
            "أزرق"
        ),
        "buttons": builder.data.get(
            "buttons",
            []
        )
    }

    embed = build_panel_embed(
        panel_data
    )

    view = BuiltPanelView(
        panel_id
    )

    # نخزن أولًا حتى BuiltPanelView يقدر يقرأ البيانات
    general_panels.append(
        panel_data
    )

    save_general_panels()

    try:

        message = await interaction.channel.send(
            embed=embed,
            view=view if len(view.children) else None
        )

        panel_data["message_id"] = message.id

        save_general_panels()

    except Exception as e:

        print(
            f"Panel send error: {e}"
        )

        try:
            await interaction.followup.send(
                "❌ حدث خطأ أثناء إرسال البانل.",
                ephemeral=True
            )
        except:
            pass

        return

    try:

        await interaction.response.send_message(
            "✅ **تم إنشاء البانل بنجاح!**",
            ephemeral=True
        )

    except discord.InteractionResponded:

        await interaction.followup.send(
            "✅ **تم إنشاء البانل بنجاح!**",
            ephemeral=True
        )


# ==================================
# /panel
# ==================================

@bot.tree.command(
    name="panel",
    description="إنشاء بانل تفاعلي متكامل"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def panel(
    interaction: discord.Interaction
):

    builder = PanelBuilder(
        interaction.user.id
    )

    embed = discord.Embed(
        title="🎨 منشئ البانلات",
        description=(
            "اضغط الزر بالأسفل لبدء إنشاء البانل.\n\n"
            "🔒 **جميع خطوات الإعداد خاصة بك.**"
        ),
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(
        embed=embed,
        view=PanelStartView(
            builder
        ),
        ephemeral=True
    )


# ==================================
# بداية إنشاء البانل
# ==================================

class PanelStartView(
    discord.ui.View
):

    def __init__(
        self,
        builder
    ):

        super().__init__(
            timeout=600
        )

        self.builder = builder

    @discord.ui.button(
        label="إنشاء بانل",
        emoji="🎨",
        style=discord.ButtonStyle.primary
    )
    async def start(
        self,
        interaction,
        button
    ):

        if not panel_owner(
            interaction,
            self.builder
        ):
            return

        await interaction.response.send_modal(
            MainPanelModal(
                self.builder
            )
        )


# ==================================
# Persistent Panels
# ==================================

async def restore_general_panels():

    for panel in general_panels:

        try:

            message_id = panel.get(
                "message_id"
            )

            if not message_id:
                continue

            bot.add_view(
                BuiltPanelView(
                    panel.get("id")
                ),
                message_id=message_id
            )

        except Exception as e:

            print(
                f"Failed to restore general panel: {e}"
            )

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
    
    await interaction.response.send_message(
        f"✅ تم حفظ إعدادات الترحيب بنجاح في روم {channel.mention}!",
        ephemeral=True
    )

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
        await channel.edit(name=data[guild_id]["name"].replace("{count}", str(guild.member_count)))

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

            embed = discord.Embed(title="👋 عضو جديد!", description=formatted_message, color=discord.Color.green(), timestamp=datetime.utcnow())
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
            await message.author.timeout(
                timedelta(minutes=5),
                reason="Mass Mention"
            )
        except:
            pass
        return True

    if config.get("mention") and len(message.mentions) >= 5:
        try:
            await message.delete()
            await message.author.timeout(
                timedelta(minutes=3),
                reason="Spam Mentions"
            )
        except:
            pass
        return True

    if config.get("badwords"):
        for word in bad_words:
            if word in content:
                try:
                    await message.delete()
                    await message.author.timeout(
                        timedelta(minutes=2),
                        reason="Bad Words"
                    )
                except:
                    pass
                return True

    if (
        (prot.get("anti_links") or prot.get("links"))
        and re.findall(r"https?://\S+", content)
    ):
        try:
            await message.delete()
            await message.author.timeout(
                timedelta(minutes=2),
                reason="رابط ممنوع"
            )
        except:
            pass
        return True

    if (
        (prot.get("anti_invite") or prot.get("invites"))
        and (
            "discord.gg/" in content
            or "discord.com/invite/" in content
        )
    ):
        try:
            await message.delete()
            await message.author.timeout(
                timedelta(minutes=5),
                reason="دعوة ديسكورد"
            )
        except:
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

    guild_id = str(message.guild.id)
    user_id_str = str(message.author.id)

    if guild_id not in xp_data:
        xp_data[guild_id] = {}

    if user_id_str not in xp_data[guild_id]:
        xp_data[guild_id][user_id_str] = {
            "xp": 0,
            "level": 1
        }

    xp_data[guild_id][user_id_str]["xp"] += 1

    current_xp = xp_data[guild_id][user_id_str]["xp"]
    current_level = xp_data[guild_id][user_id_str]["level"]

    if current_xp >= current_level * 100:
        xp_data[guild_id][user_id_str]["level"] += 1
        new_level = xp_data[guild_id][user_id_str]["level"]
        await message.channel.send(
            f"🎉 مبروك {message.author.mention} "
            f"وصلت للمستوى `{new_level}`!"
        )

    save_json(XP_FILE, xp_data)
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
                options.append(
                    discord.SelectOption(
                        label=str(name)[:100],
                        description=str(description)[:100],
                        value=str(name)
                    )
                )
        else:
            options = []
            for app_type in types:
                if not isinstance(app_type, dict) or not app_type.get("enabled", True):
                    continue

                name = app_type.get("name", "تقديم")
                description = app_type.get("description", "بدون وصف")

                options.append(
                    discord.SelectOption(
                        label=str(name)[:100],
                        description=str(description)[:100],
                        value=str(name)
                    )
                )

        options = options[:25]

        if not options:
            options.append(
                discord.SelectOption(
                    label="لا توجد أنواع تقديم",
                    description="لم تتم إضافة أي نوع تقديم بعد",
                    value="none"
                )
            )

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
            await interaction.response.send_message(
                "❌ لا توجد أنواع تقديم متاحة حاليًا.",
                ephemeral=True
            )
            return

        if has_application(
            interaction.guild.id,
            interaction.user.id
        ):
            await interaction.response.send_message(
                "❌ لديك تقديم قيد المراجعة بالفعل.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ApplyModal(
                interaction.guild.id,
                selected_type
            )
        )


class ApplyModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"تقديم {app_type}")

        self.guild_id = str(guild_id)
        self.app_type = app_type

        type_questions = (
            application_questions
            .get(self.guild_id, {})
            .get(
                app_type,
                [
                    "اسمك؟",
                    "عمرك؟",
                    "خبرتك؟",
                    "لماذا تريد الانضمام؟",
                    "أي معلومات إضافية؟"
                ]
            )
        )

        self.inputs = []

        for q in type_questions[:5]:
            if q and q != "اختياري":
                item = discord.ui.TextInput(
                    label=str(q)[:45],
                    style=discord.TextStyle.paragraph,
                    required=False
                )
                self.inputs.append(item)
                self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)

        if has_application(
            interaction.guild.id,
            interaction.user.id
        ):
            await interaction.response.send_message(
                "❌ لديك تقديم قيد المراجعة بالفعل.",
                ephemeral=True
            )
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
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        })

        save_all_applications()

        config = application_config.get(gid, {})
        result_channel_id = config.get("results_channel") or config.get("channel")
        result_channel = interaction.guild.get_channel(result_channel_id) if result_channel_id else None

        if result_channel:
            embed = discord.Embed(
                title="📩 تقديم جديد",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="👤 العضو",
                value=interaction.user.mention,
                inline=False
            )

            embed.add_field(
                name="📌 النوع",
                value=self.app_type,
                inline=False
            )

            type_questions = (
                application_questions
                .get(gid, {})
                .get(
                    self.app_type,
                    [
                        "السؤال 1",
                        "السؤال 2",
                        "السؤال 3",
                        "السؤال 4",
                        "السؤال 5"
                    ]
                )
            )

            for i, answer in enumerate(answers):
                q_name = type_questions[i] if i < len(type_questions) else f"السؤال {i + 1}"
                embed.add_field(
                    name=str(q_name)[:256],
                    value=str(answer)[:1024],
                    inline=False
                )

            embed.add_field(
                name="📌 الحالة",
                value="🟡 **قيد المراجعة**",
                inline=False
            )

            await result_channel.send(
                embed=embed,
                view=ApplicationControlView(
                    interaction.user.id,
                    app_id
                )
            )

        await interaction.response.send_message(
            "✅ تم إرسال التقديم بنجاح.",
            ephemeral=True
        )


class ApplicationControlView(discord.ui.View):
    def __init__(self, user_id, app_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.app_id = app_id

    @discord.ui.button(
        label="قبول",
        emoji="✅",
        style=discord.ButtonStyle.green,
        custom_id="application_accept"
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
            await interaction.response.send_message("❌ لم يتم العثور على التقديم.", ephemeral=True)
            return

        if application.get("status") != "pending":
            await interaction.response.send_message("⚠️ تم اتخاذ قرار بشأن هذا التقديم مسبقًا.", ephemeral=True)
            return

        application["status"] = "accepted"
        application["decision_by"] = interaction.user.id
        application["decision_time"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        save_all_applications()

        member = interaction.guild.get_member(self.user_id)
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
            except:
                pass

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()

            status_text = (
                "🟢 **مقبول**\n"
                f"👮 بواسطة: {interaction.user.mention}\n"
                f"🕐 الوقت: {application['decision_time']}"
            )

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

    @discord.ui.button(
        label="رفض",
        emoji="❌",
        style=discord.ButtonStyle.red,
        custom_id="application_reject"
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
            await interaction.response.send_message("❌ لم يتم العثور على التقديم.", ephemeral=True)
            return

        if application.get("status") != "pending":
            await interaction.response.send_message("⚠️ تم اتخاذ قرار بشأن هذا التقديم مسبقًا.", ephemeral=True)
            return

        application["status"] = "rejected"
        application["decision_by"] = interaction.user.id
        application["decision_time"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        save_all_applications()

        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send(f"❌ تم رفض تقديمك.\n📋 نوع التقديم: `{application.get('type')}`")
            except:
                pass

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()

            status_text = (
                "🔴 **مرفوض**\n"
                f"👮 بواسطة: {interaction.user.mention}\n"
                f"🕐 الوقت: {application['decision_time']}"
            )

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

@bot.tree.command(
    name="application-panel",
    description="إنشاء بانل تقديم متطور"
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
        "✅ تم إنشاء بانل التقديم بنجاح.",
        ephemeral=True
    )

@bot.tree.command(name="application-add-type", description="إضافة نوع تقديم مع رتبة خاصة وتحديث البانل تلقائياً")
@app_commands.checks.has_permissions(administrator=True)
async def application_add_type(
    interaction: discord.Interaction,
    name: str,
    role: discord.Role,
    description: str = "بدون وصف"
):
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
            await interaction.response.send_message(
                "❌ هذا النوع موجود مسبقاً.",
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

            await message.edit(
                embed=embed,
                view=ApplicationSelectView(gid)
            )

            updated += 1
            # إضافة فاصل زمني لتفادي Rate Limit عند التعديل المتكرر للبانلات
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"Panel update error: {e}")

    await interaction.response.send_message(
        f"✅ تمت إضافة نوع التقديم: `{name}`\n"
        f"🎭 الرتبة: {role.mention}\n"
        f"🔄 تم تحديث {updated} بانل تلقائياً.",
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

# ----------------------------------------------------
# الحل المحسّن لأمر reset-panels (تجنب 429 و 10062)
# ----------------------------------------------------
@bot.tree.command(name="reset-panels", description="إزالة الأزرار من البانلات القديمة بأمان")
@app_commands.checks.has_permissions(administrator=True)
async def reset_panels(interaction: discord.Interaction):
    # تثبيت التفاعل فوراً لمنع انتهاء المهلة (Unknown interaction 10062)
    await interaction.response.defer(ephemeral=True)

    count = 0
    checked = 0

    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=50):
                    checked += 1

                    if msg.author != bot.user:
                        continue

                    if not msg.components:
                        continue

                    try:
                        await msg.edit(view=None)
                        count += 1
                        # تخفيف الضغط لتجنب Rate Limit (429)
                        await asyncio.sleep(0.5)

                    except discord.HTTPException as e:
                        if e.status == 429:
                            await asyncio.sleep(5)
                        else:
                            print(f"Panel edit error: {e}")

            except discord.Forbidden:
                continue
            except discord.HTTPException as e:
                print(f"History error in #{channel.name}: {e}")
            except Exception as e:
                print(f"Reset error in #{channel.name}: {e}")

    await interaction.followup.send(
        f"♻️ تم Reset عدد `{count}` بانل.\n"
        f"🔎 تم فحص `{checked}` رسالة.",
        ephemeral=True
    )

# ==================================
# Reaction Roles System
# ==================================

class ReactionRoleView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(
        label="✅ أخذ الرتبة",
        style=discord.ButtonStyle.green,
        custom_id="take_role_btn"
    )
    async def take_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("⚠️ أنت تملك هذه الرتبة بالفعل", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ تم إعطاؤك رتبة {role.mention}", ephemeral=True)

    @discord.ui.button(
        label="❌ إزالة الرتبة",
        style=discord.ButtonStyle.red,
        custom_id="remove_role_btn"
    )
    async def remove_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)
            return

        if role not in interaction.user.roles:
            await interaction.response.send_message("⚠️ أنت لا تملك هذه الرتبة", ephemeral=True)
            return

        await interaction.user.remove_roles(role)
        await interaction.response.send_message(f"❌ تم إزالة رتبة {role.mention}", ephemeral=True)

    @discord.ui.button(
        label="👥 عرض الأعضاء",
        style=discord.ButtonStyle.blurple,
        custom_id="show_role_members_btn"
    )
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

        embed = discord.Embed(
            title=f"👥 أعضاء رتبة {role.name}",
            description=text,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(
    name="reaction-role",
    description="إنشاء بانل أخذ/إزالة رتبة عبر الأزرار"
)
@app_commands.describe(
    channel="الروم المراد إرسال البانل إليه",
    role="الرتبة المراد إعطاؤها للعضو",
    title="عنوان الرسالة (Embed)",
    description="وصف الرسالة (Embed)"
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
        f"✅ تم إنشاء بانل الرتبة بنجاح في {channel.mention} لرتبة {role.mention}",
        ephemeral=True
    )

# ==================================
# أوامر الإدارة والعقوبات (Moderation)
# ==================================

@bot.tree.command(name="ban", description="حظر عضو")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم حظر {member.mention}")
    await send_log(interaction.guild, "🔨 Ban", f"العضو: {member.mention}\nالسبب: {reason}", discord.Color.red())

@bot.tree.command(name="kick", description="طرد عضو")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 تم طرد {member.mention}")

@bot.tree.command(name="mute", description="كتم عضو (Timeout)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "لا يوجد سبب"):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(f"🔇 تم كتم {member.mention} لمدة {minutes} دقيقة.")

@bot.tree.command(name="unmute", description="فك كتم عضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None, reason="فك الكتم")
    await interaction.response.send_message(f"🔊 تم فك الكتم عن {member.mention}")

@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings = load_json(WARNINGS_FILE, {})
    gid, uid = str(interaction.guild.id), str(member.id)
    if gid not in warnings: warnings[gid] = {}
    if uid not in warnings[gid]: warnings[gid][uid] = []
    warnings[gid][uid].append({"reason": reason, "date": datetime.utcnow().strftime("%Y-%m-%d")})
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

START_TIME = datetime.utcnow()

@bot.tree.command(name="move", description="نقل عضو إلى روم صوتي")
@app_commands.checks.has_permissions(move_members=True)
async def move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
    if member.voice:
        await member.move_to(channel)
        await interaction.response.send_message(f"✅ تم نقل {member.mention} إلى {channel.mention}")
    else:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي.", ephemeral=True)

@bot.tree.command(name="deafen", description="تغميض صوت عضو")
@app_commands.checks.has_permissions(deafen_members=True)
async def deafen(interaction: discord.Interaction, member: discord.Member):
    await member.edit(deafen=True)
    await interaction.response.send_message(f"🔇 تم تغميض {member.mention}")

@bot.tree.command(name="undeafen", description="إلغاء تغميض صوت عضو")
@app_commands.checks.has_permissions(deafen_members=True)
async def undeafen(interaction: discord.Interaction, member: discord.Member):
    await member.edit(deafen=False)
    await interaction.response.send_message(f"🔊 تم إلغاء تغميض {member.mention}")

@bot.tree.command(name="timeout", description="إعطاء تايم اوت لعضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message(f"⏳ تم إعطاء {member.mention} تايم اوت لمدة {minutes} دقيقة")

@bot.tree.command(name="rolelist", description="عرض رتب السيرفر")
async def rolelist(interaction: discord.Interaction):
    roles = interaction.guild.roles[1:]
    text = "\n".join([f"{r.mention}" for r in roles[:50]])
    embed = discord.Embed(title="📋 رتب السيرفر", description=text)
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
    delta = datetime.utcnow() - START_TIME
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
    except:
        await interaction.response.send_message("❌ لا أستطيع تغيير الاسم", ephemeral=True)

@bot.tree.command(name="addrole", description="إعطاء رتبة لعضو")
@app_commands.checks.has_permissions(manage_roles=True)
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ تم إعطاء {member.mention} رتبة {role.mention}")
    except:
        await interaction.response.send_message("❌ لا أستطيع إعطاء هذه الرتبة", ephemeral=True)

@bot.tree.command(name="removerole", description="إزالة رتبة من عضو")
@app_commands.checks.has_permissions(manage_roles=True)
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"❌ تم إزالة رتبة {role.mention} من {member.mention}")
    except:
        await interaction.response.send_message("❌ لا أستطيع إزالة هذه الرتبة", ephemeral=True)

@bot.tree.command(name="createrole", description="إنشاء رتبة جديدة")
@app_commands.checks.has_permissions(manage_roles=True)
async def createrole(interaction: discord.Interaction, name: str):
    role = await interaction.guild.create_role(name=name)
    await interaction.response.send_message(f"✅ تم إنشاء الرتبة {role.mention}")

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
            except:
                pass
    await interaction.followup.send(f"✅ تم إعطاء الرتبة {role.mention} لـ {count} عضو")

@bot.tree.command(name="dm", description="إرسال رسالة خاصة لعضو")
@app_commands.checks.has_permissions(administrator=True)
async def dm(interaction: discord.Interaction, member: discord.Member, message: str):
    try:
        await member.send(message)
        await interaction.response.send_message("✅ تم إرسال الرسالة", ephemeral=True)
    except:
        await interaction.response.send_message("❌ لا يمكن إرسال رسالة لهذا العضو", ephemeral=True)

@bot.tree.command(name="announce", description="إرسال إعلان Embed")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"إعلان بواسطة {interaction.user}")
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ تم إرسال الإعلان", ephemeral=True)

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
@app_commands.checks.has_permissions(manage_messages=True)
async def suggest(interaction: discord.Interaction, suggestion: str):
    channel_id = suggestion_config.get(str(interaction.guild.id))
    if not channel_id:
        await interaction.response.send_message("❌ لم يتم إعداد روم الاقتراحات", ephemeral=True)
        return
    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ الروم غير موجود", ephemeral=True)
        return
    embed = discord.Embed(title="💡 اقتراح جديد", description=suggestion, color=discord.Color.blue(), timestamp=datetime.utcnow())
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
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue(), timestamp=datetime.utcnow())
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
    embed.add_field(name="🛡️ الحماية", value="/anti-links, /anti-invite, /badword-add", inline=False)
    embed.add_field(name="💤 نظام الـ AFK", value="/afk, /afk-status, /afk-list, /afk-remove", inline=False)
    await interaction.response.send_message(embed=embed)

# ==================================
# تشغيل البوت والأحداث العامة
# ==================================

@bot.event
async def on_ready():
    print(f"🤖 Bot Online: {bot.user}")
    
    # الأنظمة القديمة عندك
    for panel in persistent_panels:
        try:
            ptype = panel.get("type")
            if ptype == "application":
                bot.add_view(ApplicationSelectView(panel["guild_id"]), message_id=panel["message_id"])
            elif ptype == "reaction_role":
                bot.add_view(ReactionRoleView(panel["role_id"]), message_id=panel["message_id"])
        except Exception as e:
            print(f"Failed persistent view: {e}")
            
    # استعادة البانلات العامة الجديدة
    await restore_general_panels()
            
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
