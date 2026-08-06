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

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==================================
# الملفات وقواعد البيانات
# ==================================

WELCOME_CONFIG_FILE = "welcome_config.json"
LOGS_CONFIG_FILE = "logs_config.json"
MOD_CONFIG_FILE = "mod_roles.json"
GIVEAWAYS_FILE = "giveaways_database.json"
ENDED_GIVEAWAYS_FILE = "ended_giveaways_database.json"
WARNINGS_FILE = "warnings.json"
CONFIG_FILE = "config.json"
CUSTOM_COMMANDS_FILE = "custom_commands.json"
SETTINGS_FILE = "settings.json"
ERROR_LOG_FILE = "error_logs.json"
ALLOWED_CHANNELS_FILE = "allowed_channels.json"
PROTECTION_FILE = "protection_config.json"
SUGGESTIONS_FILE = "suggestions.json"
XP_FILE = "xp.json"
AFK_FILE = "afk.json"
REACTION_ROLES_FILE = "reaction_roles.json"
BACKUP_FILE = "server_backup_info.json"
ANTI_CONFIG_FILE = "anti_config.json"
BAD_WORDS_FILE = "bad_words.json"
PERSISTENT_FILE = "persistent_panels.json"

# ملفات نظام التقديمات
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

welcome_config = load_json(WELCOME_CONFIG_FILE)
mod_roles = load_json(MOD_CONFIG_FILE)
custom_commands = load_json(CUSTOM_COMMANDS_FILE)
protection_config = load_json(PROTECTION_FILE)
suggestions = load_json(SUGGESTIONS_FILE)
xp_data = load_json(XP_FILE)
afk_users = load_json(AFK_FILE)
reaction_roles = load_json(REACTION_ROLES_FILE)
allowed_channels = load_json(ALLOWED_CHANNELS_FILE)
ended_giveaways = load_json(ENDED_GIVEAWAYS_FILE)
anti_config = load_json(ANTI_CONFIG_FILE)
bad_words = load_json(BAD_WORDS_FILE, [])
persistent_panels = load_json(PERSISTENT_FILE, [])
giveaways = {}

# تحميل بيانات نظام التقديمات
applications_data = load_json(APPLICATIONS_FILE, {})
application_config = load_json(APPLICATION_CONFIG_FILE, {})
application_types = load_json(APPLICATION_TYPES_FILE, {})
application_questions = load_json(APPLICATION_QUESTIONS_FILE, {})
application_decisions = load_json(APPLICATION_DECISIONS_FILE, {})
application_cooldowns = load_json(APPLICATION_COOLDOWN_FILE, {})

def save_persistent():
    save_json(PERSISTENT_FILE, persistent_panels)

def save_applications():
    save_json(APPLICATIONS_FILE, applications_data)

def save_application_config():
    save_json(APPLICATION_CONFIG_FILE, application_config)

def save_application_types():
    save_json(APPLICATION_TYPES_FILE, application_types)

def save_application_questions():
    save_json(APPLICATION_QUESTIONS_FILE, application_questions)

def save_application_decisions():
    save_json(APPLICATION_DECISIONS_FILE, application_decisions)

def save_application_cooldowns():
    save_json(APPLICATION_COOLDOWN_FILE, application_cooldowns)

# ==================================
# نظام السجلات (Logs System)
# ==================================

