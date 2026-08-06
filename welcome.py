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

# تحميل بيانات نظام التقديمات المتطور
applications_data = load_json(APPLICATIONS_FILE, {})
application_config = load_json(APPLICATION_CONFIG_FILE, {})
application_types = load_json(APPLICATION_TYPES_FILE, {})
application_questions = load_json(APPLICATION_QUESTIONS_FILE, {})
application_decisions = load_json(APPLICATION_DECISIONS_FILE, {})
application_cooldowns = load_json(APPLICATION_COOLDOWN_FILE, {})

def save_persistent():
    save_json(PANELS_FILE, persistent_panels)

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
    await update_member_count(member.guild)
    await send_log(member.guild, "📤 خروج عضو", f"العضو: {member.mention} (`{member.id}`)", discord.Color.dark_red())

# ==================================
# فحص الحماية المتقدم (Anti Check)
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
            await message.author.timeout(timedelta(minutes=2), reason="رابط ممنوع")
        except: pass
        return True

    if (prot.get("anti_invite") or prot.get("invites")) and ("discord.gg/" in content or "discord.com/invite/" in content):
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="دعوة ديسكورد")
        except: pass
        return True

    return False

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if await anti_check(message):
        return

    # معالجة XP البسيطة
    guild_id = str(message.guild.id)
    user_id_str = str(message.author.id)
    if guild_id not in xp_data: xp_data[guild_id] = {}
    if user_id_str not in xp_data[guild_id]: xp_data[guild_id][user_id_str] = {"xp": 0, "level": 1}
    
    xp_data[guild_id][user_id_str]["xp"] += 1
    if xp_data[guild_id][user_id_str]["xp"] >= xp_data[guild_id][user_id_str]["level"] * 100:
        xp_data[guild_id][user_id_str]["level"] += 1
        await message.channel.send(f"🎉 مبروك {message.author.mention} وصلت للمستوى `{xp_data[guild_id][user_id_str]['level']}`!")

    await bot.process_commands(message)

# ==================================
# نظام التقديمات المتطور (المحدث والشامل)
# ==================================

def has_application(guild_id, user_id):
    for app in applications_data.get(str(guild_id), []):
        if app["user_id"] == user_id and app["status"] == "pending":
            return True
    return False

# ================================
# مودال الأسئلة
# ================================

class ApplyModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"تقديم {app_type}")
        self.guild_id = str(guild_id)
        self.app_type = app_type

        # محاولة جلب الأسئلة المخصصة للنوع المحدد، وإلا العامة، وإلا الافتراضية
        type_questions = application_questions.get(self.guild_id, {}).get(app_type)
        if not type_questions:
            type_questions = application_questions.get(
                self.guild_id,
                ["اسمك؟", "عمرك؟", "خبرتك؟", "اختياري", "اختياري"]
            )

        self.inputs = []
        for q in type_questions[:5]:
            if q and q != "اختياري":
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
                "❌ لديك تقديم قيد المراجعة بالفعل.",
                ephemeral=True
            )
            return

        app_id = random.randint(100000, 999999)
        answers = []
        for i in self.inputs:
            answers.append(i.value or "لم يكتب")

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
            embed.add_field(name="👤 العضو", value=interaction.user.mention, inline=False)
            embed.add_field(name="📌 النوع", value=self.app_type, inline=False)

            type_questions = application_questions.get(gid, {}).get(self.app_type, ["السؤال 1", "السؤال 2", "السؤال 3"])
            for i, a in enumerate(answers):
                q_name = type_questions[i] if i < len(type_questions) else f"السؤال {i+1}"
                embed.add_field(name=q_name, value=a[:1024], inline=False)

            await result_channel.send(
                embed=embed,
                view=ApplicationControlView(interaction.user.id, app_id)
            )

        await interaction.response.send_message(
            "✅ تم إرسال التقديم بنجاح.",
            ephemeral=True
        )

