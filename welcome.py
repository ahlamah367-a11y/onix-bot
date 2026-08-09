import discord
from discord.ext import commands
from discord import app_commands

import json
import os
from datetime import datetime, timedelta
import asyncio
import random
import time
import re

# ==================================
# إعداد خادم الويب الوهمي لإرضاء منصة Render
# ==================================
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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


GUILD_ID = 1532326696714240062


# ==================================
# قاعدة البيانات وملفات الإعدادات
# ==================================

DATABASE_FILE = "tickets_database.json"
BACKUP_FILE = "tickets_backup.json"

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

ECONOMY_FILE = "economy.json"
ACHIEVEMENTS_FILE = "achievements.json"
EVENTS_FILE = "events.json"
FUN_STATS_FILE = "fun_stats.json"

GENERAL_PANELS_FILE = "general_panels.json"


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

economy_data = load_json(ECONOMY_FILE, {})
achievements_data = load_json(ACHIEVEMENTS_FILE, {})
events_data = load_json(EVENTS_FILE, {})
fun_stats = load_json(FUN_STATS_FILE, {})
general_panels = load_json(GENERAL_PANELS_FILE, [])


def save_general_panels():
    save_json(GENERAL_PANELS_FILE, general_panels)


def save_economy():
    save_json(ECONOMY_FILE, economy_data)


def save_achievements():
    save_json(ACHIEVEMENTS_FILE, achievements_data)


def save_events():
    save_json(EVENTS_FILE, events_data)


def save_fun_stats():
    save_json(FUN_STATS_FILE, fun_stats)


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


