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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL_ID = 1532952608363516025
RULES_CHANNEL_ID = 1532951546193772554
NEWS_CHANNEL_ID = 1532952352250925056
GIVEAWAY_CHANNEL_ID = 1532946535363510292
GUILD_ID = 1532326696714240062

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

class TicketCloseView(discord.ui.View):
    def __init__(self, admin_role_id: int, ticket_logs_channel: discord.TextChannel = None, tqeem_room: discord.TextChannel = None):
        super().__init__(timeout=None)
        self.admin_role_id = admin_role_id
        self.ticket_logs_channel = ticket_logs_channel
        self.tqeem_room = tqeem_room

    @discord.ui.button(label="إغلاق التكت", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id == self.admin_role_id for role in interaction.user.roles)
        if not is_admin and interaction.user.name not in interaction.channel.name:
            await interaction.response.send_message("ليس لديك صلاحية لإغلاق هذه التذكرة!", ephemeral=True)
            return
        
        await interaction.response.send_message("جاري إغلاق التذكرة وحفظ السجلات...")
        
        # إرسال سجل الإغلاق لوجد روم اللوجز
        if self.ticket_logs_channel:
            log_embed = discord.Embed(
                title="🔒 إغلاق تذكرة",
                description=ف"تم إغلاق التذكرة بواسطة: {interaction.user.mention}\nاسم الروم: `{interaction.channel.name}`",
                color=discord.Color.red()
            )
            try:
                await self.ticket_logs_channel.send(embed=log_embed)
            except:
                pass

        # إرسال رابط التقييم لو وجد روم التقييم
        if self.tqeem_room:
            try:
                await self.tqeem_room.send(f"⭐ تقييم خدمة الدعم المقدمة من {interaction.user.mention} في التذكرة المغلقة.")
            except:
                pass

        await interaction.channel.delete()