# ================================
# أزرار الإدارة
# ================================

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
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = str(interaction.guild.id)
        for app in applications_data.get(gid, []):
            if app["id"] == self.app_id:
                app["status"] = "accepted"

        save_all_applications()

        member = interaction.guild.get_member(self.user_id)
        role_id = application_config.get(gid, {}).get("accepted_role")

        if role_id and member:
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass

        if member:
            try:
                await member.send("🎉 تم قبول تقديمك!")
            except:
                pass

        await interaction.response.send_message(
            "✅ تم قبول التقديم.",
            ephemeral=True
        )

    @discord.ui.button(
        label="رفض",
        emoji="❌",
        style=discord.ButtonStyle.red,
        custom_id="application_reject"
    )
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = str(interaction.guild.id)
        for app in applications_data.get(gid, []):
            if app["id"] == self.app_id:
                app["status"] = "rejected"

        save_all_applications()

        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send("❌ عذراً، تم رفض تقديمك.")
            except:
                pass

        await interaction.response.send_message(
            "❌ تم رفض التقديم.",
            ephemeral=True
        )

# ================================
# قائمة أنواع التقديم (Select Menu) مع إمكانية تخصيص الزر
# ================================

class ApplicationButtonView(discord.ui.View):
    def __init__(self, guild_id, button_name: str = None, button_emoji: str = None):
        super().__init__(timeout=None)
        self.add_item(ApplicationMenu(guild_id))

class ApplicationMenu(discord.ui.Select):
    def __init__(self, guild_id):
        options = []
        types = application_types.get(str(guild_id), {})
        
        if not types:
            options.append(discord.SelectOption(label="تقديم عام", description="التقديم الافتراضي للبوت"))
        else:
            for name in types:
                desc = types[name].get("description", "") if isinstance(types[name], dict) else ""
                options.append(discord.SelectOption(label=name, description=desc[:100]))

        super().__init__(
            placeholder="اختر نوع التقديم",
            options=options,
            custom_id="application_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            ApplyModal(
                interaction.guild.id,
                self.values[0]
            )
        )

class ApplicationMenuView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.add_item(ApplicationMenu(guild_id))

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
        view=ApplicationMenuView(interaction.guild.id)
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