async def send_log(guild, title, description, color):
    config = load_json(LOGS_CONFIG_FILE)
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
    config = load_json(LOGS_CONFIG_FILE)
    config[str(interaction.guild.id)] = channel.id
    save_json(LOGS_CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ تم ضبط روم السجلات بنجاح في {channel.mention}", ephemeral=True)

# ==================================
# التحقق من صلاحيات الإدارة
# ==================================

def has_mod_permission(member):
    if member.guild_permissions.administrator:
        return True
    role_id = mod_roles.get(str(member.guild.id))
    if role_id:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            return True
    return False

# ==================================
# الأحداث الأساسية (On Member Join / Remove)
# ==================================

raid_tracker = {}

@bot.event
async def on_member_join(member):
    guild = member.guild
    guild_id = str(guild.id)
    
    if guild_id in welcome_config:
        data = welcome_config[guild_id]
        channel_id = data.get("channel_id")
        raw_message = data.get("message", "أهلاً بك {user} في السيرفر!")
        channel = guild.get_channel(channel_id)
        if channel:
            formatted_message = raw_message.replace("{user}", member.mention)
            embed = discord.Embed(
                title="👋 عضو جديد!",
                description=formatted_message,
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)
            try:
                await channel.send(content=member.mention, embed=embed)
            except:
                pass

    cfg = load_json(CONFIG_FILE)
    role_id = cfg.get(guild_id, {}).get("autorole_id")
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    prot = protection_config.get(guild_id, {})
    if prot.get("anti_raid"):
        now = time.time()
        if guild.id not in raid_tracker:
            raid_tracker[guild.id] = []
        raid_tracker[guild.id].append(now)
        raid_tracker[guild.id] = [x for x in raid_tracker[guild.id] if now - x <= prot.get("raid_time", 10)]
        
        if len(raid_tracker[guild.id]) >= prot.get("raid_limit", 5):
            try:
                await guild.edit(verification_level=discord.VerificationLevel.high)
            except:
                pass
            
            try:
                await member.kick(reason="Anti-Raid: Mass Joining Detected")
            except:
                pass

            await send_log(
                guild, 
                "🚨 Raid Detected & Punished", 
                f"تم اكتشاف هجوم دخول أعضاء وتم اتخاذ إجراءات أمان تلقائية!\nالعدد: `{len(raid_tracker[guild.id])}`\nالإجراء: رفع مستوى التحقق وطرد الحسابات المخالفة.", 
                discord.Color.red()
            )

    await send_log(guild, "📥 دخول عضو", f"العضو: {member.mention} (`{member.id}`)", discord.Color.green())

@bot.event
async def on_member_remove(member):
    await send_log(member.guild, "📤 خروج عضو", f"العضو: {member.mention} (`{member.id}`)", discord.Color.dark_red())

# ==================================
# فحص الحماية المتقدم (Anti Check)
# ==================================

async def anti_check(message):
    if not message.guild or message.author.bot:
        return

    config = anti_config.get(str(message.guild.id), {})

    if config.get("massmention"):
        if message.mention_everyone:
            try:
                await message.delete()
                await message.author.timeout(timedelta(minutes=5), reason="Mass Mention")
                await send_log(
                    message.guild,
                    "🚨 Mass Mention",
                    f"العضو: {message.author.mention}\nالسبب: منشن جماعي\nالعقوبة: Timeout 5 دقائق",
                    discord.Color.red()
                )
            except:
                pass
            return

    if config.get("mention"):
        if len(message.mentions) >= 5:
            try:
                await message.delete()
                await message.author.timeout(timedelta(minutes=3), reason="Spam Mentions")
                await send_log(
                    message.guild,
                    "🚨 Mention Spam",
                    f"العضو: {message.author.mention}\nعدد المنشنات: {len(message.mentions)}\nالعقوبة: Timeout",
                    discord.Color.orange()
                )
            except:
                pass
            return

    if config.get("badwords"):
        content = message.content.lower()
        for word in bad_words:
            if word in content:
                try:
                    await message.delete()
                    await message.author.timeout(timedelta(minutes=2), reason="Bad Words")
                    await send_log(
                        message.guild,
                        "🤬 كلمة ممنوعة",
                        f"العضو: {message.author.mention}\nالكلمة: `{word}`\nالعقوبة: Timeout",
                        discord.Color.dark_red()
                    )
                except:
                    pass
                return

# ==================================
# نظام معالجة الرسائل الموحد (On Message)
# ==================================

user_message_timestamps = {}

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    await anti_check(message)

    guild_id = str(message.guild.id)
    content = message.content.lower()

    user_id_str = str(message.author.id)
    if user_id_str in afk_users:
        del afk_users[user_id_str]
        save_json(AFK_FILE, afk_users)
        try:
            await message.reply(
                "👋 أهلاً بعودتك، تم إزالة AFK عنك.",
                delete_after=5
            )
        except:
            pass

    for member in message.mentions:
        member_id_str = str(member.id)
        if member_id_str in afk_users:
            data = afk_users[member_id_str]
            try:
                await message.reply(
                    f"💤 {member.mention} حالياً AFK\n"
                    f"📝 السبب: `{data['reason']}`\n"
                    f"⏰ منذ: `{data['time']}`",
                    delete_after=10
                )
            except:
                pass

    prot = protection_config.get(guild_id, {})
    
    if prot.get("anti_links") or prot.get("links"):
        if re.findall(r"https?://\S+", content):
            if not has_mod_permission(message.author):
                try:
                    await message.delete()
                    await message.author.timeout(timedelta(minutes=2), reason="إرسال رابط ممنوع")
                    await send_log(message.guild, "🔗 رابط ممنوع", f"العضو: {message.author.mention}", discord.Color.red())
                except:
                    pass
                return

    if prot.get("anti_invite") or prot.get("invites"):
        if "discord.gg/" in content or "discord.com/invite/" in content:
            if not has_mod_permission(message.author):
                try:
                    await message.delete()
                    await message.author.timeout(timedelta(minutes=5), reason="إرسال دعوة ديسكورد")
                    await send_log(message.guild, "🚫 دعوة سيرفر ممنوعة", f"العضو: {message.author.mention}", discord.Color.dark_red())
                except:
                    pass
                return

    uid = str(message.author.id)
    if guild_id not in xp_data:
        xp_data[guild_id] = {}
    if uid not in xp_data[guild_id]:
        xp_data[guild_id][uid] = {"xp": 0, "level": 1}
    
    xp_data[guild_id][uid]["xp"] += random.randint(5, 15)
    current_xp = xp_data[guild_id][uid]["xp"]
    current_level = xp_data[guild_id][uid]["level"]
    
    if current_xp >= current_level * 100:
        xp_data[guild_id][uid]["level"] += 1
        await message.channel.send(f"🎉 مبروك {message.author.mention} وصلت للمستوى `{current_level + 1}`!")
    save_json(XP_FILE, xp_data)

    user_id = message.author.id
    now = time.time()
    if user_id not in user_message_timestamps:
        user_message_timestamps[user_id] = []
    user_message_timestamps[user_id] = [t for t in user_message_timestamps[user_id] if now - t < 5]
    user_message_timestamps[user_id].append(now)

    if len(user_message_timestamps[user_id]) >= 8:
        try:
            await message.author.timeout(timedelta(minutes=2), reason="Anti-Spam")
            await message.channel.send(f"⚠️ {message.author.mention} تم إعطاؤك تايم أوت بسبب السبام!", delete_after=5)
            user_message_timestamps[user_id] = []
        except:
            pass

    await bot.process_commands(message)

# ==================================
# نظام التقديمات المتكامل
# ==================================

def has_pending_application(guild_id, user_id):
    guild_apps = applications_data.get(str(guild_id), [])
    for app in guild_apps:
        if app.get("user_id") == user_id and app.get("status") == "pending":
            return True
    return False

async def send_application_result(member, accepted, reason, guild):
    if accepted:
        embed = discord.Embed(
            title="🎉 تم قبول طلبك",
            description=f"نبارك لك {member.mention}\n\nتم قبول طلب التقديم الخاص بك.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
    else:
        embed = discord.Embed(
            title="❌ تم رفض طلبك",
            description=f"نعتذر {member.mention}\n\nالسبب:\n{reason}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
    try:
        await member.send(embed=embed)
    except:
        pass

async def save_application_decision(guild, user, admin, status, reason):
    gid = str(guild.id)
    if gid not in application_decisions:
        application_decisions[gid] = []
    application_decisions[gid].append({
        "user": user.id if user else 0,
        "admin": admin.id,
        "status": status,
        "reason": reason,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    })
    save_application_decisions()

class AcceptButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(
            label="قبول",
            emoji="✅",
            style=discord.ButtonStyle.green
        )
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        await self.view_ref.process(interaction, True)


class RejectButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(
            label="رفض",
            emoji="❌",
            style=discord.ButtonStyle.red
        )
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            RejectReasonModal(
                self.view_ref.user_id,
                self.view_ref.app_id
            )
        )


class ApplicationDecisionView(discord.ui.View):
    def __init__(self, user_id, app_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.app_id = app_id

        self.add_item(AcceptButton(self))
        self.add_item(RejectButton(self))

    async def process(self, interaction, accepted, reason="بدون سبب"):
        gid = str(interaction.guild.id)
        if gid in applications_data:
            for app in applications_data[gid]:
                if app.get("id") == self.app_id:
                    app["status"] = "accepted" if accepted else "rejected"
                    break
            save_applications()

        member = interaction.guild.get_member(self.user_id)
        if accepted:
            role_id = application_config.get(gid, {}).get("accepted_role")
            if role_id and member:
                role = interaction.guild.get_role(role_id)
                if role:
                    try:
                        await member.add_roles(role)
                    except:
                        pass

        await save_application_decision(
            interaction.guild,
            member,
            interaction.user,
            "accepted" if accepted else "rejected",
            reason
        )

        if member:
            await send_application_result(member, accepted, reason, interaction.guild)

        # تحديث رسالة التقديم
        try:
            message = interaction.message
            embed = message.embeds[0]

            if accepted:
                embed.title = "✅ تم قبول التقديم"
                embed.color = discord.Color.green()
                embed.add_field(
                    name="الحالة",
                    value=f"مقبول بواسطة {interaction.user.mention}",
                    inline=False
                )
            else:
                embed.title = "❌ تم رفض التقديم"
                embed.color = discord.Color.red()
                embed.add_field(
                    name="الحالة",
                    value=f"مرفوض بواسطة {interaction.user.mention}",
                    inline=False
                )

            await message.edit(embed=embed, view=None)

        except Exception as e:
            print("Embed Update Error:", e)

        try:
            await interaction.response.send_message("✅ تم تنفيذ القرار", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send("✅ تم تنفيذ القرار", ephemeral=True)

class RejectReasonModal(discord.ui.Modal, title="سبب رفض التقديم"):
    def __init__(self, user_id, app_id):
        super().__init__()
        self.user_id = user_id
        self.app_id = app_id
        self.reason_input = discord.ui.TextInput(
            label="سبب الرفض",
            placeholder="اكتب سبب الرفض هنا...",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in applications_data:
            for app in applications_data[gid]:
                if app.get("id") == self.app_id:
                    app["status"] = "rejected"
                    app["reject_reason"] = self.reason_input.value
                    break
            save_applications()

        member = interaction.guild.get_member(self.user_id)
        await save_application_decision(
            interaction.guild,
            member,
            interaction.user,
            "rejected",
            self.reason_input.value
        )

        if member:
            await send_application_result(member, False, self.reason_input.value, interaction.guild)

        # تحديث رسالة التقديم عند الرفض بالموعد
        try:
            message = interaction.message
            embed = message.embeds[0]
            embed.title = "❌ تم رفض التقديم"
            embed.color = discord.Color.red()
            embed.add_field(
                name="الحالة",
                value=f"مرفوض بواسطة {interaction.user.mention}",
                inline=False
            )
            embed.add_field(
                name="السبب",
                value=self.reason_input.value,
                inline=False
            )
            await message.edit(embed=embed, view=None)
        except Exception as e:
            print("Embed Update Error:", e)

        await interaction.response.send_message("❌ تم رفض الطلب وإرسال السبب للعضو", ephemeral=True)

class DynamicApplicationModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"تقديم {app_type}")
        self.guild_id = guild_id
        self.app_type = app_type
        questions = application_questions.get(str(guild_id), ["اسمك", "عمرك", "لماذا تريد الانضمام؟"])
        for question in questions[:5]:
            self.add_item(
                discord.ui.TextInput(
                    label=question[:45],
                    required=True,
                    style=discord.TextStyle.paragraph
                )
            )

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(self.guild_id)
        if gid not in applications_data:
            applications_data[gid] = []

        answers = [item.value for item in self.children]
        app_id = random.randint(100000, 999999)

        applications_data[gid].append({
            "id": app_id,
            "user_id": interaction.user.id,
            "type": self.app_type,
            "answers": answers,
            "status": "pending"
        })

        if gid not in application_cooldowns:
            application_cooldowns[gid] = {}
        application_cooldowns[gid][str(interaction.user.id)] = time.time()

        save_applications()
        save_application_cooldowns()

        config = application_config.get(gid, {})
        result_channel_id = config.get("results") or config.get("results_channel")
        if result_channel_id:
            channel = interaction.guild.get_channel(result_channel_id)
            if channel:
                embed = discord.Embed(
                    title="📩 تقديم جديد",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="العضو", value=interaction.user.mention, inline=False)
                embed.add_field(name="النوع", value=self.app_type, inline=True)
                embed.add_field(name="رقم التقديم", value=str(app_id), inline=True)
                for i, answer in enumerate(answers):
                    embed.add_field(name=f"السؤال {i+1}", value=answer, inline=False)

                view = ApplicationDecisionView(interaction.user.id, app_id)
                msg = await channel.send(embed=embed, view=view)
                
                persistent_panels.append({
                    "type": "application_decision",
                    "guild_id": interaction.guild.id,
                    "channel_id": channel.id,
                    "message_id": msg.id,
                    "user_id": interaction.user.id,
                    "app_id": app_id
                })
                save_persistent()

        await interaction.response.send_message("✅ تم إرسال التقديم بنجاح", ephemeral=True)

class ApplicationTypeSelect(discord.ui.Select):
    def __init__(self, guild_id):
        options = []
        types = application_types.get(str(guild_id), [])
        if not types:
            options.append(discord.SelectOption(label="تقديم عام", description="التقديم الافتراضي بالسيرفر"))
        else:
            for item in types:
                if item.get("enabled", True):
                    options.append(discord.SelectOption(label=item["name"], description=item.get("description", "بدون وصف")))
        super().__init__(placeholder="اختر نوع التقديم", options=options)
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        if has_pending_application(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("❌ لديك تقديم قيد المراجعة بالفعل", ephemeral=True)
            return
        await interaction.response.send_modal(DynamicApplicationModal(self.guild_id, self.values[0]))

class ApplicationTypeSelectView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.add_item(ApplicationTypeSelect(guild_id))

class ApplicationButtonView(discord.ui.View):
    def __init__(self, guild_id, button_text, button_emoji):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        
        btn = discord.ui.Button(
            label=button_text,
            emoji=button_emoji,
            style=discord.ButtonStyle.green,
            custom_id=f"open_application_btn_{guild_id}"
        )
        btn.callback = self.button_callback
        self.add_item(btn)

    async def button_callback(self, interaction: discord.Interaction):
        types = application_types.get(str(self.guild_id), [])
        if len(types) > 1:
            await interaction.response.send_message("اختر نوع التقديم المناسب:", view=ApplicationTypeSelectView(self.guild_id), ephemeral=True)
        else:
            app_type = types[0]["name"] if types else "تقديم عام"
            if has_pending_application(interaction.guild.id, interaction.user.id):
                await interaction.response.send_message("❌ لديك تقديم قيد المراجعة بالفعل", ephemeral=True)
                return
            await interaction.response.send_modal(DynamicApplicationModal(self.guild_id, app_type))

@bot.tree.command(name="application-setup", description="إنشاء بانل التقديم")
@app_commands.checks.has_permissions(administrator=True)
async def application_setup(
    interaction: discord.Interaction,
    panel_channel: discord.TextChannel,
    results_channel: discord.TextChannel,
    description: str,
    button_text: str = "تقديم",
    button_emoji: str = "📝",
    image: str = None
):
    guild_id = str(interaction.guild.id)
    application_config[guild_id] = {
        "panel_channel": panel_channel.id,
        "results": results_channel.id,
        "description": description,
        "button_text": button_text,
        "emoji": button_emoji,
        "image": image,
        "enabled": True
    }
    save_application_config()

    embed = discord.Embed(title="📋 التقديمات", description=description, color=discord.Color.blurple())
    if image:
        embed.set_image(url=image)

    view = ApplicationButtonView(interaction.guild.id, button_text, button_emoji)
    msg = await panel_channel.send(embed=embed, view=view)

    persistent_panels.append({
        "type": "application",
        "guild_id": interaction.guild.id,
        "channel_id": panel_channel.id,
        "message_id": msg.id,
        "button_text": button_text,
        "button_emoji": button_emoji
    })
    save_persistent()

    await interaction.response.send_message("✅ تم إنشاء بانل التقديم بنجاح مع زر مخصص", ephemeral=True)

@bot.tree.command(name="application-role", description="تحديد الرتبة التي تعطى عند القبول")
@app_commands.checks.has_permissions(administrator=True)
async def application_role(interaction: discord.Interaction, role: discord.Role):
    guild_id = str(interaction.guild.id)
    if guild_id not in application_config:
        application_config[guild_id] = {}
    application_config[guild_id]["accepted_role"] = role.id
    save_application_config()
    await interaction.response.send_message(f"✅ سيتم إعطاء {role.mention} عند القبول", ephemeral=True)

@bot.tree.command(name="applications-list", description="عرض آخر التقديمات")
@app_commands.checks.has_permissions(administrator=True)
async def applications_list(interaction: discord.Interaction):
    apps = applications_data.get(str(interaction.guild.id), [])
    if not apps:
        await interaction.response.send_message("لا يوجد تقديمات", ephemeral=True)
        return
    text = ""
    for app in apps[-10:]:
        text += f"#{app.get('id')} <@{app.get('user_id')}> - {app.get('status')}\n"
    embed = discord.Embed(title="📋 آخر التقديمات", description=text, color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="application-info", description="عرض معلومات تقديم محدد")
async def application_info(interaction: discord.Interaction, number: int):
    apps = applications_data.get(str(interaction.guild.id), [])
    found = next((app for app in apps if app.get("id") == number), None)
    if not found:
        await interaction.response.send_message("❌ لم يتم العثور على التقديم", ephemeral=True)
        return
    embed = discord.Embed(title=f"📋 تقديم رقم {number}", color=discord.Color.blue())
    embed.add_field(name="العضو", value=f"<@{found.get('user_id')}>", inline=False)
    embed.add_field(name="الحالة", value=found.get("status"), inline=False)
    for i, ans in enumerate(found.get("answers", [])):
        embed.add_field(name=f"الإجابة {i+1}", value=ans, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================================
# أوامر الإدارة والعقوبات الأخرى
# ==================================

@bot.tree.command(name="anti-setup", description="تشغيل أنظمة الحماية")
@app_commands.checks.has_permissions(administrator=True)
async def anti_setup(interaction: discord.Interaction):
    anti_config[str(interaction.guild.id)] = {
        "mention": True,
        "massmention": True,
        "badwords": True
    }
    save_json(ANTI_CONFIG_FILE, anti_config)
    await interaction.response.send_message("✅ تم تشغيل أنظمة الحماية", ephemeral=True)

@bot.tree.command(name="announce", description="إرسال إعلان Embed")
@app_commands.describe(channel="الروم", title="العنوان", text="النص")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, text: str):
    embed = discord.Embed(title=title, description=text, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_footer(text=interaction.guild.name)
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ تم إرسال الإعلان", ephemeral=True)

@bot.tree.command(name="say", description="جعل البوت يرسل رسالة")
@app_commands.describe(text="الرسالة")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, text: str):
    await interaction.channel.send(text)
    await interaction.response.send_message("✅ تم الإرسال", ephemeral=True)

@bot.tree.command(name="set-welcome", description="تحديد روم وإعداد رسالة الترحيب")
@app_commands.describe(channel="روم الترحيب", message="رسالة الترحيب")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط", ephemeral=True)
        return
    welcome_config[str(interaction.guild.id)] = {"channel_id": channel.id, "message": message}
    save_json(WELCOME_CONFIG_FILE, welcome_config)
    await interaction.response.send_message(f"✅ تم ضبط نظام الترحيب في {channel.mention}!", ephemeral=True)

@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.describe(member="العضو", reason="السبب")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings = load_json(WARNINGS_FILE)
    gid, uid = str(interaction.guild.id), str(member.id)
    if gid not in warnings: warnings[gid] = {}
    if uid not in warnings[gid]: warnings[gid][uid] = []
    
    warnings[gid][uid].append({"reason": reason, "moderator": interaction.user.name, "date": datetime.utcnow().strftime("%Y/%m/%d %H:%M")})
    save_json(WARNINGS_FILE, warnings)
    await interaction.response.send_message(f"✅ تم تحذير العضو {member.mention}.", ephemeral=True)
    await send_log(interaction.guild, "⚠️ تحذير عضو", f"العضو: {member.mention}\nالسبب: `{reason}`", discord.Color.orange())

@bot.tree.command(name="timeout", description="إعطاء تايم أوت لعضو")
@app_commands.describe(member="العضو", duration="المدة بالدقائق", reason="السبب")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "لا يوجد سبب"):
    try:
        await member.timeout(timedelta(minutes=duration), reason=reason)
        await interaction.response.send_message(f"✅ تم إعطاء تايم أوت لـ {member.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="طرد عضو")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ تم طرد {member.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)

@bot.tree.command(name="ban", description="حظر عضو")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"✅ تم حظر {member.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)

@bot.tree.command(name="clear", description="مسح الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم حذف {len(deleted)} رسالة.", ephemeral=True)

@bot.tree.command(name="lock", description="قفل الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل الروم بنجاح.")

@bot.tree.command(name="unlock", description="فتح الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح الروم بنجاح.")

@bot.tree.command(name="afk", description="تفعيل وضع AFK")
@app_commands.describe(reason="سبب الغياب")
async def afk(interaction: discord.Interaction, reason: str = "بدون سبب"):
    afk_users[str(interaction.user.id)] = {
        "reason": reason,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json(AFK_FILE, afk_users)
    await interaction.response.send_message(f"💤 تم تفعيل AFK\nالسبب: `{reason}`", ephemeral=True)

@bot.tree.command(name="unafk", description="إلغاء وضع AFK")
async def unafk(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in afk_users:
        del afk_users[user_id]
        save_json(AFK_FILE, afk_users)
        await interaction.response.send_message("✅ تم إلغاء وضع AFK", ephemeral=True)
    else:
        await interaction.response.send_message("❌ أنت لست AFK", ephemeral=True)

@bot.tree.command(name="suggest", description="إرسال اقتراح للسيرفر")
async def suggest(interaction: discord.Interaction, suggestion: str):
    embed = discord.Embed(title="💡 اقتراح جديد", description=suggestion, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"بواسطة {interaction.user}")
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    await interaction.response.send_message("✅ تم إرسال اقتراحك.", ephemeral=True)

@bot.tree.command(name="rank", description="عرض مستوى العضو")
async def rank(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = xp_data.get(str(interaction.guild.id), {}).get(str(member.id), {"xp": 0, "level": 1})
    embed = discord.Embed(title="🏆 المستوى", description=f"👤 العضو: {member.mention}\n⭐ المستوى: `{data['level']}`\n✨ XP: `{data['xp']}`", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="bot-status", description="عرض حالة البوت")
async def bot_status(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🤖 حالة البوت", color=discord.Color.green())
    embed.add_field(name="🟢 الحالة", value="Online")
    embed.add_field(name="📡 Ping", value=f"{latency}ms")
    embed.add_field(name="🌐 السيرفرات", value=len(bot.guilds))
    await interaction.response.send_message(embed=embed)

# ==================================
# نظام Reaction Roles (Slash Command)
# ==================================

class ReactionRoleView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id
        button = discord.ui.Button(
            label="🎭 أخذ / إزالة الرتبة",
            style=discord.ButtonStyle.primary,
            custom_id=f"reaction_role_btn_{role_id}"
        )
        button.callback = self.role_button
        self.add_item(button)

    async def role_button(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ الرتبة غير موجودة في السيرفر", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ تم إزالة رتبة {role.mention}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ تم إعطاؤك رتبة {role.mention}", ephemeral=True)

@bot.tree.command(name="reaction-role", description="إنشاء زر للحصول على رتبة")
@app_commands.describe(role="الرتبة", channel="الروم", text="النص الذي سيظهر")
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role(interaction: discord.Interaction, role: discord.Role, channel: discord.TextChannel, text: str):
    embed = discord.Embed(title="🎭 رتبة تلقائية", description=text, color=discord.Color.blue())
    embed.add_field(name="اضغط الزر للحصول على:", value=role.mention)

    msg = await channel.send(embed=embed, view=ReactionRoleView(role.id))
    reaction_roles[str(msg.id)] = {"role_id": role.id, "channel_id": channel.id, "guild_id": interaction.guild.id}
    save_json(REACTION_ROLES_FILE, reaction_roles)

    persistent_panels.append({
        "type": "reaction_role",
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": msg.id,
        "role_id": role.id
    })
    save_persistent()

    bot.add_view(ReactionRoleView(role.id), message_id=msg.id)

    await interaction.response.send_message("✅ تم إنشاء رتبة الزر بنجاح", ephemeral=True)

# ==================================
# أحداث التشغيل والتجهيز (On Ready)
# ==================================

@bot.event
async def on_ready():
    print("="*40)
    print(f"🤖 Bot Online : {bot.user}")
    print(f"🌐 Servers : {len(bot.guilds)}")
    print("="*40)

    for panel in persistent_panels:
        try:
            ptype = panel.get("type")
            msg_id = panel.get("message_id")

            if ptype == "application":
                bot.add_view(
                    ApplicationButtonView(
                        panel["guild_id"],
                        panel.get("button_text", "تقديم"),
                        panel.get("button_emoji", "📝")
                    ),
                    message_id=msg_id
                )
            elif ptype == "application_decision":
                bot.add_view(
                    ApplicationDecisionView(
                        panel["user_id"],
                        panel["app_id"]
                    ),
                    message_id=msg_id
                )
            elif ptype == "reaction_role":
                bot.add_view(
                    ReactionRoleView(
                        panel["role_id"]
                    ),
                    message_id=msg_id
                )
        except Exception as e:
            print(f"❌ Failed to load persistent view: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands globally")
    except Exception as e:
        print(f"❌ Sync Error: {e}")
        save_error(e)

# ==================================
# تشغيل البوت
# ==================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token not found! Please set DISCORD_TOKEN environment variable.")
