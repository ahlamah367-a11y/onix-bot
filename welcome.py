import discord
from discord.ext import commands
from discord import app_commands

import json
import os
from datetime import datetime, timedelta
import asyncio
import random
import time

# ==================================
# إعداد البوت
# ==================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

GUILD_ID = 1532326696714240062

# ==================================
# إعدادات ونظام الترحيب (Welcome System)
# ==================================

WELCOME_CONFIG_FILE = "welcome_config.json"

def load_welcome_config():
    if os.path.exists(WELCOME_CONFIG_FILE):
        with open(WELCOME_CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_welcome_config():
    with open(WELCOME_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(welcome_config, f, indent=4, ensure_ascii=False)

welcome_config = load_welcome_config()


@bot.tree.command(name="set-welcome", description="تحديد روم وإعداد رسالة الترحيب")
@app_commands.describe(channel="روم الترحيب", message="رسالة الترحيب (استخدم {user} لعمل إشارة للأعضاء)")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط", ephemeral=True)
        return

    welcome_config[str(interaction.guild.id)] = {
        "channel_id": channel.id,
        "message": message
    }
    save_welcome_config()

    await interaction.response.send_message(
        f"✅ تم ضبط نظام الترحيب بنجاح في الروم {channel.mention}!",
        ephemeral=True
    )


@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    
    # 1. نظام الترحيب
    if guild_id in welcome_config:
        data = welcome_config[guild_id]
        channel_id = data.get("channel_id")
        raw_message = data.get("message", "أهلاً بك {user} في السيرفر!")
        channel = member.guild.get_channel(channel_id)
        if channel:
            formatted_message = raw_message.replace("{user}", member.mention)
            embed = discord.Embed(
                title="👋 عضو جديد!",
                description=formatted_message,
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            embed.set_footer(text=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
            try:
                await channel.send(content=member.mention, embed=embed)
            except:
                pass

    # 2. نظام الرول التلقائي (Autorole)
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            try:
                cfg = json.load(f)
                role_id = cfg.get(str(member.guild.id), {}).get("autorole_id")
                if role_id:
                    role = member.guild.get_role(role_id)
                    if role:
                        await member.add_roles(role)
            except:
                pass

    # 3. سجلات دخول عضو
    await send_log(member.guild, "📥 دخول عضو", f"العضو: {member.mention} (`{member.id}`)", discord.Color.green())


# ==================================
# نظام السجلات (Logs System)
# ==================================

LOGS_CONFIG_FILE = "logs_config.json"

def load_logs_config():
    if os.path.exists(LOGS_CONFIG_FILE):
        with open(LOGS_CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_logs_config(data):
    with open(LOGS_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def send_log(guild, title, description, color):
    config = load_logs_config()
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
    config = load_logs_config()
    config[str(interaction.guild.id)] = channel.id
    save_logs_config(config)
    await interaction.response.send_message(f"✅ تم ضبط روم السجلات بنجاح في {channel.mention}", ephemeral=True)


@bot.event
async def on_member_remove(member):
    await send_log(member.guild, "📤 خروج عضو", f"العضو: {member.mention} (`{member.id}`)", discord.Color.dark_red())


# ==================================
# إعدادات رتبة الإدارة السريعة
# ==================================

MOD_CONFIG_FILE = "mod_roles.json"

def load_mod_roles():
    if os.path.exists(MOD_CONFIG_FILE):
        with open(MOD_CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_mod_roles(data):
    with open(MOD_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

mod_roles = load_mod_roles()

def has_mod_permission(member):
    if member.guild_permissions.administrator:
        return True

    role_id = mod_roles.get(str(member.guild.id))

    if role_id:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            return True

    return False


@bot.tree.command(name="set-mod-role", description="تحديد رتبة الإدارة للأوامر السريعة")
@app_commands.describe(role="الرتبة التي تستطيع استعمال أوامر الإدارة")
@app_commands.checks.has_permissions(administrator=True)
async def set_mod_role(interaction: discord.Interaction, role: discord.Role):
    mod_roles[str(interaction.guild.id)] = role.id
    save_mod_roles(mod_roles)

    await interaction.response.send_message(
        f"✅ تم تحديد رتبة الإدارة: {role.mention}",
        ephemeral=True
    )


# ==================================
# قاعدة البيانات الخاصة بالقيف أوي
# ==================================

GIVEAWAYS_FILE = "giveaways_database.json"
ENDED_GIVEAWAYS_FILE = "ended_giveaways_database.json"

giveaways = {}
ended_giveaways = {}

def load_giveaways():
    if os.path.exists(GIVEAWAYS_FILE):
        with open(GIVEAWAYS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def load_ended_giveaways():
    if os.path.exists(ENDED_GIVEAWAYS_FILE):
        with open(ENDED_GIVEAWAYS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_giveaways_data():
    data_to_save = {}
    for gid, gdata in giveaways.items():
        data_to_save[str(gid)] = {
            "id": gdata["id"],
            "prize": gdata["prize"],
            "winners_count": gdata["winners_count"],
            "image_url": gdata["image_url"],
            "participants": gdata["participants"],
            "channel_id": gdata["message"].channel.id,
            "message_id": gdata["message"].id,
            "end_time": gdata["end_time"].isoformat(),
            "creator": str(gdata.get("creator", "Unknown"))
        }
    with open(GIVEAWAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=4, ensure_ascii=False)

def save_ended_giveaways_data():
    data_to_save = {}
    for gid, gdata in ended_giveaways.items():
        data_to_save[str(gid)] = {
            "id": gdata["id"],
            "prize": gdata["prize"],
            "winners_count": gdata["winners_count"],
            "image_url": gdata["image_url"],
            "participants": gdata["participants"],
            "channel_id": gdata["channel_id"],
            "message_id": gdata["message_id"],
            "end_time": gdata["end_time"],
            "winners": gdata.get("winners", "لا يوجد"),
            "creator": str(gdata.get("creator", "Unknown"))
        }
    with open(ENDED_GIVEAWAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=4, ensure_ascii=False)

ended_giveaways = load_ended_giveaways()


# ==================================
# نظام القيف أوي المطور
# ==================================

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="🎉 مشاركة", style=discord.ButtonStyle.success, custom_id="giveaway_join_secure")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            await interaction.response.send_message("❌ لا يُسمح للبوتات بالمشاركة!", ephemeral=True)
            return

        data = giveaways.get(self.giveaway_id)
        if not data:
            await interaction.response.send_message("❌ انتهى القيف أوي.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in data["participants"]:
            data["participants"].remove(user_id)
            await interaction.response.send_message("❌ تم إلغاء مشاركتك.", ephemeral=True)
        else:
            data["participants"].append(user_id)
            await interaction.response.send_message("✅ تم تسجيل مشاركتك!", ephemeral=True)

        save_giveaways_data()
        await update_giveaway_message(data)


async def update_giveaway_message(data):
    remaining = data["end_time"] - datetime.utcnow()
    if remaining.total_seconds() < 0:
        return

    seconds = int(remaining.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"

    embed = discord.Embed(
        title="🎉 قيف أوي جديد | GIVEAWAY",
        description=f"> 🎁 **الجائزة:** `{data['prize']}`\n> 🏆 **عدد الفائزين:** `{data['winners_count']}`\n> 👥 **المشاركون:** `{len(data['participants'])}`\n> ⏳ **متبقي:** `{time_str}`",
        color=discord.Color.gold()
    )
    if data["image_url"]:
        embed.set_image(url=data["image_url"])

    try:
        await data["message"].edit(embed=embed, view=GiveawayView(data["id"]))
    except:
        pass


async def giveaway_timer(data):
    while datetime.utcnow() < data["end_time"]:
        await update_giveaway_message(data)
        await asyncio.sleep(5)

    await end_giveaway(data["id"])


async def end_giveaway(giveaway_id, is_reroll=False):
    data = giveaways.get(giveaway_id)
    if not data:
        return

    participants = data["participants"]
    winners_count = data["winners_count"]

    if len(participants) == 0:
        winners_text = "لا يوجد مشاركين"
    else:
        actual_winners_count = min(winners_count, len(participants))
        chosen_winners = random.sample(participants, actual_winners_count)
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
        winners_list = []
        for index, winner_id in enumerate(chosen_winners):
            medal = medals[index] if index < len(medals) else "🏅"
            winners_list.append(f"{medal} <@{winner_id}>")
        winners_text = "\n".join(winners_list)

    embed = discord.Embed(
        title="🎉 انتهى القيف أوي" if not is_reroll else "🔄 إعادة اختيار الفائزين",
        description=f"> 🎁 الجائزة: `{data['prize']}`\n> 🏆 الفائزين:\n{winners_text}\n> 👥 عدد المشاركين: `{len(participants)}`",
        color=discord.Color.red()
    )
    if data["image_url"]:
        embed.set_image(url=data["image_url"])

    try:
        await data["message"].edit(embed=embed, view=None)
    except:
        pass

    ended_giveaways[str(giveaway_id)] = {
        "id": data["id"],
        "prize": data["prize"],
        "winners_count": data["winners_count"],
        "image_url": data["image_url"],
        "participants": data["participants"],
        "channel_id": data["message"].channel.id,
        "message_id": data["message"].id,
        "end_time": data["end_time"].isoformat(),
        "winners": winners_text,
        "creator": str(data.get("creator", "Unknown"))
    }
    save_ended_giveaways_data()

    if giveaway_id in giveaways:
        del giveaways[giveaway_id]
        save_giveaways_data()


@bot.tree.command(name="giveaway", description="إنشاء قيف أوي مطور")
@app_commands.describe(prize="الجائزة", duration_minutes="المدة بالدقائق", winners_count="عدد الفائزين", channel="الروم", image_url="رابط صورة الجائزة (اختياري)")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, prize: str, duration_minutes: int, winners_count: int, channel: discord.TextChannel, image_url: str = None):
    if duration_minutes < 1:
        await interaction.response.send_message("❌ الوقت يجب أن يكون أكثر من دقيقة واحدة!", ephemeral=True)
        return

    giveaway_id = random.randint(100000, 999999)
    embed = discord.Embed(
        title="🎉 قيف أوي جديد",
        description=f"> 🎁 الجائزة: `{prize}`\n> 🏆 عدد الفائزين: `{winners_count}`\n> 👥 المشاركون: `0`\n> ⏳ المدة: `{duration_minutes} دقيقة`",
        color=discord.Color.gold()
    )
    if image_url:
        embed.set_image(url=image_url)

    msg = await channel.send(content="@everyone", embed=embed, view=GiveawayView(giveaway_id))
    
    data = {
        "id": giveaway_id,
        "prize": prize,
        "winners_count": winners_count,
        "image_url": image_url,
        "participants": [],
        "message": msg,
        "end_time": datetime.utcnow() + timedelta(minutes=duration_minutes),
        "creator": interaction.user.name
    }

    giveaways[giveaway_id] = data
    save_giveaways_data()
    bot.loop.create_task(giveaway_timer(data))

    await interaction.response.send_message("✅ تم إنشاء القيف أوي بنجاح.", ephemeral=True)


@bot.tree.command(name="giveaway-cancel", description="إلغاء قيف أوي نشط")
@app_commands.describe(giveaway_id="معرف القيف أوي")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway_cancel(interaction: discord.Interaction, giveaway_id: int):
    data = giveaways.get(giveaway_id)
    if not data:
        await interaction.response.send_message("❌ لم يتم العثور على قيف أوي نشط بهذا المعرف.", ephemeral=True)
        return

    try:
        embed = discord.Embed(title="❌ تم إلغاء القيف أوي", description=f"الجائزة: `{data['prize']}`", color=discord.Color.dark_grey())
        await data["message"].edit(embed=embed, view=None)
    except:
        pass

    if giveaway_id in giveaways:
        del giveaways[giveaway_id]
        save_giveaways_data()

    await interaction.response.send_message("✅ تم إلغاء القيف أوي بنجاح.", ephemeral=True)


@bot.tree.command(name="reroll", description="إعادة اختيار فائزين جدد للقيف أوي")
@app_commands.describe(giveaway_id="معرف القيف أوي (رقم الـ ID)", winners_count="عدد الفائزين الجدد")
@app_commands.checks.has_permissions(administrator=True)
async def reroll(interaction: discord.Interaction, giveaway_id: int, winners_count: int = 1):
    data = giveaways.get(giveaway_id)
    if not data:
        saved_ended = load_ended_giveaways()
        if str(giveaway_id) in saved_ended:
            data = saved_ended[str(giveaway_id)]
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        else:
            await interaction.response.send_message("❌ لم يتم العثور على القيف أوي بهذا المعرف.", ephemeral=True)
            return

    participants = data["participants"]
    if not participants:
        await interaction.response.send_message("❌ لا يوجد مشاركين في هذا القيف أوي لإعادة الاختيار.", ephemeral=True)
        return

    actual_winners_count = min(winners_count, len(participants))
    chosen_winners = random.sample(participants, actual_winners_count)
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    winners_list = []
    for index, winner_id in enumerate(chosen_winners):
        medal = medals[index] if index < len(medals) else "🏅"
        winners_list.append(f"{medal} <@{winner_id}>")
    winners_text = "\n".join(winners_list)

    embed = discord.Embed(
        title="🔄 إعادة اختيار الفائزين (Reroll)",
        description=f"> 🎁 الجائزة: `{data['prize']}`\n> 🏆 الفائزين الجدد:\n{winners_text}",
        color=discord.Color.purple()
    )
    if data.get("image_url"):
        embed.set_image(url=data["image_url"])

    channel_id = data["channel_id"] if isinstance(data["channel_id"], int) else data["message"].channel.id
    channel = interaction.guild.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)

    await interaction.response.send_message("✅ تم إعادة اختيار الفائزين بنجاح!", ephemeral=True)


@bot.tree.command(name="giveaway-info", description="معلومات القيف أوي")
@app_commands.describe(giveaway_id="معرف القيف أوي")
async def giveaway_info(interaction: discord.Interaction, giveaway_id: int):
    data = giveaways.get(giveaway_id)
    if not data:
        saved_ended = load_ended_giveaways()
        if str(giveaway_id) in saved_ended:
            data = saved_ended[str(giveaway_id)]
            data["end_time"] = datetime.fromisoformat(data["end_time"])
            time_text = "انتهى بالفعل"
        else:
            await interaction.response.send_message("❌ القيف أوي غير موجود.", ephemeral=True)
            return
    else:
        remaining = data["end_time"] - datetime.utcnow()
        if remaining.total_seconds() < 0:
            time_text = "انتهى الوقت"
        else:
            seconds = int(remaining.total_seconds())
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            time_text = f"{hours} ساعة و {minutes} دقيقة"

    embed = discord.Embed(
        title=f"📋 Giveaway Logs & Info #{data['id']}",
        description=f"> 👤 **المنشئ:** `{data.get('creator', 'غير معروف')}`\n> 🎁 **الجائزة:** `{data['prize']}`\n> 🏆 **عدد الفائزين المطلوبة:** `{data['winners_count']}`\n> 👥 **عدد المشاركين:** `{len(data['participants'])}`\n> ⏳ **الحالة/الوقت:** `{time_text}`",
        color=discord.Color.blue()
    )
    if data.get("image_url"):
        embed.set_image(url=data["image_url"])

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================================
# نظام العقوبات (Warnings, Timeout, Kick, Ban)
# ==================================

WARNINGS_FILE = "warnings.json"

def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_warnings(data):
    with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.describe(member="العضو المراد تحذيره", reason="السبب")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings = load_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    if guild_id not in warnings:
        warnings[guild_id] = {}
    if user_id not in warnings[guild_id]:
        warnings[guild_id][user_id] = []

    warn_data = {
        "reason": reason,
        "moderator": interaction.user.name,
        "date": datetime.utcnow().strftime("%Y/%m/%d %H:%M")
    }
    warnings[guild_id][user_id].append(warn_data)
    save_warnings(warnings)

    await interaction.response.send_message(f"✅ تم تحذير العضو {member.mention} بنجاح.", ephemeral=True)
    await send_log(interaction.guild, "⚠️ تحذير عضو", f"العضو: {member.mention}\nالسبب: `{reason}`\nالمشرف: {interaction.user.mention}", discord.Color.orange())


@bot.tree.command(name="warnings", description="عرض تحذيرات عضو")
@app_commands.describe(member="العضو")
async def warnings_cmd(interaction: discord.Interaction, member: discord.Member):
    warnings = load_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    user_warnings = warnings.get(guild_id, {}).get(user_id, [])
    if not user_warnings:
        await interaction.response.send_message(f"✅ العضو {member.mention} ليس لديه أي تحذيرات.", ephemeral=True)
        return

    desc = f"📋 **سجل التحذيرات لـ {member.mention}**\n\n"
    for idx, w in enumerate(user_warnings, 1):
        desc += f"**{idx}-** `{w['reason']}`\n> المشرف: `{w['moderator']}` | التاريخ: `{w['date']}`\n\n"

    embed = discord.Embed(title="سجل التحذيرات", description=desc, color=discord.Color.yellow())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clear-warnings", description="مسح تحذيرات عضو")
@app_commands.describe(member="العضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    warnings = load_warnings()
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    if guild_id in warnings and user_id in warnings[guild_id]:
        del warnings[guild_id][user_id]
        save_warnings(warnings)

    await interaction.response.send_message(f"✅ تم مسح تحذيرات العضو {member.mention}.", ephemeral=True)


@bot.tree.command(name="timeout", description="إعطاء تايم أوت لعضو")
@app_commands.describe(member="العضو", duration="المدة (بالدقائق)", reason="السبب")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "لا يوجد سبب"):
    delta = timedelta(minutes=duration)
    try:
        await member.timeout(delta, reason=reason)
        await interaction.response.send_message(f"✅ تم إسكات العضو {member.mention} لمدة {duration} دقائق.", ephemeral=True)
        await send_log(interaction.guild, "⏳ تايم أوت", f"العضو: {member.mention}\nالمدة: `{duration} دقيقة`\nالسبب: `{reason}`", discord.Color.gold())
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)


@bot.tree.command(name="untimeout", description="إزالة التايم أوت عن عضو")
@app_commands.describe(member="العضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.timeout(None)
        await interaction.response.send_message(f"✅ تم إزالة التايم عن {member.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)


@bot.tree.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.describe(member="العضو", reason="السبب")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ تم طرد العضو {member.mention}.", ephemeral=True)
        await send_log(interaction.guild, "👢 طرد عضو", f"العضو: {member.mention}\nالسبب: `{reason}`", discord.Color.red())
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)


@bot.tree.command(name="ban", description="حظر عضو من السيرفر")
@app_commands.describe(member="العضو", reason="السبب")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"✅ تم حظر العضو {member.mention}.", ephemeral=True)
        await send_log(interaction.guild, "🔨 تم حظر عضو", f"العضو: {member.mention}\nالسبب: `{reason}`\nالمشرف: {interaction.user.mention}", discord.Color.dark_red())
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)


@bot.tree.command(name="unban", description="فك الحظر عن عضو بواسطة الآيدي")
@app_commands.describe(user_id="آيدي العضو")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ تم فك الحظر عن العضو {user.name}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ أو الآيدي غير صحيح: {e}", ephemeral=True)


# ==================================
# أوامر الإدارة والرومات (Clear, Lock, Unlock, Slowmode)
# ==================================

@bot.tree.command(name="clear", description="مسح عدد من الرسائل")
@app_commands.describe(amount="عدد الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم حذف {len(deleted)} رسالة بنجاح.", ephemeral=True)


@bot.tree.command(name="lock", description="قفل الروم الحالي")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل الروم بنجاح.")
    await send_log(interaction.guild, "🔒 قفل روم", f"الروم: {interaction.channel.mention}", discord.Color.dark_grey())


@bot.tree.command(name="unlock", description="فتح الروم الحالي")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح الروم بنجاح.")
    await send_log(interaction.guild, "🔓 فتح روم", f"الروم: {interaction.channel.mention}", discord.Color.light_grey())


@bot.tree.command(name="slowmode", description="تحديد سرعة الشات (Slowmode)")
@app_commands.describe(seconds="عدد الثواني")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"✅ تم ضبط Slowmode إلى {seconds} ثانية.", ephemeral=True)


# ==================================
# نظام Autorole
# ==================================

@bot.tree.command(name="autorole", description="تحديد الرول التلقائي للأعضاء الجدد")
@app_commands.describe(role="الرول")
@app_commands.checks.has_permissions(administrator=True)
async def autorole(interaction: discord.Interaction, role: discord.Role):
    cfg = {}
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            try:
                cfg = json.load(f)
            except:
                pass
    
    cfg[str(interaction.guild.id)] = {"autorole_id": role.id}
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

    await interaction.response.send_message(f"✅ تم ضبط الرول التلقائي إلى {role.mention}", ephemeral=True)


# ==================================
# نظام الأوامر المختصرة والنصية
# ==================================

CUSTOM_COMMANDS_FILE = "custom_commands.json"

def load_custom_commands():
    if os.path.exists(CUSTOM_COMMANDS_FILE):
        with open(CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_custom_commands():
    with open(CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(custom_commands, f, indent=4, ensure_ascii=False)

custom_commands = load_custom_commands()

COMMAND_LIST = [
    "lock",
    "unlock",
    "clear",
    "warn",
    "kick",
    "ban",
    "slowmode"
]


@bot.tree.command(name="add-command", description="إنشاء أمر مختصر مثل قفل أو مسح")
@app_commands.describe(
    name="الكلمة التي ستكتبها",
    command="الأمر الذي سيتم تنفيذه",
    channel="الروم (اختياري)"
)
@app_commands.choices(
    command=[
        app_commands.Choice(name="قفل", value="lock"),
        app_commands.Choice(name="فتح", value="unlock"),
        app_commands.Choice(name="مسح", value="clear"),
        app_commands.Choice(name="تحذير", value="warn"),
        app_commands.Choice(name="طرد", value="kick"),
        app_commands.Choice(name="بان", value="ban"),
        app_commands.Choice(name="Slowmode", value="slowmode")
    ]
)
@app_commands.checks.has_permissions(administrator=True)
async def add_command(
    interaction: discord.Interaction,
    name: str,
    command: str,
    channel: discord.TextChannel = None
):
    gid = str(interaction.guild.id)

    if gid not in custom_commands:
        custom_commands[gid] = {}

    custom_commands[gid][name] = {
        "command": command,
        "channel_id": channel.id if channel else None
    }

    save_custom_commands()

    await interaction.response.send_message(
        f"✅ تم إنشاء الأمر المختصر `{name}` للأمر `{command}`",
        ephemeral=True
    )


@bot.tree.command(name="delete-command", description="حذف أمر نصي")
@app_commands.describe(command="اسم الأمر المراد حذفه")
@app_commands.checks.has_permissions(administrator=True)
async def delete_command(
    interaction: discord.Interaction,
    command: str
):
    guild_id = str(interaction.guild.id)

    if guild_id not in custom_commands:
        await interaction.response.send_message(
            "❌ لا توجد أوامر.",
            ephemeral=True
        )
        return

    if command not in custom_commands[guild_id]:
        await interaction.response.send_message(
            "❌ هذا الأمر غير موجود.",
            ephemeral=True
        )
        return

    del custom_commands[guild_id][command]
    save_custom_commands()

    await interaction.response.send_message(
        f"✅ تم حذف الأمر `{command}`.",
        ephemeral=True
    )


@bot.tree.command(name="edit-command", description="تعديل أمر نصي")
@app_commands.describe(
    command="اسم الأمر",
    new_action="الأمر الجديد",
    channel="الروم الجديد (اختياري)"
)
@app_commands.choices(new_action=[
    app_commands.Choice(name="قفل", value="lock"),
    app_commands.Choice(name="فتح", value="unlock"),
    app_commands.Choice(name="مسح", value="clear"),
    app_commands.Choice(name="تحذير", value="warn"),
    app_commands.Choice(name="طرد", value="kick"),
    app_commands.Choice(name="بان", value="ban"),
    app_commands.Choice(name="Slowmode", value="slowmode")
])
@app_commands.checks.has_permissions(administrator=True)
async def edit_command(
    interaction: discord.Interaction,
    command: str,
    new_action: str,
    channel: discord.TextChannel = None
):
    guild_id = str(interaction.guild.id)

    if command not in custom_commands.get(guild_id, {}):
        await interaction.response.send_message(
            "❌ الأمر غير موجود.",
            ephemeral=True
        )
        return

    custom_commands[guild_id][command] = {
        "command": new_action,
        "channel_id": channel.id if channel else None
    }

    save_custom_commands()

    await interaction.response.send_message(
        f"✅ تم تعديل الأمر `{command}`.",
        ephemeral=True
    )


@bot.tree.command(name="commands-list", description="عرض الأوامر النصية المضافة")
async def commands_list(interaction: discord.Interaction):
    data = custom_commands.get(str(interaction.guild.id), {})

    if not data:
        await interaction.response.send_message(
            "❌ لا توجد أوامر مضافة",
            ephemeral=True
        )
        return

    text = ""

    for cmd, info in data.items():
        text += f"🔹 `{cmd}` → {info.get('command') or info.get('action')}\n"

    embed = discord.Embed(
        title="📋 الأوامر النصية",
        description=text,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================================
# نظام Anti-Spam التلقائي والأوامر المخصصة
# ==================================

user_message_timestamps = {}

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if has_mod_permission(message.author):

        args = message.content.split()
        command = args[0].lower() if args else ""

        # ======================
        # قفل
        # ======================
        if command == "قفل":
            channel = message.channel

            if len(args) > 1:
                try:
                    channel = message.guild.get_channel(int(args[1].replace("<#", "").replace(">", "")))
                except:
                    pass

            await channel.set_permissions(
                message.guild.default_role,
                send_messages=False
            )

            await message.reply(f"🔒 تم قفل {channel.mention}")
            return


        # ======================
        # فتح
        # ======================
        if command == "فتح":
            channel = message.channel

            if len(args) > 1:
                try:
                    channel = message.guild.get_channel(int(args[1].replace("<#", "").replace(">", "")))
                except:
                    pass

            await channel.set_permissions(
                message.guild.default_role,
                send_messages=True
            )

            await message.reply(f"🔓 تم فتح {channel.mention}")
            return


        # ======================
        # مسح
        # ======================
        if command == "مسح":

            if len(args) < 2:
                await message.reply("❌ مثال: مسح 50")
                return

            try:
                amount = int(args[1])

                deleted = await message.channel.purge(
                    limit=amount + 1
                )

                msg = await message.channel.send(
                    f"🧹 تم مسح {len(deleted)-1} رسالة"
                )

                await msg.delete(delay=5)

            except:
                await message.reply("❌ الرقم غير صحيح")

            return


        # ======================
        # Slowmode
        # ======================
        if command == "slowmode":

            if len(args) < 2:
                await message.reply("❌ مثال: slowmode 10")
                return

            try:
                seconds = int(args[1])

                await message.channel.edit(
                    slowmode_delay=seconds
                )

                await message.reply(
                    f"🐌 تم وضع Slowmode {seconds} ثانية"
                )

            except:
                await message.reply("❌ الرقم غير صحيح")

            return


        # ======================
        # تحذير
        # ======================
        if command in ["تحذير", "warn"]:

            if not message.mentions:
                await message.reply(
                    "❌ مثال: تحذير @العضو السبب"
                )
                return

            member = message.mentions[0]

            reason = " ".join(args[2:])

            if not reason:
                reason = "بدون سبب"

            warnings = load_warnings()

            gid = str(message.guild.id)
            uid = str(member.id)

            if gid not in warnings:
                warnings[gid] = {}

            if uid not in warnings[gid]:
                warnings[gid][uid] = []


            warnings[gid][uid].append({
                "reason": reason,
                "moderator": message.author.name,
                "date": datetime.utcnow().strftime("%Y/%m/%d %H:%M")
            })

            save_warnings(warnings)


            await message.reply(
                f"⚠️ تم تحذير {member.mention}\nالسبب: {reason}"
            )

            return


        # ======================
        # طرد
        # ======================
        if command == "طرد":

            if not message.mentions:
                await message.reply(
                    "❌ مثال: طرد @العضو السبب"
                )
                return

            member = message.mentions[0]

            reason = " ".join(args[2:])

            if not reason:
                reason = "بدون سبب"


            try:
                await member.kick(reason=reason)

                await message.reply(
                    f"👢 تم طرد {member.mention}\nالسبب: {reason}"
                )

            except:
                await message.reply(
                    "❌ لا أستطيع طرد هذا العضو"
                )

            return


        # ======================
        # بان
        # ======================
        if command == "بان":

            if not message.mentions:
                await message.reply(
                    "❌ مثال: بان @العضو السبب"
                )
                return


            member = message.mentions[0]

            reason = " ".join(args[2:])

            if not reason:
                reason = "بدون سبب"


            try:
                await member.ban(reason=reason)

                await message.reply(
                    f"🔨 تم حظر {member.mention}\nالسبب: {reason}"
                )

            except:
                await message.reply(
                    "❌ لا أستطيع حظر هذا العضو"
                )

            return


    # الأوامر المختصرة
    guild_commands = custom_commands.get(
        str(message.guild.id),
        {}
    )

    if message.content in guild_commands:

        data = guild_commands[message.content]

        action = data["command"]

        if action == "lock":
            await message.channel.set_permissions(
                message.guild.default_role,
                send_messages=False
            )

            await message.reply("🔒 تم القفل")

        elif action == "unlock":
            await message.channel.set_permissions(
                message.guild.default_role,
                send_messages=True
            )

            await message.reply("🔓 تم الفتح")


    # نظام Anti-Spam التلقائي
    user_id = message.author.id
    now = time.time()
    if user_id not in user_message_timestamps:
        user_message_timestamps[user_id] = []
    
    user_message_timestamps[user_id] = [t for t in user_message_timestamps[user_id] if now - t < 5]
    user_message_timestamps[user_id].append(now)

    if len(user_message_timestamps[user_id]) >= 5:
        try:
            await message.author.timeout(timedelta(minutes=2), reason="Anti-Spam: إرسال رسائل متعددة بسرعة")
            await message.channel.send(f"⚠️ {message.author.mention} تم إعطاؤك تايم أوت تلقائي بسبب السبام!", delete_after=5)
            user_message_timestamps[user_id] = []
        except:
            pass

    await bot.process_commands(message)


# ==================================
# تشغيل البوت واستعادة الفيوهات
# ==================================

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    
    saved_giveaways = load_giveaways()
    for gid_str, gdata in saved_giveaways.items():
        try:
            channel = bot.get_channel(gdata["channel_id"])
            if channel:
                msg = await channel.fetch_message(gdata["message_id"])
                end_time = datetime.fromisoformat(gdata["end_time"])
                
                view = GiveawayView(int(gid_str))
                bot.add_view(view, message_id=gdata["message_id"])
                
                if datetime.utcnow() < end_time:
                    restored_data = {
                        "id": gdata["id"],
                        "prize": gdata["prize"],
                        "winners_count": gdata["winners_count"],
                        "image_url": gdata["image_url"],
                        "participants": gdata["participants"],
                        "message": msg,
                        "end_time": end_time,
                        "creator": gdata.get("creator", "Unknown")
                    }
                    giveaways[int(gid_str)] = restored_data
                    bot.loop.create_task(giveaway_timer(restored_data))
        except Exception as e:
            print(f"Error restoring giveaway {gid_str}: {e}")

    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} Guild Commands")
    except Exception as e:
        print(f"❌ Sync Error: {e}")


TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