ACHIEVEMENTS = {
    "first_credit": {
        "name": "💰 أول كريدت",
        "description": "احصل على أول Credit",
        "reward": 100
    },
    "rich": {
        "name": "💎 الثري",
        "description": "وصل إلى 10,000 Credit",
        "reward": 500
    },
    "gambler": {
        "name": "🎲 عاشق الألعاب",
        "description": "العب 25 لعبة",
        "reward": 250
    },
    "winner": {
        "name": "🏆 الفائز",
        "description": "اربح 10 ألعاب",
        "reward": 500
    },
    "event_winner": {
        "name": "🎉 بطل الفعاليات",
        "description": "اربح فعالية",
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


def default_ticket():

    return {
        "name": "تذكرة جديدة",
        "description": "اضغط لفتح التذكرة",
        "panel_description": "اضغط لفتح التذكرة",
        "emoji": "🎫",
        "color": "blue",
        "welcome_message": "أهلاً {user} 👋\nسيتم الرد عليك قريباً.",
        "ticket_image": None,
        "image": None,
        "open_category": None,
        "close_category": None,
        "staff_roles": [],
        "blocked_roles": [],
        "blocked_role": None,
        "open_logs": None,
        "close_logs": None,
        "rating_room": None,
        "claim": True,
        "rating": True,
        "transcript": True,
        "ask_reason": False,
        "max_tickets": 1,
        "prevent_same_type": True,
        "counter": 0,
        "opened": 0,
        "closed": 0,
        "ratings": [],
        "priority": "normal",
        "auto_close": False,
        "auto_close_time": 24,
        "notes": [],
        "added_members": [],
        "last_activity": None
    }


def default_database():

    return {
        "tickets": {},
        "panel": {
            "title": "🎫 نظام التذاكر",
            "description": "اختر نوع التذكرة من القائمة بالأسفل",
            "image": None,
            "channel": None,
            "message_id": None
        },
        "open_tickets": {},
        "closed_today": 0,
        "stats": {
            "total_opened": 0,
            "total_closed": 0,
            "tickets_today": 0,
            "daily_opened": {},
            "daily_closed": {},
            "ratings": [],
            "staff": {},
            "logs": [],
            "permissions": {
                "managers": [],
                "setup_admins": []
            }
        },
        "auto_setup": {}
    }


def load_database():

    if not os.path.exists(DATABASE_FILE):
        return default_database()

    with open(DATABASE_FILE, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except:
            return default_database()


try:
    database = load_database()
except:
    database = default_database()
    save_database = lambda: open(DATABASE_FILE, "w", encoding="utf-8").write(json.dumps(database, indent=4, ensure_ascii=False))
    save_database()


def save_database():

    with open(DATABASE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            database,
            file,
            indent=4,
            ensure_ascii=False
        )


def make_embed(title, description, color=discord.Color.blue()):

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )

    embed.set_footer(
        text="🎫 Professional Ticket System"
    )

    return embed


def is_manager(user):
    if user.guild_permissions.administrator:
        return True
    return user.id in database["stats"]["permissions"]["managers"]


def create_ticket_id():

    number = len(database["tickets"]) + 1
    return f"ticket_{number}"


def get_ticket(ticket_id):

    return database["tickets"].get(ticket_id)


def get_ticket_from_channel(channel_id):

    return database["open_tickets"].get(str(channel_id))


def check_staff(interaction):

    ticket = get_ticket_from_channel(interaction.channel.id)

    if not ticket:
        return False

    settings = database["tickets"].get(ticket["type"])

    if not settings:
        return False

    staff_roles = settings.get("staff_roles", [])
    
    if is_manager(interaction.user):
        return True

    user_roles = [role.id for role in interaction.user.roles]

    for role in staff_roles:
        if role in user_roles:
            return True

    return False


print("✅ الأجزاء الأساسية وقواعد البيانات جاهزة")


@bot.tree.command(
    name="reload-data",
    description="إعادة تحميل قاعدة البيانات"
)
async def reload_data(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ للمشرفين فقط",
            ephemeral=True
        )
        return

    global database
    database = load_database()

    await interaction.response.send_message(
        "✅ تم تحديث البيانات",
        ephemeral=True
    )


@bot.tree.command(
    name="backup-tickets",
    description="عمل نسخة احتياطية"
)
async def backup_tickets(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ للمشرفين فقط",
            ephemeral=True
        )
        return

    filename = f"backup-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(filename,"w",encoding="utf-8") as f:
        json.dump(
            database,
            f,
            indent=4,
            ensure_ascii=False
        )

    await interaction.response.send_message(
        "✅ تم إنشاء نسخة احتياطية",
        file=discord.File(filename),
        ephemeral=True
    )


@bot.tree.command(
    name="restore-backup",
    description="استرجاع نسخة احتياطية"
)
async def restore_backup(interaction:discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ للمشرفين فقط",
            ephemeral=True
        )
        return

    global database

    if not os.path.exists(BACKUP_FILE):
        await interaction.response.send_message(
            "❌ لا يوجد نسخة احتياطية",
            ephemeral=True
        )
        return

    with open(BACKUP_FILE, "r", encoding="utf-8") as file:
        database = json.load(file)

    await interaction.response.send_message(
        embed=make_embed(
            "✅ تم الاسترجاع",
            "تم استرجاع قاعدة بيانات التذاكر بنجاح.",
            discord.Color.green()
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="add-manager",
    description="إضافة مدير لنظام التذاكر"
)
@app_commands.describe(
    member="العضو"
)
async def add_manager(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ للمشرفين فقط",
            ephemeral=True
        )
        return

    database["stats"]["permissions"]["managers"].append(
        member.id
    )

    save_database()

    database["stats"]["logs"].append({
        "user": str(interaction.user.id),
        "action": f"أضاف المدير {member.id}",
        "time": str(datetime.now())
    })

    await interaction.response.send_message(
        embed=make_embed(
            "👑 تم إضافة مدير",
            f"{member.mention} أصبح مدير نظام التذاكر.",
            discord.Color.green()
        )
    )


@bot.tree.command(
    name="ticket-auto-setup",
    description="إعداد نظام التذاكر تلقائياً"
)
async def ticket_auto_setup(
    interaction: discord.Interaction
):

    if not is_manager(interaction.user):
        await interaction.response.send_message(
            "❌ لا تملك صلاحية",
            ephemeral=True
        )
        return

    guild = interaction.guild

    open_category = await guild.create_category(
        "🎫 التذاكر المفتوحة"
    )

    close_category = await guild.create_category(
        "🔒 التذاكر المغلقة"
    )

    logs = await guild.create_text_channel(
        "📜-ticket-logs"
    )

    database["panel"]["channel"] = logs.id

    database["auto_setup"] = {
        "open_category": open_category.id,
        "close_category": close_category.id,
        "logs": logs.id
    }

    save_database()

    await interaction.response.send_message(
        embed=make_embed(
            "✅ تم الإعداد",
            "تم إنشاء نظام التذاكر بالكامل.",
            discord.Color.green()
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="ticket-system-info",
    description="معلومات النظام"
)
async def ticket_system_info(
    interaction: discord.Interaction
):

    embed = make_embed(
        "🤖 حالة النظام",
        ""
    )

    embed.add_field(
        name="🎫 أنواع التذاكر",
        value=str(len(database["tickets"]))
    )

    embed.add_field(
        name="📂 التذاكر المفتوحة",
        value=str(len(database["open_tickets"]))
    )

    embed.add_field(
        name="👑 المدراء",
        value=str(len(database["stats"]["permissions"]["managers"]))
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="dashboard",
    description="لوحة إحصائيات التذاكر"
)
async def dashboard(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ للمشرفين فقط",
            ephemeral=True
        )
        return

    stats = database["stats"]

    embed = discord.Embed(
        title="📊 لوحة التحكم",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🎫 إجمالي الفتح",
        value=str(stats["total_opened"])
    )

    embed.add_field(
        name="🔒 إجمالي الإغلاق",
        value=str(stats["total_closed"])
    )

    embed.add_field(
        name="👑 عدد الإداريين",
        value=str(len(stats["staff"]))
    )

    embed.set_footer(
        text="Ticket System Professional"
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="ticket-create",
    description="إنشاء نوع تذكرة جديد"
)
@app_commands.describe(
    name="اسم التذكرة",
    description="وصف التذكرة في البانل"
)
async def ticket_create(
    interaction: discord.Interaction,
    name: str,
    description: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    ticket_id = create_ticket_id()

    database["tickets"][ticket_id] = default_ticket()
    database["tickets"][ticket_id]["name"] = name
    database["tickets"][ticket_id]["description"] = description
    database["tickets"][ticket_id]["panel_description"] = description

    save_database()

    await interaction.response.send_message(
        f"✅ تم إنشاء نوع تذكرة جديد\n🎫 الاسم: {name}\n🆔 المعرف: `{ticket_id}`",
        ephemeral=True
    )


@bot.tree.command(
    name="ticket-delete",
    description="حذف نوع تذكرة"
)
@app_commands.describe(
    ticket_id="معرف التذكرة"
)
async def ticket_delete(
    interaction: discord.Interaction,
    ticket_id: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    if ticket_id not in database["tickets"]:
        await interaction.response.send_message("❌ هذا النوع غير موجود", ephemeral=True)
        return

    del database["tickets"][ticket_id]
    save_database()

    await interaction.response.send_message("✅ تم حذف نوع التذكرة", ephemeral=True)


@bot.tree.command(
    name="tickets-list",
    description="عرض أنواع التذاكر"
)
async def tickets_list(
    interaction: discord.Interaction
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    if not database["tickets"]:
        await interaction.response.send_message("❌ لا يوجد أنواع تذاكر حالياً", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎫 أنواع التذاكر",
        color=discord.Color.blue()
    )

    for ticket_id, data in database["tickets"].items():
        embed.add_field(
            name=f"{data['emoji']} {data['name']}",
            value=f"🆔 `{ticket_id}`\n📝 {data.get('description', data.get('panel_description', ''))}",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="ticket-copy",
    description="نسخ إعدادات تذكرة موجودة بالكامل"
)
@app_commands.describe(
    ticket_id="معرف التذكرة المراد نسخها"
)
async def ticket_copy(
    interaction: discord.Interaction,
    ticket_id: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    original_ticket = get_ticket(ticket_id)
    if not original_ticket:
        await interaction.response.send_message("❌ التذكرة المراد نسخها غير موجودة", ephemeral=True)
        return

    new_id = create_ticket_id()
    copied_data = json.loads(json.dumps(original_ticket))
    copied_data["name"] = f"{copied_data['name']} (نسخة)"
    copied_data["counter"] = 0
    copied_data["opened"] = 0
    copied_data["closed"] = 0
    copied_data["ratings"] = []

    database["tickets"][new_id] = copied_data
    save_database()

    await interaction.response.send_message(f"✅ تم نسخ التذكرة بنجاح!\n🆔 المعرف الجديد: `{new_id}`", ephemeral=True)


@bot.tree.command(
    name="ticket-rename-type",
    description="تغيير اسم نوع التذكرة"
)
@app_commands.describe(
    ticket_id="معرف التذكرة",
    new_name="الاسم الجديد"
)
async def ticket_rename_type(
    interaction: discord.Interaction,
    ticket_id: str,
    new_name: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    ticket = get_ticket(ticket_id)

    if not ticket:
        await interaction.response.send_message("❌ التذكرة غير موجودة", ephemeral=True)
        return

    ticket["name"] = new_name
    save_database()

    await interaction.response.send_message("✅ تم تغيير الاسم", ephemeral=True)


class PanelSettingsModal(discord.ui.Modal):

    def __init__(self, option):
        super().__init__(title="تعديل البانل")
        self.option = option

        self.value = discord.ui.TextInput(
            label="القيمة الجديدة",
            placeholder="اكتب التعديل هنا",
            required=True,
            max_length=500
        )
        self.add_item(self.value)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.value.value

        if self.option == "title":
            database["panel"]["title"] = value
        elif self.option == "description":
            database["panel"]["description"] = value
        elif self.option == "image":
            database["panel"]["image"] = value

        save_database()
        await interaction.response.send_message("✅ تم تعديل البانل", ephemeral=True)


class PanelSettingsView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="إعدادات البانل",
        options=[
            discord.SelectOption(label="تعديل عنوان البانل", value="title", emoji="✏️"),
            discord.SelectOption(label="تعديل وصف البانل", value="description", emoji="📝"),
            discord.SelectOption(label="إضافة صورة للبانل", value="image", emoji="🖼️")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(PanelSettingsModal(select.values[0]))


@bot.tree.command(
    name="panel-setup",
    description="تعديل إعدادات البانل الموحد"
)
async def panel_setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    embed = discord.Embed(
        title="🖥️ إعداد البانل",
        description="اختر الشيء الذي تريد تعديله:\n\n✏️ العنوان\n📝 الوصف\n🖼️ الصورة",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=PanelSettingsView(), ephemeral=True)


class TicketSelect(discord.ui.Select):

    def __init__(self):

        options = []

        for ticket_id, data in database["tickets"].items():

            options.append(
                discord.SelectOption(
                    label=data["name"],
                    value=ticket_id,
                    description=data.get(
                        "panel_description",
                        data.get("description", "فتح تذكرة")
                    )[:100],
                    emoji=data.get("emoji", "🎫")
                )
            )

        if not options:

            options.append(
                discord.SelectOption(
                    label="لا يوجد تذاكر",
                    value="none",
                    emoji="❌"
                )
            )

        options.append(
            discord.SelectOption(
                label="🔄 تحديث القائمة",
                value="refresh_menu",
                description="إعادة تحميل أنواع التذاكر",
                emoji="🔄"
            )
        )

        super().__init__(
            placeholder="🎫 اختر نوع التذكرة",
            options=options,
            custom_id="ticket_select_menu_secure"
        )

    async def callback(self, interaction: discord.Interaction):

        ticket_type = self.values[0]

        if ticket_type == "refresh_menu":

            await interaction.response.edit_message(
                view=TicketPanel()
            )

            return

        if ticket_type == "none":

            await interaction.response.send_message(
                "❌ لا يوجد أنواع تذاكر حاليا",
                ephemeral=True
            )

            return

        user_id = interaction.user.id

        ticket_settings = database["tickets"].get(ticket_type)

        for t in database["open_tickets"].values():

            if t.get("owner") == user_id:

                await interaction.response.send_message(
                    "❌ لديك تذكرة مفتوحة بالفعل",
                    ephemeral=True
                )

                return

        if ticket_settings and ticket_settings.get("ask_reason"):

            await interaction.response.send_modal(
                TicketFormModal(ticket_type)
            )

            return

        await create_ticket(
            interaction,
            ticket_type,
            None
        )


class TicketPanel(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            TicketSelect()
        )


@bot.tree.command(
    name="send-ticket-panel",
    description="إرسال بانل التذاكر الموحد"
)
async def send_ticket_panel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ هذا الأمر للمشرفين فقط",
            ephemeral=True
        )

        return

    await interaction.response.defer(
        ephemeral=True
    )

    panel = database["panel"]
    old_message_id = panel.get("message_id")

    if old_message_id:

        try:

            old_message = await interaction.channel.fetch_message(
                old_message_id
            )

            await old_message.delete()

        except:

            pass

    embed = discord.Embed(

        title=panel.get(
            "title",
            "🎫 نظام التذاكر"
        ),

        description=panel.get(
            "description",
            "اختر نوع التذكرة من القائمة"
        ),

        color=discord.Color.blue()

    )

    if panel.get("image"):

        embed.set_image(
            url=panel["image"]
        )

    message = await interaction.channel.send(

        embed=embed,

        view=TicketPanel()

    )

    database["panel"]["message_id"] = message.id
    database["panel"]["channel"] = interaction.channel.id
    save_database()

    await interaction.followup.send(

        "✅ تم إرسال بانل التذاكر",

        ephemeral=True

    )


class TicketFormModal(discord.ui.Modal):

    def __init__(self, ticket_type):
        super().__init__(title="معلومات فتح التذكرة")
        self.ticket_type = ticket_type

        self.question1 = discord.ui.TextInput(
            label="ماذا تريد؟",
            placeholder="اكتب طلبك بالتفصيل",
            required=True,
            max_length=300
        )

        self.question2 = discord.ui.TextInput(
            label="التفاصيل الإضافية",
            placeholder="اكتب أي معلومات تساعد الإدارة",
            required=False,
            max_length=300
        )

        self.add_item(self.question1)
        self.add_item(self.question2)

    async def on_submit(self, interaction: discord.Interaction):

        reason = (
            f"📝 الطلب:\n{self.question1.value}\n\n"
            f"📌 التفاصيل:\n{self.question2.value}"
        )

        await create_ticket(
            interaction,
            self.ticket_type,
            reason
        )


@bot.tree.command(
    name="ticket-form",
    description="تفعيل نموذج أسئلة لنوع تذكرة"
)
@app_commands.describe(
    ticket_id="معرف نوع التذكرة"
)
async def ticket_form(
    interaction: discord.Interaction,
    ticket_id: str
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ هذا الأمر للمشرفين فقط",
            ephemeral=True
        )
        return

    if ticket_id not in database["tickets"]:
        await interaction.response.send_message(
            "❌ نوع التذكرة غير موجود",
            ephemeral=True
        )
        return

    database["tickets"][ticket_id]["ask_reason"] = True
    save_database()

    await interaction.response.send_message(
        embed=make_embed(
            "✅ تم تفعيل النموذج",
            f"تم تفعيل أسئلة الفتح لنوع التذكرة:\n🎫 {database['tickets'][ticket_id]['name']}",
            discord.Color.green()
        ),
        ephemeral=True
    )


async def create_transcript(channel):
    messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        author = f"{message.author.name}#{message.author.discriminator}" if message.author.discriminator != "0" else message.author.name
        avatar = message.author.display_avatar.url
        content = message.content or ""
        
        embeds_html = ""
        for embed in message.embeds:
            embeds_html += f"""
            <div style="background-color: #2f3136; border-left: 4px solid #7289da; padding: 10px; margin-top: 5px; border-radius: 4px;">
                <b style="color: #ffffff;">{embed.title or ''}</b>
                <p style="color: #dcddde; white-space: pre-wrap;">{embed.description or ''}</p>
            </div>
            """

        attachments_html = ""
        for att in message.attachments:
            attachments_html += f'<br><a href="{att.url}" target="_blank" style="color: #00b0f4;">📎 {att.filename}</a>'

        messages.append(f"""
        <div style="display: flex; margin-bottom: 15px; font-family: Arial, sans-serif;">
            <img src="{avatar}" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 15px;">
            <div>
                <div><b>{author}</b> <span style="font-size: 11px; color: #72767d; margin-left: 5px;">{timestamp}</span></div>
                <div style="color: #dcddde; white-space: pre-wrap; margin-top: 2px;">{content}</div>
                {embeds_html}
                {attachments_html}
            </div>
        </div>
        """)

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Transcript - {channel.name}</title>
    </head>
    <body style="background-color: #36393f; color: #dcddde; padding: 20px;">
        <h2 style="color: #ffffff; border-bottom: 1px solid #4f545c; padding-bottom: 10px;">📜 سجل التذكرة: {channel.name}</h2>
        {"".join(messages)}
    </body>
    </html>
    """

    filename = f"transcript-{channel.id}.html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)

    return filename


async def send_open_log(interaction, channel, ticket):
    settings = database["tickets"].get(ticket["type"])
    if not settings:
        return

    log_id = settings.get("open_logs")
    if not log_id:
        return

    log = interaction.guild.get_channel(log_id)
    if log:
        embed = discord.Embed(
            title="🎫 فتح تذكرة",
            description=f"👤 العضو:\n{interaction.user.mention}\n\n📁 الروم:\n{channel.mention}",
            color=discord.Color.green()
        )
        await log.send(embed=embed)


async def send_close_log(interaction, channel, transcript):
    ticket = database["open_tickets"].get(str(channel.id))
    if not ticket:
        return

    settings = database["tickets"].get(ticket["type"])
    if not settings:
        return

    log_id = settings.get("close_logs")
    if not log_id:
        return

    log = interaction.guild.get_channel(log_id)
    if log:
        embed = discord.Embed(
            title="🔒 إغلاق تذكرة",
            description=f"👤 أغلقها:\n{interaction.user.mention}\n\n📁 الروم:\n{channel.name}",
            color=discord.Color.red()
        )
        await log.send(embed=embed)
        await log.send(file=discord.File(transcript))


async def create_ticket(interaction, ticket_type, reason=None):
    settings = database["tickets"].get(ticket_type)
    if not settings:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ نوع التذكرة غير موجود", ephemeral=True)
        return

    category_id = settings.get("open_category")
    category = interaction.guild.get_channel(category_id) if category_id else None

    settings["counter"] += 1
    number = settings["counter"]
    channel_name = f"{settings['emoji']}-ticket-{number}"

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    }

    for role_id in settings.get("staff_roles", []):
        role = interaction.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channel = await interaction.guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites
    )

    database["open_tickets"][str(channel.id)] = {
        "owner": interaction.user.id,
        "user": str(interaction.user.id),
        "type": ticket_type,
        "created": str(datetime.now()),
        "claimed": None,
        "reason": reason,
        "closed": False,
        "priority": "normal",
        "last_activity": str(datetime.now()),
        "added_members": []
    }

    database["stats"]["total_opened"] += 1
    settings["opened"] += 1
    save_database()

    colors = {
        "blue": discord.Color.blue(),
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "gold": discord.Color.gold()
    }
    embed_color = colors.get(settings.get("color"), discord.Color.blue())

    welcome_text = settings.get("welcome_message", "أهلاً {user} 👋\nسيتم الرد عليك قريباً.")
    embed = discord.Embed(
        title=f"{settings['emoji']} {settings['name']}",
        description=welcome_text.replace("{user}", interaction.user.mention),
        color=embed_color
    )

    embed.add_field(name="👤 صاحب التذكرة", value=interaction.user.mention, inline=False)
    embed.add_field(name="🔢 رقم التذكرة", value=f"#{number}", inline=False)

    if reason:
        embed.add_field(name="📝 السبب", value=reason, inline=False)

    if settings.get("ticket_image") or settings.get("image"):
        embed.set_image(url=settings.get("ticket_image") or settings.get("image"))

    embed.set_footer(text="نظام التذاكر الاحترافي")

    await channel.send(embed=embed, view=TicketButtons())
    await send_open_log(interaction, channel, database["open_tickets"][str(channel.id)])

    if not interaction.response.is_done():
        await interaction.response.send_message(f"✅ تم فتح التذكرة {channel.mention}", ephemeral=True)


class TicketButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim",
        emoji="👑",
        style=discord.ButtonStyle.blurple,
        custom_id="claim_button_secure"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_staff(interaction):
            await interaction.response.send_message("❌ ليس لديك صلاحية لاستلاستلام التذكرة", ephemeral=True)
            return

        ticket = database["open_tickets"].get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("❌ التذكرة غير موجودة", ephemeral=True)
            return

        if ticket.get("claimed"):
            await interaction.response.send_message(
                "⚠️ هذه التذكرة تم استلامها مسبقاً",
                ephemeral=True
            )
            return

        ticket["claimed"] = interaction.user.id
        
        staff = str(interaction.user.id)
        if staff not in database["stats"]["staff"]:
            database["stats"]["staff"][staff] = {
                "claimed": 0,
                "closed": 0
            }
        database["stats"]["staff"][staff]["claimed"] += 1

        database["stats"]["logs"].append({
            "user": str(interaction.user.id),
            "action": "استلم التذكرة",
            "time": str(datetime.now())
        })

        save_database()
        
        button.disabled = True
        await interaction.message.edit(view=self)

        embed = make_embed(
            "👑 تم استلام التذكرة",
            f"الإداري المسؤول الآن:\n{interaction.user.mention}",
            discord.Color.gold()
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(f"👑 تم استلام التذكرة بنجاح", ephemeral=True)

    @discord.ui.button(
        label="إغلاق",
        emoji="🔒",
        style=discord.ButtonStyle.red,
        custom_id="close_button_secure"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_staff(interaction):
            await interaction.response.send_message("❌ ليس لديك صلاحية", ephemeral=True)
            return

        channel_id = str(interaction.channel.id)
        if channel_id in database["open_tickets"]:
            database["open_tickets"][channel_id]["closed"] = True
            
            staff = str(interaction.user.id)
            if staff not in database["stats"]["staff"]:
                database["stats"]["staff"][staff] = {"claimed": 0, "closed": 0}
            database["stats"]["staff"][staff]["closed"] += 1

            database["stats"]["logs"].append({
                "user": str(interaction.user.id),
                "action": "أغلق التذكرة",
                "time": str(datetime.now())
            })

        save_database()

        await interaction.response.send_message(
            "🔒 تم تجهيز إغلاق التذكرة\n⭐ اختر تقييم الخدمة:",
            view=RatingView(interaction.channel.id),
            ephemeral=True
        )


class RatingView(discord.ui.View):

    def __init__(self, ticket_channel_id):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id

    async def save_rating(self, interaction, stars):
        ticket = database["open_tickets"].get(str(self.ticket_channel_id))
        if not ticket:
            return

        ticket_type = ticket["type"]
        ticket_settings = database["tickets"].get(ticket_type)

        if ticket_settings:
            ticket_settings["ratings"].append({
                "user": str(interaction.user.id),
                "stars": stars,
                "staff": ticket.get("claimed")
            })

        save_database()
        await send_rating_log(interaction, stars, ticket)
        
        channel = interaction.channel
        
        close_cat_id = ticket_settings.get("close_category") if ticket_settings else None
        if close_cat_id:
            close_category = interaction.guild.get_channel(close_cat_id)
            if close_category:
                try:
                    await channel.edit(category=close_category)
                except:
                    pass

        transcript = await create_transcript(channel)
        await send_close_log(interaction, channel, transcript)

        await interaction.response.send_message("⭐ تم حفظ تقييمك بنجاح، سيتم حذف الروم خلال 3 ثواني...", ephemeral=True)
        
        await asyncio.sleep(3)
        try:
            await channel.delete()
        except:
            pass

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.gray, custom_id="rating_1_sec")
    async def one(self, interaction, button):
        await self.save_rating(interaction, 1)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.blurple, custom_id="rating_3_sec")
    async def three(self, interaction, button):
        await self.save_rating(interaction, 3)

    @discord.ui.button(
        label="⭐⭐⭐⭐",
        style=discord.ButtonStyle.blurple,
        custom_id="rating_4_sec"
    )
    async def four(self, interaction, button):
        await self.save_rating(interaction, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.green, custom_id="rating_5_sec")
    async def five(self, interaction, button):
        await self.save_rating(interaction, 5)


async def send_rating_log(interaction, stars, ticket):
    ticket_type = database["tickets"].get(ticket["type"])
    if not ticket_type:
        return

    rating_room = ticket_type.get("rating_room")
    if not rating_room:
        return

    channel = interaction.guild.get_channel(rating_room)
    if not channel:
        return

    staff = ticket.get("claimed")
    staff_text = f"<@{staff}>" if staff else "لا يوجد"

    embed = discord.Embed(title="⭐ تقييم جديد", color=discord.Color.gold())
    embed.add_field(name="👤 العضو", value=interaction.user.mention, inline=False)
    embed.add_field(name="⭐ التقييم", value=f"{stars}/5", inline=False)
    embed.add_field(name="👑 الإداري المستلم", value=staff_text, inline=False)

    await channel.send(embed=embed)


@bot.tree.command(name="claim", description="استلام التذكرة")
async def claim_ticket(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ ليس لديك صلاحية لاستلام التذكرة", ephemeral=True)
        return

    ticket = get_ticket_from_channel(interaction.channel.id)
    if not ticket:
        await interaction.response.send_message("❌ التذكرة غير موجودة", ephemeral=True)
        return

    if ticket.get("claimed"):
        await interaction.response.send_message("⚠️ هذه التذكرة تم استلامها مسبقاً", ephemeral=True)
        return

    ticket["claimed"] = interaction.user.id
    
    staff = str(interaction.user.id)
    if staff not in database["stats"]["staff"]:
        database["stats"]["staff"][staff] = {"claimed": 0, "closed": 0}
    database["stats"]["staff"][staff]["claimed"] += 1

    database["stats"]["logs"].append({
        "user": str(interaction.user.id),
        "action": "استلم التذكرة",
        "time": str(datetime.now())
    })

    save_database()
    
    embed = make_embed(
        "👑 تم استلام التذكرة",
        f"الإداري المسؤول الآن:\n{interaction.user.mention}",
        discord.Color.gold()
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message(f"👑 تم استلام التذكرة", ephemeral=True)


@bot.tree.command(name="close", description="إغلاق التذكرة")
async def close_ticket(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    channel_id = str(interaction.channel.id)
    if channel_id in database["open_tickets"]:
        database["open_tickets"][channel_id]["closed"] = True
        
        staff = str(interaction.user.id)
        if staff not in database["stats"]["staff"]:
            database["stats"]["staff"][staff] = {"claimed": 0, "closed": 0}
        database["stats"]["staff"][staff]["closed"] += 1

        database["stats"]["logs"].append({
            "user": str(interaction.user.id),
            "action": "أغلق التذكرة",
            "time": str(datetime.now())
        })

    save_database()
    await interaction.response.send_message("⭐ يرجى تقييم التذكرة قبل الإغلاق", view=RatingView(interaction.channel.id), ephemeral=True)


@bot.tree.command(name="rename", description="تغيير اسم التذكرة")
@app_commands.describe(name="الاسم الجديد")
async def rename_ticket(interaction: discord.Interaction, name: str):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.edit(name=name)
    database["stats"]["logs"].append({
        "user": str(interaction.user.id),
        "action": f"غير اسم التذكرة إلى {name}",
        "time": str(datetime.now())
    })
    save_database()
    await interaction.response.send_message("✅ تم تغيير الاسم")


@bot.tree.command(name="priority", description="تحديد أولوية التذكرة")
@app_commands.choices(
    level=[
        app_commands.Choice(name="عادي", value="normal"),
        app_commands.Choice(name="مهم", value="important"),
        app_commands.Choice(name="عاجل", value="urgent")
    ]
)
async def priority_ticket(interaction: discord.Interaction, level: app_commands.Choice[str]):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    ticket = get_ticket_from_channel(interaction.channel.id)
    ticket["priority"] = level.value
    ticket["last_activity"] = str(datetime.now())
    save_database()
    await interaction.response.send_message(f"📌 تم تغيير الأولوية إلى: {level.name}")


@bot.tree.command(name="ticket-add", description="إضافة عضو للتذكرة")
async def ticket_add(interaction: discord.Interaction, member: discord.Member):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.set_permissions(member, view_channel=True, send_messages=True)
    await interaction.response.send_message(f"✅ تمت إضافة {member.mention}")


@bot.tree.command(name="ticket-remove", description="إزالة عضو من التذكرة")
async def ticket_remove(interaction: discord.Interaction, member: discord.Member):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.set_permissions(member, overwrite=None)
    await interaction.response.send_message(f"✅ تمت إزالة {member.mention}")


@bot.tree.command(name="lock", description="قفل الكتابة في التذكرة")
async def lock_ticket(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل التذكرة")


@bot.tree.command(name="unlock", description="فتح الكتابة في التذكرة")
async def unlock_ticket(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح التذكرة")


@bot.tree.command(name="reopen", description="إعادة فتح التذكرة")
async def reopen_ticket(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
    await interaction.response.send_message("🔄 تم إعادة فتح التذكرة")


@bot.tree.command(name="move", description="نقل التذكرة")
@app_commands.describe(category="ID الكاتجوري الجديد")
async def move_ticket(interaction: discord.Interaction, category: str):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    try:
        category_id = int(category)
    except:
        await interaction.response.send_message("❌ ID غير صحيح", ephemeral=True)
        return

    new_category = interaction.guild.get_channel(category_id)
    if not new_category:
        await interaction.response.send_message("❌ لم يتم العثور على الكاتجوري", ephemeral=True)
        return

    await interaction.channel.edit(category=new_category)
    await interaction.response.send_message("🚚 تم نقل التذكرة")


@bot.tree.command(
    name="auto-move",
    description="نقل التذكرة تلقائياً إلى كاتجوري"
)
@app_commands.describe(
    category="ID الكاتجوري"
)
async def auto_move(
    interaction: discord.Interaction,
    category: str
):
    if not check_staff(interaction):
        await interaction.response.send_message(
            "❌ لا تملك صلاحية",
            ephemeral=True
        )
        return

    try:
        category_id = int(category)
    except:
        await interaction.response.send_message(
            "❌ ID غير صحيح",
            ephemeral=True
        )
        return

    new_category = interaction.guild.get_channel(category_id)

    if not new_category:
        await interaction.response.send_message(
            "❌ الكاتجوري غير موجود",
            ephemeral=True
        )
        return

    await interaction.channel.edit(
        category=new_category
    )

    embed = discord.Embed(
        title="🚚 تم نقل التذكرة",
        description=f"تم نقل التذكرة إلى:\n{new_category.name}",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="ticket-info",
    description="عرض معلومات التذكرة الحالية"
)
async def ticket_info(interaction: discord.Interaction):

    ticket = get_ticket_from_channel(interaction.channel.id)

    if not ticket:
        await interaction.response.send_message(
            "❌ هذا الروم ليس تذكرة",
            ephemeral=True
        )
        return

    settings = database["tickets"].get(ticket["type"])

    embed = discord.Embed(
        title="🎫 معلومات التذكرة",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👤 صاحب التذكرة",
        value=f"<@{ticket['owner']}>",
        inline=False
    )

    embed.add_field(
        name="📁 النوع",
        value=settings["name"] if settings else "غير معروف",
        inline=False
    )

    embed.add_field(
        name="👑 المستلم",
        value=f"<@{ticket['claimed']}>" if ticket["claimed"] else "لا يوجد",
        inline=False
    )

    embed.add_field(
        name="📌 الأولوية",
        value=ticket.get("priority","normal"),
        inline=False
    )

    embed.add_field(
        name="📅 التاريخ",
        value=ticket.get("created","غير معروف"),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@bot.tree.command(
    name="ticket-note",
    description="إضافة ملاحظة للتذكرة"
)
@app_commands.describe(
    note="الملاحظة"
)
async def ticket_note(
    interaction: discord.Interaction,
    note: str
):

    if not check_staff(interaction):
        await interaction.response.send_message(
            "❌ ليس لديك صلاحية",
            ephemeral=True
        )
        return

    ticket = get_ticket_from_channel(interaction.channel.id)

    if not ticket:
        await interaction.response.send_message(
            "❌ ليست تذكرة",
            ephemeral=True
        )
        return

    ticket.setdefault("notes", [])

    ticket["notes"].append({
        "staff": interaction.user.id,
        "note": note,
        "time": str(datetime.now())
    })

    save_database()

    await interaction.response.send_message(
        "✅ تم حفظ الملاحظة",
        ephemeral=True
    )


@bot.tree.command(
    name="ticket-notes",
    description="عرض ملاحظات التذكرة"
)
async def ticket_notes(interaction: discord.Interaction):

    ticket = get_ticket_from_channel(interaction.channel.id)

    if not ticket:
        await interaction.response.send_message(
            "❌ ليست تذكرة",
            ephemeral=True
        )
        return

    notes = ticket.get("notes", [])

    if not notes:
        await interaction.response.send_message(
            "📭 لا يوجد ملاحظات",
            ephemeral=True
        )
        return

    text = ""

    for n in notes:
        text += f"👤 <@{n['staff']}> : {n['note']}\n"

    embed = discord.Embed(
        title="📝 ملاحظات التذكرة",
        description=text,
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@bot.tree.command(name="ticket-stats", description="إحصائيات التذاكر")
async def ticket_stats(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    opened = len(database["open_tickets"])
    closed = database.get("closed_today", 0)

    embed = discord.Embed(title="📊 إحصائيات التذاكر", color=discord.Color.blue())
    embed.add_field(name="🎫 المفتوحة", value=str(opened))
    embed.add_field(name="🔒 المغلقة", value=str(closed))
    await interaction.response.send_message(embed=embed)


class TicketSettingsModal(discord.ui.Modal):

    def __init__(self, ticket_id, option):
        super().__init__(title="تعديل إعداد التذكرة")
        self.ticket_id = ticket_id
        self.option = option

        self.value = discord.ui.TextInput(
            label="القيمة الجديدة",
            placeholder="اكتب القيمة أو ID هنا",
            required=True,
            max_length=4000
        )
        self.add_item(self.value)

    async def on_submit(self, interaction: discord.Interaction):
        ticket = database["tickets"][self.ticket_id]
        value = self.value.value

        if self.option == "name":
            ticket["name"] = value
        elif self.option == "description":
            ticket["description"] = value
            ticket["panel_description"] = value
        elif self.option == "emoji":
            ticket["emoji"] = value
        elif self.option == "color":
            ticket["color"] = value
        elif self.option == "welcome":
            ticket["welcome_message"] = value
        elif self.option == "image":
            ticket["ticket_image"] = value
            ticket["image"] = value
        elif self.option == "open_category":
            ticket["open_category"] = int(value)
        elif self.option == "close_category":
            ticket["close_category"] = int(value)
        elif self.option == "staff_role":
            ticket["staff_roles"].append(int(value))
        elif self.option == "remove_staff_role":
            role_id = int(value)
            if role_id in ticket["staff_roles"]:
                ticket["staff_roles"].remove(role_id)

        save_database()
        await interaction.response.send_message("✅ تم حفظ التعديل", ephemeral=True)


class TicketSettingsView(discord.ui.View):

    def __init__(self, ticket_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id

    @discord.ui.select(
        placeholder="اختر إعداد للتعديل",
        options=[
            discord.SelectOption(label="اسم التذكرة", value="name", emoji="🏷️"),
            discord.SelectOption(label="وصف البانل", value="description", emoji="📝"),
            discord.SelectOption(label="إيموجي التذكرة", value="emoji", emoji="😀"),
            discord.SelectOption(label="لون التذكرة", value="color", emoji="🎨"),
            discord.SelectOption(label="رسالة الترحيب", value="welcome", emoji="👋"),
            discord.SelectOption(label="صورة داخل التذكرة", value="image", emoji="🖼️"),
            discord.SelectOption(label="كاتجوري الفتح", value="open_category", emoji="📂"),
            discord.SelectOption(label="كاتجوري الإغلاق", value="close_category", emoji="🔒"),
            discord.SelectOption(label="إضافة رتبة إدارة", value="staff_role", emoji="🛡️"),
            discord.SelectOption(label="إزالة رتبة إدارة", value="remove_staff_role", emoji="❌")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(TicketSettingsModal(self.ticket_id, select.values[0]))


@bot.tree.command(name="ticket-settings", description="تعديل إعدادات نوع تذكرة")
@app_commands.describe(ticket_id="معرف التذكرة")
async def ticket_settings(interaction: discord.Interaction, ticket_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط", ephemeral=True)
        return

    if ticket_id not in database["tickets"]:
        await interaction.response.send_message("❌ نوع التذكرة غير موجود", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚙️ إعدادات التذكرة",
        description=f"تعديل:\n🎫 {database['tickets'][ticket_id]['name']}",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=TicketSettingsView(ticket_id), ephemeral=True)


spam_users = {}
SPAM_LIMIT = 5
SPAM_TIME = 5


async def anti_spam(message):
    user = message.author.id
    now = asyncio.get_event_loop().time()

    if user not in spam_users:
        spam_users[user] = []

    spam_users[user].append(now)

    spam_users[user] = [
        x for x in spam_users[user]
        if now - x <= SPAM_TIME
    ]

    if len(spam_users[user]) >= SPAM_LIMIT:
        try:
            await message.delete()
        except:
            pass

        embed = discord.Embed(
            title="⚠️ حماية السبام",
            description=f"{message.author.mention} تم منع الإرسال السريع.",
            color=discord.Color.orange()
        )

        await message.channel.send(
            embed=embed,
            delete_after=5
        )

        spam_users[user] = []


AUTO_CLOSE_TIME = 24 * 60 * 60

async def auto_close_checker():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        for channel_id, ticket in list(database["open_tickets"].items()):
            try:
                created = datetime.fromisoformat(ticket["created"])
                if (now - created).total_seconds() >= AUTO_CLOSE_TIME:
                    channel = bot.get_channel(int(channel_id))
                    if channel:
                        embed = discord.Embed(
                            title="🔒 إغلاق تلقائي",
                            description="تم إغلاق التذكرة بسبب عدم النشاط لمدة 24 ساعة.",
                            color=discord.Color.red()
                        )
                        await channel.send(embed=embed)
                        try:
                            await channel.delete()
                        except:
                            pass
                    del database["open_tickets"][channel_id]
                    save_database()
            except:
                pass
        await asyncio.sleep(300)


async def database_backup():
    await bot.wait_until_ready()
    while not bot.is_closed():
        with open(BACKUP_FILE, "w", encoding="utf-8") as file:
            json.dump(
                database,
                file,
                indent=4,
                ensure_ascii=False
            )
        await asyncio.sleep(3600)


@bot.tree.command(
    name="balance",
    description="عرض رصيدك أو رصيد عضو"
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
        title="💰 الرصيد",
        description=(
            f"👤 العضو: {member.mention}\n\n"
            f"💳 **Credits:** `{data['credits']:,}`"
        ),
        color=discord.Color.gold()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="daily",
    description="استلام مكافأة يومية"
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
            f"⏳ ارجع بعد **{hours} ساعة و {minutes} دقيقة**.",
            ephemeral=True
        )
        return

    reward = random.randint(300, 700)

    user["credits"] += reward
    user["daily"] = now

    save_economy()

    unlock_achievement(
        interaction.guild.id,
        interaction.user.id,
        "first_credit"
    )

    await interaction.response.send_message(
        f"🎁 حصلت على **{reward:,} Credits** اليوم!\n"
        f"💰 رصيدك الآن: **{user['credits']:,}**"
    )


@bot.tree.command(
    name="work",
    description="اعمل لتحصل على Credits"
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
            f"⏳ يمكنك العمل بعد `{minutes}m {seconds}s`.",
            ephemeral=True
        )
        return

    jobs = [
        "💻 برمجت بوت جديد",
        "🧹 نظفت السيرفر",
        "🎮 لعبت مع الأعضاء",
        "🛠️ ساعدت الإدارة",
        "📦 رتبت الملفات",
        "☕ اشتغلت في الكافيه"
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
        f"💵 حصلت على **{reward:,} Credits**\n"
        f"💰 رصيدك: **{user['credits']:,}**"
    )


@bot.tree.command(
    name="pay",
    description="تحويل Credits إلى عضو"
)
async def pay(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    if member.bot:
        await interaction.response.send_message(
            "❌ لا يمكنك التحويل للبوتات.",
            ephemeral=True
        )
        return

    if member.id == interaction.user.id:
        await interaction.response.send_message(
            "😂 تريد تدفع لنفسك؟",
            ephemeral=True
        )
        return

    if amount <= 0:
        await interaction.response.send_message(
            "❌ المبلغ يجب أن يكون أكبر من صفر.",
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
            "❌ ما عندك Credits كافية.",
            ephemeral=True
        )
        return

    sender["credits"] -= amount
    receiver["credits"] += amount

    save_economy()

    await interaction.response.send_message(
        f"💸 تم تحويل **{amount:,} Credits** إلى {member.mention}."
    )


@bot.tree.command(
    name="economy-leaderboard",
    description="ترتيب أغنى أعضاء السيرفر"
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
            "❌ لا توجد بيانات بعد."
        )
        return

    lines = []
    medals = ["🥇", "🥈", "🥉"]

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
            f"{medal} {member.mention} — "
            f"**{data.get('credits', 0):,}** 💰"
        )

    embed = discord.Embed(
        title="🏆 أغنى أعضاء السيرفر",
        description="\n".join(lines),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="8ball",
    description="اسأل الكرة السحرية"
)
async def eight_ball(
    interaction: discord.Interaction,
    question: str
):

    answers = [
        "نعم ✅",
        "لا ❌",
        "غالبًا 🤔",
        "مستحيل 💀",
        "أكيد 🔥",
        "اسألني بكرة 🗿",
        "الجواب عند المدير 👀",
        "ما عندي علم 😂",
        "الاحتمال كبير جدًا 📈",
        "لا تسأل أسئلة صعبة 😭"
    ]

    await interaction.response.send_message(
        f"🎱 **السؤال:** {question}\n\n"
        f"🔮 **الجواب:** {random.choice(answers)}"
    )


@bot.tree.command(
    name="dice",
    description="ارمِ النرد"
)
async def dice(interaction: discord.Interaction):

    result = random.randint(1, 6)

    await interaction.response.send_message(
        f"🎲 رميت النرد وطلع: **{result}**"
    )


@bot.tree.command(
    name="coinflip",
    description="اقلب العملة"
)
async def coinflip(interaction: discord.Interaction):

    result = random.choice([
        "🪙 صورة",
        "🪙 كتابة"
    ])

    await interaction.response.send_message(
        f"🪙 النتيجة: **{result}**"
    )


@bot.tree.command(
    name="choose",
    description="خل البوت يختار لك"
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
            "❌ اكتب خيارين على الأقل مفصولين بفاصلة.\n"
            "مثال: `/choose بيتزا, برغر, شاورما`",
            ephemeral=True
        )
        return

    selected = random.choice(choices)

    await interaction.response.send_message(
        f"🎯 اخترت لك: **{selected}**"
    )


@bot.tree.command(
    name="rank",
    description="عرض مستواك و XP"
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
        title=f"⭐ مستوى {member.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="⭐ المستوى",
        value=f"`{level}`",
        inline=True
    )

    embed.add_field(
        name="✨ XP",
        value=f"`{xp:,}`",
        inline=True
    )

    embed.add_field(
        name="📈 المستوى القادم",
        value=f"`{next_xp:,} XP`",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="profile",
    description="عرض ملفك الشخصي الكامل"
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
        title=f"👤 ملف {member.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="⭐ المستوى",
        value=f"`{xp.get('level', 1)}`",
        inline=True
    )

    embed.add_field(
        name="✨ XP",
        value=f"`{xp.get('xp', 0):,}`",
        inline=True
    )

    embed.add_field(
        name="💰 Credits",
        value=f"`{money.get('credits', 0):,}`",
        inline=True
    )

    embed.add_field(
        name="🎮 الألعاب",
        value=f"`{money.get('games', 0)}`",
        inline=True
    )

    embed.add_field(
        name="🏆 الانتصارات",
        value=f"`{money.get('wins', 0)}`",
        inline=True
    )

    embed.add_field(
        name="🎉 فعاليات فاز بها",
        value=f"`{money.get('events_won', 0)}`",
        inline=True
    )

    embed.add_field(
        name="🏅 الإنجازات",
        value=f"`{len(user_achievements)}`",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="achievements",
    description="عرض إنجازاتك"
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
                f"✅ **{info['name']}**\n"
                f"> {info['description']}"
            )
        else:
            lines.append(
                f"🔒 **{info['name']}**\n"
                f"> {info['description']}"
            )

    embed = discord.Embed(
        title=f"🏅 إنجازات {member.display_name}",
        description="\n\n".join(lines),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed
    )


class EventView(discord.ui.View):

    def __init__(self, event_id):
        super().__init__(timeout=None)

        self.event_id = str(event_id)

        button = discord.ui.Button(
            label="🎉 مشاركة",
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
                "❌ هذه الفعالية غير موجودة.",
                ephemeral=True
            )
            return

        if event["ended"]:
            await interaction.response.send_message(
                "❌ انتهت الفعالية.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        if user_id in event["participants"]:
            await interaction.response.send_message(
                "⚠️ أنت مشارك بالفعل!",
                ephemeral=True
            )
            return

        event["participants"].append(
            user_id
        )

        save_events()

        await interaction.response.send_message(
            "🎉 تم تسجيل مشاركتك في الفعالية!",
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
        "🟢 مفتوحة"
        if not event["ended"]
        else "🔴 انتهت"
    )

    embed = discord.Embed(
        title=f"🎉 {event['title']}",
        description=event["description"],
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🎁 الجائزة",
        value=f"**{event['reward']:,} Credits**",
        inline=True
    )

    embed.add_field(
        name="👥 المشاركون",
        value=f"`{len(event['participants'])}`",
        inline=True
    )

    embed.add_field(
        name="📌 الحالة",
        value=status,
        inline=True
    )

    if not event["ended"]:

        embed.add_field(
            name="⏳ الوقت المتبقي",
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
                    f"🎉 انتهت فعالية **{event['title']}**\n"
                    f"❌ لم يشارك أحد، لذلك لا يوجد فائز."
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
            f"🎉 **انتهت الفعالية!**\n\n"
            f"🏆 الفائز: {winner_text}\n"
            f"💰 الجائزة: **{event['reward']:,} Credits**\n\n"
            f"مبروك! 🎊"
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


@bot.tree.command(
    name="event-create",
    description="إنشاء فعالية مع جائزة Credits"
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
            "❌ مدة الفعالية يجب أن تكون أكبر من صفر.",
            ephemeral=True
        )
        return

    if reward <= 0:
        await interaction.response.send_message(
            "❌ الجائزة يجب أن تكون أكبر من صفر.",
            ephemeral=True
        )
        return

    event_id = str(
        random.randint(
            100000,
            999999
        )
    )

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
        f"✅ تم إنشاء الفعالية!\n"
        f"🆔 ID: `{event_id}`\n"
        f"🎁 الجائزة: **{reward:,} Credits**",
        ephemeral=True
    )

    asyncio.create_task(
        event_timer(event_id)
    )


@bot.tree.command(
    name="event-info",
    description="عرض معلومات فعالية"
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
            "❌ لم يتم العثور على الفعالية.",
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


@bot.tree.command(
    name="event-end",
    description="إنهاء فعالية واختيار الفائز"
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
            "❌ الفعالية غير موجودة.",
            ephemeral=True
        )
        return

    if event["ended"]:
        await interaction.response.send_message(
            "⚠️ الفعالية منتهية بالفعل.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "⏳ جاري إنهاء الفعالية...",
        ephemeral=True
    )

    await finish_event(
        event_id
    )


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
    description="إنشاء بانل عام"
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
        title="📌 Panel",
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
        "✅ تم إنشاء البانل وحفظه بنجاح",
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

    channel_id = message.channel.id
    if str(channel_id) in database["open_tickets"]:
        database["open_tickets"][str(channel_id)]["last_activity"] = str(datetime.now())
        save_database()

    await anti_spam(message)

    guild_id = str(message.guild.id)
    user_id_str = str(message.author.id)
    if guild_id not in xp_data: xp_data[guild_id] = {}
    if user_id_str not in xp_data[guild_id]: xp_data[guild_id][user_id_str] = {"xp": 0, "level": 1}
    
    xp_data[guild_id][user_id_str]["xp"] += 1
    save_json(XP_FILE, xp_data)
    
    if xp_data[guild_id][user_id_str]["xp"] >= xp_data[guild_id][user_id_str]["level"] * 100:
        xp_data[guild_id][user_id_str]["level"] += 1
        save_json(XP_FILE, xp_data)
        await message.channel.send(f"🎉 مبروك {message.author.mention} وصلت للمستوى `{xp_data[guild_id][user_id_str]['level']}`!")

    await bot.process_commands(message)


def has_application(guild_id, user_id):
    for app in applications_data.get(str(guild_id), []):
        if app["user_id"] == user_id and app["status"] == "pending":
            return True
    return False


class ApplyModal(discord.ui.Modal):
    def __init__(self, guild_id, app_type):
        super().__init__(title=f"تقديم {app_type}")
        self.guild_id = str(guild_id)
        self.app_type = app_type

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


class ApplicationControlView(discord.ui.View):
    def __init__(self, user_id, app_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.app_id = app_id

    @discord.ui.button(
        label="قبول",
        emoji="✅",
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
                "❌ لم يتم العثور على التقديم.",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "⚠️ تم اتخاذ قرار بشأن هذا التقديم مسبقًا.",
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
                                    reason="قبول التقديم"
                                )
                            except Exception as e:
                                print(f"Role error: {e}")
                    break

            try:
                await member.send(
                    f"🎉 تم قبول تقديمك!\n"
                    f"📋 نوع التقديم: `{app_type}`"
                )
            except:
                pass

        if interaction.message and interaction.message.embeds:

            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            found = False

            for i, field in enumerate(embed.fields):

                if field.name == "📌 الحالة":

                    embed.set_field_at(
                        i,
                        name="📌 الحالة",
                        value=(
                            "🟢 **مقبول**\n"
                            f"👮 بواسطة: {interaction.user.mention}\n"
                            f"🕐 الوقت: {application['decision_time']}"
                        ),
                        inline=False
                    )

                    found = True
                    break

            if not found:
                embed.add_field(
                    name="📌 الحالة",
                    value=(
                        "🟢 **مقبول**\n"
                        f"👮 بواسطة: {interaction.user.mention}\n"
                        f"🕐 الوقت: {application['decision_time']}"
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
            "✅ تم قبول التقديم وتحديث البانل.",
            ephemeral=True
        )

    @discord.ui.button(
        label="رفض",
        emoji="❌",
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
                "❌ لم يتم العثور على التقديم.",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "⚠️ تم اتخاذ قرار بشأن هذا التقديم مسبقًا.",
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
                    f"❌ تم رفض تقديمك.\n"
                    f"📋 نوع التقديم: `{application.get('type')}`"
                )
            except:
                pass

        if interaction.message and interaction.message.embeds:

            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            found = False

            for i, field in enumerate(embed.fields):

                if field.name == "📌 الحالة":

                    embed.set_field_at(
                        i,
                        name="📌 الحالة",
                        value=(
                            "🔴 **مرفوض**\n"
                            f"👮 بواسطة: {interaction.user.mention}\n"
                            f"🕐 الوقت: {application['decision_time']}"
                        ),
                        inline=False
                    )

                    found = True
                    break

            if not found:
                embed.add_field(
                    name="📌 الحالة",
                    value=(
                        "🔴 **مرفوض**\n"
                        f"👮 بواسطة: {interaction.user.mention}\n"
                        f"🕐 الوقت: {application['decision_time']}"
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
            "❌ تم رفض التقديم وتحديث البانل.",
            ephemeral=True
        )


class ApplicationSelect(discord.ui.Select):
    def __init__(self, guild_id):
        self.guild_id = str(guild_id)
        types = application_types.get(self.guild_id, [])

        options = []
        if isinstance(types, list):
            for t in types:
                if isinstance(t, dict):
                    name = t.get("name")
                    desc = t.get("description", "تقديم جديد")[:100]
                    if name:
                        options.append(discord.SelectOption(label=name, description=desc, emoji="📋"))

        if not options:
            options.append(discord.SelectOption(label="لا يوجد أنواع تقديم متاحة", value="none", emoji="❌"))

        super().__init__(placeholder="📋 اختر نوع التقديم المناسب", options=options, custom_id="application_select_menu")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ لا توجد أنواع تقديم متاحة حالياً.", ephemeral=True)
            return

        app_type = self.values[0]
        if has_application(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("❌ لديك تقديم قيد المراجعة بالفعل.", ephemeral=True)
            return

        await interaction.response.send_modal(ApplyModal(interaction.guild.id, app_type))


class ApplicationSelectView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.add_item(ApplicationSelect(guild_id))


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

    found = False
    new_types = []
    for t in types:
        if isinstance(t, dict) and t.get("name") == name:
            found = True
        else:
            new_types.append(t)

    if not found:
        await interaction.response.send_message("❌ لم يتم العثور على هذا النوع.", ephemeral=True)
        return

    application_types[gid] = new_types
    save_application_types()

    await interaction.response.send_message(f"✅ تم حذف نوع التقديم `{name}` بنجاح.", ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    
    bot.add_view(TicketPanel())
    bot.add_view(TicketButtons())
    
    for channel_id in database["open_tickets"]:
        bot.add_view(RatingView(int(channel_id)))

    for panel in persistent_panels:
        if panel.get("type") == "application":
            bot.add_view(ApplicationSelectView(panel.get("guild_id")))

    for event_id, event in events_data.items():
        if not event.get("ended"):
            bot.add_view(EventView(event_id))

    bot.loop.create_task(auto_close_checker())
    bot.loop.create_task(database_backup())
    bot.loop.create_task(restore_events())

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} Commands")
    except Exception as e:
        print(e)


TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token not found!")
