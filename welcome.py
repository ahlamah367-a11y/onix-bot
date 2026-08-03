import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
import os
import random
import asyncio
import re


app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # استخدام البورت الذي يحدده Render تلقائياً، وإذا لم يوجد يستخدم 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- إعدادات البوت والـ Intents ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# الأيديات المحددة
WELCOME_CHANNEL_ID = 1532952608363516025  # روم الترحيب
RULES_CHANNEL_ID = 1532951546193772554     # روم القوانين
NEWS_CHANNEL_ID = 1532952352250925056      # روم الأخبار
GIVEAWAY_CHANNEL_ID = 1532946535363510292  # روم الهدايا
GUILD_ID = 1532326696714240062             # آيدي السيرفر

@bot.event
async def on_ready():
    print(f"ONIX BOT تم تشغيل البوت بنجاح: {bot.user.name}")
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print("تم مزامنة أوامر السلاش بنجاح!")
    except Exception as e:
        print(f"خطأ في مزامنة الأوامر: {e}")

# --- نظام الترحيب ---
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        member_number = member.guild.member_count

        rules_link = f"<#{RULES_CHANNEL_ID}>"
        news_link = f"<#{NEWS_CHANNEL_ID}>"
        giveaway_link = f"<#{GIVEAWAY_CHANNEL_ID}>"

        text_content = (
            f"• أهلاً بك في سيرفر **{member.guild.name}**\n"
            f"• أنرت السيرفر يا {member.mention}\n\n"
            f"• ترتيبك بين الأعضاء: **{member_number}**\n\n"
            f"• يرجى قراءة القوانين والالتزام بها:\n"
            f"{rules_link}\n\n"
            f"• تابع آخر أخبار السيرفر:\n"
            f"{news_link}\n\n"
            f"• لا تفوتك آخر الهدايا والقيم:\n"
            f"{giveaway_link}"
        )

        embed = discord.Embed(color=discord.Color.from_rgb(30, 30, 30))
        embed.add_field(name="✨ 𝙾𝙽𝙸𝚇 𝙲𝙾𝙼𝙼𝚄𝙽𝙸𝚃𝚈 ✨", value="Welcome to our family", inline=False)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)

        await channel.send(content=text_content, embed=embed)

# --- نظام القيف أواي (Giveaway) ---
def parse_duration(duration_str: str) -> int:
    duration_str = duration_str.lower().strip()
    match = re.match(r"^(\d+)\s*([smhd]?)$", duration_str)
    if not match:
        return 0

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == 's':
        return amount
    elif unit == 'm':
        return amount * 60
    elif unit == 'h':
        return amount * 3600
    elif unit == 'd':
        return amount * 86400
    else:
        return amount

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="المشاركة في السحب", style=discord.ButtonStyle.secondary, custom_id="join_giveaway_btn")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("أنت مشارك مسبقاً في هذا السحب بالفعل.", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("تم تسجيل مشاركتك بنجاح. بالتوفيق.", ephemeral=True)

@bot.tree.command(name="giveaway", description="إنشاء مسابقة قيف أواي مع سحب تلقائي للفائز")
@app_commands.describe(prize="اسم الجائزة أو تفاصيلها", duration="مدة السحب (مثال: 30s للثواني، 1m للدقائق)")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway_slash(interaction: discord.Interaction, prize: str, duration: str = "30s"):
    channel = interaction.guild.get_channel(GIVEAWAY_CHANNEL_ID)
    if not channel:
        channel = interaction.channel

    seconds = parse_duration(duration)
    if seconds <= 0:
        seconds = 30

    embed = discord.Embed(
        title="GIVEAWAY",
        description=(
            f"### 🎁 الجائزة\n"
            f"> **{prize}**\n\n"
            f"### ⏳ المدة\n"
            f"> `{duration}`\n\n"
            f"### 👤 الإشراف\n"
            f"> {interaction.user.mention}\n\n"
            f"اضغط على الزر أدناه للمشاركة في السحب."
        ),
        color=discord.Color.from_rgb(20, 20, 20)
    )
    embed.set_footer(text="ONIX Community")

    view = GiveawayView()
    message = await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ تم نشر القيف أواي بنجاح في روم <#{channel.id}> وسيتم السحب بعد `{duration}`!", ephemeral=True)

    await asyncio.sleep(seconds)

    for child in view.children:
        child.disabled = True

    try:
        await message.edit(view=view)
    except:
        pass

    if view.participants:
        winner_id = random.choice(list(view.participants))
        winner = interaction.guild.get_member(winner_id)
        winner_text = winner.mention if winner else f"<@{winner_id}>"

        result_embed = discord.Embed(
            title="GIVEAWAY ENDED",
            description=(
                f"### 🎁 الجائزة\n"
                f"> **{prize}**\n\n"
                f"### 🏆 الفائز\n"
                f"> مبروك {winner_text}!\n\n"
                f"تم اختيار الفائز عشوائياً من بين `{len(view.participants)}` مشارك."
            ),
            color=discord.Color.from_rgb(20, 20, 20)
        )
        result_embed.set_footer(text="ONIX Community")
        await channel.send(content=f"🎉 تهانينا {winner_text}! لقد فزت بـ **{prize}**!", embed=result_embed)
    else:
        await channel.send(f"❌ انتهى القيف أواي لـ **{prize}**، للأسف لم يشارك أي أحد في السحب!")

# --- نظام الـ Panel العادي ---
class CustomPanelView(discord.ui.View):
    def __init__(self, response_text: str):
        super().__init__(timeout=None)
        self.response_text = response_text

    @discord.ui.button(label="زر تفاعلي", style=discord.ButtonStyle.secondary, custom_id="custom_panel_btn")
    async def panel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.response_text, ephemeral=True)