@bot.tree.command(name="application-update-panel", description="تحديث بانل التقديم الحالي")
@app_commands.checks.has_permissions(administrator=True)
async def application_update_panel(
    interaction: discord.Interaction,
    title: str,
    description: str,
    button_name: str,
    button_emoji: str,
    image: str = None
):
    gid = str(interaction.guild.id)

    if gid not in application_config:
        await interaction.response.send_message(
            "❌ لا يوجد بانل تقديم معد مسبقاً.",
            ephemeral=True
        )
        return

    config = application_config[gid]

    channel_id = config.get("panel_channel") or config.get("channel")
    old_message_id = None

    for panel in persistent_panels:
        if panel.get("type") == "application" and str(panel.get("guild_id")) == gid:
            old_message_id = panel.get("message_id")
            break

    if not old_message_id:
        await interaction.response.send_message(
            "❌ لم يتم العثور على رسالة البانل.",
            ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(channel_id)

    if not channel:
        await interaction.response.send_message(
            "❌ روم البانل غير موجود.",
            ephemeral=True
        )
        return

    try:
        msg = await channel.fetch_message(old_message_id)

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        if image:
            embed.set_image(url=image)

        await msg.edit(
            embed=embed,
            view=ApplicationButtonView(
                interaction.guild.id,
                button_name,
                button_emoji
            )
        )

        # حفظ التحديثات
        application_config[gid]["title"] = title
        application_config[gid]["description"] = description
        application_config[gid]["button_name"] = button_name
        application_config[gid]["button_emoji"] = button_emoji
        application_config[gid]["image"] = image

        save_all_applications()

        await interaction.response.send_message(
            "✅ تم تحديث بانل التقديم بنجاح.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ حدث خطأ: {e}",
            ephemeral=True
        )

@bot.tree.command(name="application-add-type", description="إضافة نوع تقديم جديد")
@app_commands.checks.has_permissions(administrator=True)
async def application_add_type(interaction: discord.Interaction, name: str, description: str = "بدون وصف"):
    gid = str(interaction.guild.id)
    if gid not in application_types: 
        application_types[gid] = {}
    application_types[gid][name] = {"description": description}
    save_all_applications()
    await interaction.response.send_message(f"✅ تم إضافة نوع التقديم: `{name}`", ephemeral=True)

@bot.tree.command(name="application-remove-type", description="حذف نوع تقديم")
@app_commands.checks.has_permissions(administrator=True)
async def application_remove_type(interaction: discord.Interaction, name: str):
    gid = str(interaction.guild.id)
    if name in application_types.get(gid, {}):
        del application_types[gid][name]
        save_all_applications()
        await interaction.response.send_message("✅ تم حذف النوع.", ephemeral=True)
    else:
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

@bot.tree.command(name="application-set-role", description="تحديد رتبة المقبولين في التقديمات")
@app_commands.checks.has_permissions(administrator=True)
async def application_set_role(interaction: discord.Interaction, role: discord.Role):
    gid = str(interaction.guild.id)
    if gid not in application_config: 
        application_config[gid] = {}
    application_config[gid]["accepted_role"] = role.id
    save_all_applications()
    await interaction.response.send_message(f"✅ سيتم إعطاء رتبة {role.mention} للمقبولين تلقائياً", ephemeral=True)

@bot.tree.command(name="application-button", description="تغيير اسم الزر والإيموجي")
@app_commands.checks.has_permissions(administrator=True)
async def application_button(interaction: discord.Interaction, button_name: str, emoji: str):
    gid = str(interaction.guild.id)
    if gid not in application_config: 
        application_config[gid] = {}
    application_config[gid]["button_name"] = button_name
    application_config[gid]["button_emoji"] = emoji
    save_all_applications()
    await interaction.response.send_message("✅ تم تعديل زر التقديم.", ephemeral=True)

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

@bot.tree.command(name="reset-panels", description="إعادة تحميل جميع البانلات")
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
    await interaction.response.send_message(f"♻️ تم Reset عدد `{count}` بانل.", ephemeral=True)

# ==================================
# Reaction Roles System
# ==================================

class ReactionRoleView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="✅ أخذ/إزالة الرتبة", style=discord.ButtonStyle.green, custom_id="toggle_role_btn")
    async def toggle_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ تم إزالة رتبة {role.mention} منك", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ تم إعطاؤك رتبة {role.mention}", ephemeral=True)

@bot.tree.command(name="reaction-role", description="إنشاء زر للحصول على رتبة")
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role(interaction: discord.Interaction, role: discord.Role, channel: discord.TextChannel, text: str):
    embed = discord.Embed(title="🎭 رتبة تلقائية", description=text, color=discord.Color.blue())
    msg = await channel.send(embed=embed, view=ReactionRoleView(role.id))
    persistent_panels.append({"type": "reaction_role", "guild_id": interaction.guild.id, "channel_id": channel.id, "message_id": msg.id, "role_id": role.id})
    save_persistent()
    await interaction.response.send_message("✅ تم إنشاء زر الرتبة بنجاح", ephemeral=True)

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

@bot.tree.command(name="undeafen", description="إلغاء تغميض عضو")
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
    embed.add_field(name="📝 التقديمات والترحيب", value="/application-panel, /application-update-panel, /application-add-type, /application-remove-type, /application-set-questions, /set-welcome, /member-count-setup", inline=False)
    embed.add_field(name="🛡️ الحماية", value="/anti-links, /anti-invite, /badword-add", inline=False)
    await interaction.response.send_message(embed=embed)

# ==================================
# تشغيل البوت والأحداث العامة
# ==================================

@bot.event
async def on_ready():
    print(f"🤖 Bot Online: {bot.user}")
    for panel in persistent_panels:
        try:
            ptype = panel.get("type")
            if ptype == "application":
                bot.add_view(ApplicationMenuView(panel["guild_id"]), message_id=panel["message_id"])
            elif ptype == "reaction_role":
                bot.add_view(ReactionRoleView(panel["role_id"]), message_id=panel["message_id"])
        except Exception as e:
            print(f"Failed persistent view: {e}")
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
