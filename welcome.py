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

class TicketCloseView(discord.ui.View):
    def __init__(self, admin_role_id: int, ticket_logs_channel: discord.TextChannel = None, tqeem_room: discord.TextChannel = None):
        super().__init__(timeout=None)
        self.admin_role_id = admin_role_id
        self.ticket_logs_channel = ticket_logs_channel
        self.tqeem_room = tqeem_room

    @discord.ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id == self.admin_role_id for role in interaction.user.roles)
        if not is_admin and interaction.user.name not in interaction.channel.name:
            await interaction.response.send_message("ليس لديك صلاحية لإغلاق هذه التذكرة!", ephemeral=True)
            return
        
        await interaction.response.send_message("⏳ جاري إغلاق التذكرة وحفظ السجلات...")
        
        if self.ticket_logs_channel:
            log_embed = discord.Embed(
                title="🔒 سجل إغلاق تذكرة",
                description=f"> **المشرف:** {interaction.user.mention}\n> **اسم الروم:** `{interaction.channel.name}`",
                color=discord.Color.from_rgb(20, 20, 20)
            )
            try:
                await self.ticket_logs_channel.send(embed=log_embed)
            except:
                pass

        if self.tqeem_room:
            try:
                await self.tqeem_room.send(f"⭐ تقييم خدمة الدعم المقدمة من {interaction.user.mention} في التذكرة المغلقة (`{interaction.channel.name}`).")
            except:
                pass

        await asyncio.sleep(1.5)
        await interaction.channel.delete()

