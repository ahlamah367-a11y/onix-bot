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
# قاعدة البيانات وإعداداتها (التذاكر)
# ==================================

DATABASE_FILE = "tickets_database.json"
BACKUP_FILE = "tickets_backup.json"


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



# ==================================
# أدوات مساعدة وتصميم موحد
# ==================================

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
# إنشاء أنواع التذاكر والأوامر الإدارية
# ==================================

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


# ==================================
# إعدادات البانل والمودال
# ==================================

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


# ==================================
# القوائم والبانل الموحد
# ==================================

class TicketSelect(discord.ui.Select):

    def __init__(self):
        options = []
        for ticket_id, data in database["tickets"].items():
            options.append(
                discord.SelectOption(
                    label=data["name"],
                    value=ticket_id,
                    description=data.get("panel_description", data.get("description", "فتح تذكرة"))[:100],
                    emoji=data.get("emoji", "🎫")
                )
            )

        if not options:
            options.append(discord.SelectOption(label="لا يوجد تذاكر", value="none"))

        super().__init__(
            placeholder="🎫 اختر نوع التذكرة",
            options=options,
            custom_id="ticket_select_menu_secure"
        )

    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]

        if ticket_type == "none":
            await interaction.response.send_message("❌ لا يوجد أنواع تذاكر", ephemeral=True)
            return

        user_id = interaction.user.id
        ticket_settings = database["tickets"].get(ticket_type)

        for t in database["open_tickets"].values():
            if t["owner"] == user_id:
                await interaction.response.send_message(
                    "❌ لديك تذكرة مفتوحة بالفعل",
                    ephemeral=True
                )
                return

        opened_count = 0
        for t in database["open_tickets"].values():
            if t.get("owner") == user_id:
                opened_count += 1

        if ticket_settings and opened_count >= ticket_settings.get("max_tickets", 1):
            await interaction.response.send_message(
                "❌ وصلت الحد الأقصى من التذاكر المفتوحة",
                ephemeral=True
            )
            return

        if ticket_settings:
            user_roles = [r.id for r in interaction.user.roles]

            for role in ticket_settings.get("blocked_roles", []):
                if role in user_roles:
                    await interaction.response.send_message(
                        "❌ لا يمكنك فتح هذه التذكرة",
                        ephemeral=True
                    )
                    return

        if ticket_settings and ticket_settings.get("prevent_same_type", True):
            for t in database["open_tickets"].values():
                if t.get("owner") == user_id and t["type"] == ticket_type:
                    await interaction.response.send_message("❌ لديك تذكرة مفتوحة من نفس النوع بالفعل", ephemeral=True)
                    return

        if ticket_settings and ticket_settings.get("ask_reason"):
            await interaction.response.send_modal(TicketFormModal(ticket_type))
            return

        await create_ticket(interaction, ticket_type, None)



class TicketPanel(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())



@bot.tree.command(
    name="send-ticket-panel",
    description="إرسال بانل التذاكر الموحد"
)
async def send_ticket_panel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ هذا الأمر مخصص للمشرفين فقط",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    panel = database["panel"]

    old_message_id = database["panel"].get("message_id")

    if old_message_id:
        try:
            old_message = await interaction.channel.fetch_message(old_message_id)
            await old_message.delete()
        except:
            pass


    embed = discord.Embed(
        title=panel["title"],
        description=panel["description"],
        color=discord.Color.blue()
    )

    if panel["image"]:
        embed.set_image(url=panel["image"])


    message = await interaction.channel.send(
        embed=embed,
        view=TicketPanel()
    )


    database["panel"]["message_id"] = message.id
    database["panel"]["channel"] = interaction.channel.id
    save_database()


    await interaction.followup.send(
        "✅ تم إرسال بانل التذاكر الجديد",
        ephemeral=True
    )


# ==================================
# نظام نماذج التذاكر (Ticket Forms)
# ==================================

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


# ==================================
# نظام فتح التذاكر والترانسكريبت
# ==================================

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


# ==================================
# أزرار وأدوات داخل التذكرة
# ==================================

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
            await interaction.response.send_message("❌ ليس لديك صلاحية لاستلام التذكرة", ephemeral=True)
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


# ==================================
# نظام التقييم والإغلاق
# ==================================

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


# ==================================
# أوامر الإدارة داخل التذكرة (تم تعديل الأسماء لتجنب التكرار)
# ==================================

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



@bot.tree.command(name="ticket-lock", description="قفل الكتابة في التذكرة")
async def ticket_lock(interaction: discord.Interaction):
    if not check_staff(interaction):
        await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
        return

    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل التذكرة")



@bot.tree.command(name="ticket-unlock", description="فتح الكتابة في التذكرة")
async def ticket_unlock(interaction: discord.Interaction):
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


# ==================================
# إعدادات التذكرة المخصصة
# ==================================

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
# أوامر الإدارة والرومات العامة (Clear, Lock, Unlock, Slowmode)
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
# نظام Anti-Spam التلقائي والأوامر المخصصة و Background Tasks
# ==================================

user_message_timestamps = {}
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


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    channel_id = message.channel.id
    if str(channel_id) in database["open_tickets"]:
        database["open_tickets"][str(channel_id)]["last_activity"] = str(datetime.now())
        save_database()

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



@bot.event
async def on_guild_channel_delete(channel):
    if str(channel.id) in database["open_tickets"]:
        database["open_tickets"].pop(str(channel.id))
        database["stats"]["total_closed"] += 1
        save_database()


# ==================================
# تشغيل البوت واستقرار الـ Persistent Views
# ==================================

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    
    bot.add_view(TicketPanel())
    bot.add_view(TicketButtons())
    
    for channel_id in database["open_tickets"]:
        bot.add_view(RatingView(int(channel_id)))

    bot.loop.create_task(auto_close_checker())
    bot.loop.create_task(database_backup())

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