class TicketPanelView(discord.ui.View):
    def __init__(self, ticket_name_format, open_category, admin_role, welcome_message, mention_target, close_category, lock_channel, ticket_logs, tqeem_room, ownership, reason, username_number, admin_perm, welcome_image, line_url):
        super().__init__(timeout=None)
        self.ticket_name_format = ticket_name_format
        self.open_category = open_category
        self.admin_role = admin_role
        self.welcome_message = welcome_message
        self.mention_target = mention_target
        self.close_category = close_category
        self.lock_channel = lock_channel
        self.ticket_logs = ticket_logs
        self.tqeem_room = tqeem_room
        self.ownership = ownership
        self.reason = reason
        self.username_number = username_number
        self.admin_perm = admin_perm
        self.welcome_image = welcome_image
        self.line_url = line_url

    async def create_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        # تحديد التسمية بناءً على خيار (يوزر العضو أم رقم)
        if self.username_number and "رقم" in self.username_number.lower():
            # توليد رقم عشوائي أو تسلسلي بسيط
            ticket_suffix = str(random.randint(1000, 9999))
        else:
            ticket_suffix = user.name

        ticket_channel_name = self.ticket_name_format.replace("{user}", ticket_suffix)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=not self.lock_channel),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        if self.admin_perm:
            # تخصيص إضافي لرتبة مسؤول الأدمنية لو وجدت
            overwrites[self.admin_perm] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=ticket_channel_name,
            category=self.open_category,
            overwrites=overwrites
        )

        mentions_text = f"{user.mention} {self.admin_role.mention}"
        if self.mention_target:
            mentions_text += f" {self.mention_target}"

        # تجهيز الرسالة الترحيبية والإيمبد
        embed = discord.Embed(title="تذكرة جديدة", description=self.welcome_message, color=discord.Color.from_rgb(30, 30, 30))
        if self.welcome_image:
            embed.set_image(url=self.welcome_image)

        view = TicketCloseView(
            admin_role_id=self.admin_role.id,
            ticket_logs_channel=self.ticket_logs,
            tqeem_room=self.tqeem_room
        )

        # إرسال الخط (Line) لو تم توفيره
        if self.line_url:
            await ticket_channel.send(self.line_url)

        await ticket_channel.send(content=mentions_text, embed=embed, view=view)
        await interaction.followup.send(f"تم إنشاء تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)

class CustomTicketPanelView(discord.ui.View):
    def __init__(self, ticket_name, open_category, admin_role, welcome_message, mentions, close_category, lock_channel, button_name, ticket_logs, tqeem_room, ownership, reason, username_number, admin_perm, welcome_image, line_url):
        super().__init__(timeout=None)
        self.ticket_name = ticket_name
        self.open_category = open_category
        self.admin_role = admin_role
        self.welcome_message = welcome_message
        self.mentions = mentions
        self.close_category = close_category
        self.lock_channel = lock_channel
        self.ticket_logs = ticket_logs
        self.tqeem_room = tqeem_room
        self.ownership = ownership
        self.reason = reason
        self.username_number = username_number
        self.admin_perm = admin_perm
        self.welcome_image = welcome_image
        self.line_url = line_url

        self.add_item(CustomTicketButton(button_name))

class CustomTicketButton(discord.ui.Button):
    def __init__(self, button_name):
        super().__init__(label=button_name, style=discord.ButtonStyle.primary, custom_id="custom_open_ticket_btn")

    async def callback(self, interaction: discord.Interaction):
        view_logic = TicketPanelView(
            ticket_name_format=self.view.ticket_name,
            open_category=self.view.open_category,
            admin_role=self.view.admin_role,
            welcome_message=self.view.welcome_message,
            mention_target=self.view.mentions,
            close_category=self.view.close_category,
            lock_channel=self.view.lock_channel,
            ticket_logs=self.view.ticket_logs,
            tqeem_room=self.view.tqeem_room,
            ownership=self.view.ownership,
            reason=self.view.reason,
            username_number=self.view.username_number,
            admin_perm=self.view.admin_perm,
            welcome_image=self.view.welcome_image,
            line_url=self.view.line_url
        )
        await view_logic.create_ticket(interaction)

@bot.tree.command(name="ticket-setup", description="إنشاء بانل التكتات بكامل الخيارات المتقدمة")
@app_commands.describe(
    ticket="اسم التذكرة (مثال: support-{user})",
    category="كاتجوري التذاكر الجديدة",
    role="الرول الخاصة بادارة التذكرة",
    ticket_logs="روم ارسال التذاكر المغلقة (Logs)",
    close_catejory="كاتجوري التكتات المغلقة",
    tqeem_room="روم ارسال تقييم مستلم التذكرة",
    ownership="تفعيل استدعاء الاونر شيب او الغاءه",
    reason="سبب فتح التذكرة تفعيل او الغاء",
    username_number="اسم التذكرة يوزر العضو ام رقم؟",
    admin="رتبة مسؤول الادمنية",
    welcome_msg="الرسالة التي ترسل داخل التذكرة",
    welcome_image="رابط الصورة التي ترسل داخل التذكرة",
    mentions="تحديد منشن الرتب او الاشخاص عند فتح تذكرة",
    line="تعيين رابط صورة الخط (Line)"
)
async def ticket_setup(
    interaction: discord.Interaction,
    ticket: str,
    category: discord.CategoryChannel,
    role: discord.Role,
    ticket_logs: discord.TextChannel,
    close_catejory: discord.CategoryChannel,
    tqeem_room: discord.TextChannel,
    ownership: str,
    reason: str,
    username_number: str,
    admin: discord.Role,
    welcome_msg: str,
    welcome_image: str = None,
    mentions: str = None,
    line: str = None
):
    embed = discord.Embed(
        title="✨ Ticket System Panel ✨",
        description="اضغط على الزر أدناه لفتح تذكرة جديدة ومراسلة الإدارة.",
        color=discord.Color.from_rgb(20, 20, 20)
    )
    if welcome_image:
        embed.set_thumbnail(url=welcome_image)

    view = CustomTicketPanelView(
        ticket_name=ticket,
        open_category=category,
        admin_role=role,
        welcome_message=welcome_msg,
        mentions=mentions,
        close_category=close_catejory,
        lock_channel=True,
        button_name="فتح تذكرة",
        ticket_logs=ticket_logs,
        tqeem_room=tqeem_room,
        ownership=ownership,
        reason=reason,
        username_number=username_number,
        admin_perm=admin,
        welcome_image=welcome_image,
        line_url=line
    )

    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ تم إعداد ونشر بانل التكتات بكامل الخيارات بنجاح!", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