@bot.tree.command(name="panel", description="إنشاء بانل مخصص داخل إيمبد أنيق وهادئ")
@app_commands.describe(
    description="وصف البانل داخل الإيمبد",
    button_label="اسم الزر",
    button_message="الرسالة التي تظهر عند الضغط على الزر"
)
@app_commands.checks.has_permissions(administrator=True)
async def panel_slash(interaction: discord.Interaction, description: str, button_label: str, button_message: str):
    embed = discord.Embed(
        title="CONTROL PANEL",
        description=f"> {description}",
        color=discord.Color.from_rgb(20, 20, 20)
    )
    embed.set_footer(text="ONIX Community")

    view = CustomPanelView(response_text=button_message)
    for child in view.children:
        if child.custom_id == "custom_panel_btn":
            child.label = button_label

    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ تم إنشاء البانل بنجاح داخل الإيمبد!", ephemeral=True)

# --- نظام التكتات المتكامل (Tickets) ---
class TicketCloseView(discord.ui.View):
    def __init__(self, admin_role_id: int):
        super().__init__(timeout=None)
        self.admin_role_id = admin_role_id

    @discord.ui.button(label="إغلاق التكت", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id == self.admin_role_id for role in interaction.user.roles)
        if not is_admin and interaction.user.name not in interaction.channel.name:
            await interaction.response.send_message("ليس لديك صلاحية لإغلاق هذه التذكرة!", ephemeral=True)
            return
        
        await interaction.response.send_message("جاري إغلاق التذكرة...")
        await interaction.channel.delete()

class TicketPanelView(discord.ui.View):
    def __init__(self, ticket_name_format, open_category, admin_role, welcome_message, mention_target, close_category, lock_channel):
        super().__init__(timeout=None)
        self.ticket_name_format = ticket_name_format
        self.open_category = open_category
        self.admin_role = admin_role
        self.welcome_message = welcome_message
        self.mention_target = mention_target
        self.close_category = close_category
        self.lock_channel = lock_channel

    @discord.ui.button(label="فتح تذكرة", style=discord.ButtonStyle.success, custom_id="open_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=not self.lock_channel),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel_name = self.ticket_name_format.replace("{user}", user.name)

        ticket_channel = await guild.create_text_channel(
            name=ticket_channel_name,
            category=self.open_category,
            overwrites=overwrites
        )

        mentions_text = f"{user.mention} {self.admin_role.mention}"
        if self.mention_target:
            mentions_text += f" {self.mention_target}"

        embed = discord.Embed(title="تذكرة جديدة", description=self.welcome_message, color=discord.Color.blue())
        view = TicketCloseView(admin_role_id=self.admin_role.id)
        await ticket_channel.send(content=mentions_text, embed=embed, view=view)
        await interaction.response.send_message(f"تم إنشاء تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)


@bot.tree.command(name="setup-ticket", description="إنشاء بانل التكتات بكامل الخيارات")
@app_commands.describe(
    panel_room="روم إرسال البانل",
    panel_description="وصف داخل البانل",
    button_name="اسم زر البانل",
    open_category="كاتجوري مكان التكتات المفتوحة",
    close_category="كاتجوري التكت المغلقة",
    lock_channel="قفل الروم داخل التكت يظهر فقط للي له صلاحية",
    ticket_name="اسم التذكرة",
    admin_role="رتبة مسؤول الإدارة",
    welcome_message="رسالة التي ترسل داخل التذكرة",
    panel_image_emoji="رابط الصورة أو الإيموجي للبانل",
    mentions="تحديد منشن الرتب أو الأشخاص عند فتح التذكرة"
)
async def setup_ticket(
    interaction: discord.Interaction,
    panel_room: discord.TextChannel,
    panel_description: str,
    button_name: str,
    open_category: discord.CategoryChannel,
    close_category: discord.CategoryChannel,
    lock_channel: bool,
    ticket_name: str,
    admin_role: discord.Role,
    welcome_message: str,
    panel_image_emoji: str = None,
    mentions: str = None
):
    embed = discord.Embed(description=panel_description, color=discord.Color.green())
    if panel_image_emoji:
        if panel_image_emoji.startswith("http"):
            embed.set_image(url=panel_image_emoji)
        else:
            embed.set_thumbnail(url=panel_image_emoji)

    class CustomTicketPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
        super().__init__(timeout=None)

    @discord.ui.button(label=button_name, style=discord.ButtonStyle.primary, custom_id="custom_open_ticket_btn")
    async def custom_open(self, inter: discord.Interaction, button: discord.ui.Button):
        view_logic = TicketPanelView(
            ticket_name_format=ticket_name,
            open_category=open_category,
            admin_role=admin_role,
            welcome_message=welcome_message,
            mention_target=mentions,
            close_category=close_category,
            lock_channel=lock_channel
        )
        await view_logic.create_ticket(inter)

    await interaction.response.send_message("تم إنشاء بانل التكتات بنجاح!", ephemeral=True)

# --- تشغيل البوت النهائي ---
bot.run(os.getenv("DISCORD_TOKEN"))