class TicketCoreHandler:
    @staticmethod
    async def create_ticket(
        interaction: discord.Interaction,
        ticket_name_format,
        open_category,
        admin_role,
        welcome_message,
        mention_target,
        close_category,
        ticket_logs,
        tqeem_room,
        ownership,
        reason,
        username_number,
        admin_perm,
        welcome_image,
        line_url
    ):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        if username_number and "رقم" in username_number.lower():
            ticket_suffix = str(random.randint(1000, 9999))
        else:
            ticket_suffix = user.name

        ticket_channel_name = ticket_name_format.replace("{user}", ticket_suffix)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        if admin_perm:
            overwrites[admin_perm] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=ticket_channel_name,
            category=open_category,
            overwrites=overwrites
        )

        mentions_text = f"{user.mention} {admin_role.mention}"
        if mention_target:
            mentions_text += f" {mention_target}"

        # تنسيق إيمبد التذكرة بشكل فخم ونظيف بدون أي روابط نصية ظاهرة
        embed = discord.Embed(
            title="❖ 𝙾𝙽𝙸𝚇 🭠 𝓣𝓲𝓬𝓴𝓮𝓽",
            description=f"> {welcome_message}",
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        if reason and "تفعيل" in reason.lower():
            embed.add_field(name="📌 حالة الطلب", value="> قيد المراجعة والانتظار", inline=False)

        if ownership and "تفعيل" in ownership.lower():
            embed.add_field(name="🛡️ تنبيه الإدارة", value=f"> تم استدعاء المسؤولين بواسطة {user.mention}", inline=False)

        # جعل الصورة تظهر بشكل احترافي داخل الإيمبد بدون رابط نصي مزعج
        if welcome_image:
            embed.set_image(url=welcome_image)
            
        embed.set_footer(text="ONIX Community • Secure Ticket System", icon_url=guild.icon.url if guild.icon else None)

        view = TicketCloseView(
            admin_role_id=admin_role.id,
            ticket_logs_channel=ticket_logs,
            tqeem_room=tqeem_room
        )

        if line_url:
            await ticket_channel.send(line_url)

        await ticket_channel.send(content=mentions_text, embed=embed, view=view)
        
        followup_msg = f"✅ تم فتح تذكرتك بنجاح: {ticket_channel.mention}"
        if ownership and "تفعيل" in ownership.lower():
            followup_msg += " (تم استدعاء الأونرشيب)"

        await interaction.followup.send(followup_msg, ephemeral=True)

class TicketSelectDropdown(discord.ui.Select):
    def __init__(self, options_data):
        discord_options = []
        self.tickets_config = options_data
        
        for item in options_data:
            discord_options.append(
                discord.SelectOption(
                    label=item["label"],
                    description="اضغط هنا لفتح هذا القسم المخصص",
                    emoji="🎫"
                )
            )
            
        super().__init__(placeholder=" اضغط هنا لاختيار نوع التذكرة...", min_values=1, max_values=1, options=discord_options, custom_id="custom_ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        selected_label = self.values[0]
        config = next((item for item in self.tickets_config if item["label"] == selected_label), None)
        
        if not config:
            await interaction.response.send_message("حدث خطأ في اختيار التذكرة.", ephemeral=True)
            return

        await TicketCoreHandler.create_ticket(
            interaction=interaction,
            ticket_name_format=config["ticket"],
            open_category=config["category"],
            admin_role=config["role"],
            welcome_message=config["welcome_msg"],
            mention_target=config["mentions"],
            close_category=config["close_category"],
            ticket_logs=config["ticket_logs"],
            tqeem_room=config["tqeem_room"],
            ownership=config["ownership"],
            reason=config["reason"],
            username_number=config["username_number"],
            admin_perm=config["admin"],
            welcome_image=config["welcome_image"],
            line_url=config["line"]
        )

class MultiTicketPanelView(discord.ui.View):
    def __init__(self, options_data):
        super().__init__(timeout=None)
        self.add_item(TicketSelectDropdown(options_data))

@bot.tree.command(name="ticket-setup", description="إنشاء بانل التكتات الأنيق مع تحديد الخيارات")
@app_commands.describe(
    panel_description="وصف البانل داخل الإيمبد الرئيسي",
    ticket_label="اسم الخيار بالقائمة (مثال: الدعم الفني / إبلاغ عن مشكلة)",
    ticket="اسم التذكرة (مثال: support-{user})",
    category="كاتجوري التذاكر الجديدة",
    role="الرول الخاصة بادارة التذكرة",
    ticket_logs="روم ارسال التذاكر المغلقة (Logs)",
    close_catejory="كاتجوري التكتات المغلقة",
    tqeem_room="روم ارسال تقييم مستلم التذكرة",
    ownership="تفعيل أو إلغاء استدعاء الأونرشيب",
    reason="تفعيل أو إلغاء سبب فتح التذكرة",
    username_number="اسم التذكرة يوزر العضو أم رقم؟",
    admin="رتبة مسؤول الادمنية",
    welcome_msg="الرسالة التي ترسل داخل التذكرة",
    welcome_image="رابط الصورة داخل التذكرة (تظهر بداخل الإيمبد بشكل أنيق)",
    mentions="تحديد منشن الرتب أو الأشخاص عند فتح التذكرة",
    line="تعيين رابط صورة الخط (Line)"
)
async def ticket_setup(
    interaction: discord.Interaction,
    panel_description: str,
    ticket_label: str,
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
    options_data = [
        {
            "label": ticket_label,
            "ticket": ticket,
            "category": category,
            "role": role,
            "ticket_logs": ticket_logs,
            "close_category": close_catejory,
            "tqeem_room": tqeem_room,
            "ownership": ownership,
            "reason": reason,
            "username_number": username_number,
            "admin": admin,
            "welcome_msg": welcome_msg,
            "welcome_image": welcome_image,
            "mentions": mentions,
            "line": line
        }
    ]

    embed = discord.Embed(
        title="✨ 𝙾𝙽𝙸𝚇 𝙲𝙾𝙼𝙼𝚄𝙽𝙸𝚃𝚈 • 🎫 𝓣𝓲𝓬𝓴𝓮𝓽𝓼 ✨",
        description=f"> {panel_description}",
        color=discord.Color.from_rgb(15, 15, 15)
    )
    if welcome_image:
        embed.set_image(url=welcome_image)
    embed.set_footer(text="اختر من القائمة أدناه ما يناسب طلبك وسيقوم النظام بخدمتك.")

    view = MultiTicketPanelView(options_data)

    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✨ تم نشر بانل التكتات الأنيق بنجاح!", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
