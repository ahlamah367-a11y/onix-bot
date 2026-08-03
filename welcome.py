import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import os
import random
import asyncio
from datetime import datetime, timedelta

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

GUILD_ID = 1532326696714240062

ping_channel_id = None
# تم تثبيت روم الترحيب تلقائياً على الرابط الذي أرسلته
welcome_channel_id = 1532952608363516025

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
    
    if not auto_ping_task.is_running():
        auto_ping_task.start()

@tasks.loop(minutes=5)
async def auto_ping_task():
    global ping_channel_id
    if ping_channel_id:
        channel = bot.get_channel(ping_channel_id)
        if channel:
            try:
                await channel.send("🏓 **ONIX BOT Ping Check:** البوت يعمل بكفاءة عالية ومتصل بنجاح! ✨")
            except Exception as e:
                print(f"خطأ في إرسال الـ Ping: {e}")

# ==================== نظام الترحيب الثابت مع صورة بروفايل العضو والروابط الصحيحة ====================
@bot.event
async def on_member_join(member: discord.Member):
    global welcome_channel_id
    if welcome_channel_id:
        channel = bot.get_channel(welcome_channel_id)
        if channel:
            description_text = (
                f"> أهلاً بك في سيرفر **ONIX COMMUNITY**\n"
                f"> أنرت السيرفر يا {member.mention}\n\n"
                f"> ترتيبك بين الأعضاء: **{member.guild.member_count}**\n\n"
                f"> يرجى قراءة القوانين والالتزام بها:\n"
                f"> <#1532951546193772554> **· 🟪 「 القوانين 」**\n\n"
                f"> تابع آخر أخبار السيرفر:\n"
                f"> <#1532326696714240062> **· 📢 「 اخبار 」**\n\n"
                f"> لا تفوتك آخر الهدايا والقيم:\n"
                f"> <#1532952352250925056> **· 🎁 「 الهدايا 」**"
            )

            embed = discord.Embed(
                description=description_text,
                color=discord.Color.from_rgb(15, 15, 15)
            )
            
            # وضع صورة بروفايل العضو الذي انضم كصورة مصغرة للإيمبد
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="✨ ONIX COMMUNITY ✨\nWelcome to our family")
                
            try:
                await channel.send(content=f"welcome {member.mention}", embed=embed)
            except Exception as e:
                print(f"خطأ في إرسال الترحيب: {e}")

@bot.tree.command(name="set-welcome", description="تحديد روم الترحيب بالأعضاء الجدد")
@app_commands.describe(channel="اختر الروم المخصص للترحيب")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    global welcome_channel_id
    welcome_channel_id = channel.id
    await interaction.response.send_message(f"✅ تم تحديد روم الترحيب بنجاح: {channel.mention}", ephemeral=True)

# ==================== نظام التذاكر والبانل المستقل ====================
class SingleTicketButtonView(discord.ui.View):
    def __init__(self, button_label: str, button_desc: str):
        super().__init__(timeout=None)
        self.button_label = button_label
        self.button_desc = button_desc

    @discord.ui.button(label="🎫 فتح تذكرة", style=discord.ButtonStyle.blurple, custom_id="single_panel_ticket_btn")
    async def open_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"✅ تم استلام طلبك عبر زر: **{self.button_label}**\n> {self.button_desc}", ephemeral=True)

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

        embed = discord.Embed(
            title="❖ 𝙾𝙽𝙸𝚇 🭠 𝓣𝓲𝓬𝓴𝓮𝓽",
            description=f"> {welcome_message}",
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        if reason and "تفعيل" in reason.lower():
            embed.add_field(name="📌 حالة الطلب", value="> قيد المراجعة والانتظار", inline=False)

        if ownership and "تفعيل" in ownership.lower():
            embed.add_field(name="🛡️ تنبيه الإدارة", value=f"> تم استدعاء المسؤولين بواسطة {user.mention}", inline=False)

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
                    description=item["description"],
                    emoji=item["emoji"]
                )
            )
            
        super().__init__(placeholder="اضغط هنا لاختيار قسم التذكرة المناسب...", min_values=1, max_values=1, options=discord_options, custom_id="multi_ticket_dropdown_system")

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

@bot.tree.command(name="ticket-setup", description="إنشاء بانل تكتات متطور يحتوي على خيارات متعددة")
@app_commands.describe(
    panel_description="وصف البانل العام داخل الإيمبد",
    welcome_image="رابط صورة البانل الرئيسية",
    label_1="اسم الخيار الأول بالقائمة",
    desc_1="وصف الخيار الأول",
    emoji_1="إيموجي الخيار الأول",
    ticket_1="اسم تذكرة الخيار الأول",
    category_1="كاتجوري الخيار الأول",
    role_1="رول إدارة الخيار الأول",
    label_2="اسم الخيار الثاني (اختياري)",
    desc_2="وصف الخيار الثاني",
    emoji_2="إيموجي الخيار الثاني",
    ticket_2="اسم تذكرة الخيار الثاني",
    category_2="كاتجوري الخيار الثاني",
    role_2="رول إدارة الخيار الثاني",
    ticket_logs="روم السجلات",
    close_catejory="كاتجوري المغلقة",
    tqeem_room="روم التقييم",
    ownership="استدعاء الأونرشيب؟",
    reason="سبب فتح التذكرة؟",
    username_number="يوزر العضو أم رقم؟",
    admin="رتبة مسؤول الادمنية",
    welcome_msg="رسالة الترحيب",
    mentions="منشنات إضافية",
    line="رابط الخط"
)
async def ticket_setup(
    interaction: discord.Interaction,
    panel_description: str,
    label_1: str,
    desc_1: str,
    emoji_1: str,
    ticket_1: str,
    category_1: discord.CategoryChannel,
    role_1: discord.Role,
    ticket_logs: discord.TextChannel,
    close_catejory: discord.CategoryChannel,
    tqeem_room: discord.TextChannel,
    ownership: str,
    reason: str,
    username_number: str,
    admin: discord.Role,
    welcome_msg: str,
    label_2: str = None,
    desc_2: str = None,
    emoji_2: str = None,
    ticket_2: str = None,
    category_2: discord.CategoryChannel = None,
    role_2: discord.Role = None,
    welcome_image: str = None,
    mentions: str = None,
    line: str = None
):
    options_data = [
        {
            "label": label_1, "description": desc_1, "emoji": emoji_1, "ticket": ticket_1,
            "category": category_1, "role": role_1, "ticket_logs": ticket_logs,
            "close_category": close_catejory, "tqeem_room": tqeem_room, "ownership": ownership,
            "reason": reason, "username_number": username_number, "admin": admin,
            "welcome_msg": welcome_msg, "welcome_image": welcome_image, "mentions": mentions, "line": line
        }
    ]

    if label_2 and ticket_2 and category_2 and role_2:
        options_data.append({
            "label": label_2, "description": desc_2 or "قسم مخصص", "emoji": emoji_2 or "📌", "ticket": ticket_2,
            "category": category_2, "role": role_2, "ticket_logs": ticket_logs,
            "close_category": close_catejory, "tqeem_room": tqeem_room, "ownership": ownership,
            "reason": reason, "username_number": username_number, "admin": admin,
            "welcome_msg": welcome_msg, "welcome_image": welcome_image, "mentions": mentions, "line": line
        })

    embed = discord.Embed(
        title="✨ 𝙾𝙽𝙸𝚇 𝙲𝙾𝙼𝙼𝚄𝙽𝙸𝚃𝚈 • 🎫 𝓣𝓲𝓬𝓴𝓮𝓽ⵙ ✨",
        description=f"> {panel_description}",
        color=discord.Color.from_rgb(15, 15, 15)
    )
    if welcome_image:
        embed.set_image(url=welcome_image)
    embed.set_footer(text="اختر القسم المناسب من القائمة أدناه لفتح تذكرتك.")

    view = MultiTicketPanelView(options_data)
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✨ تم نشر بانل التكتات المتعدد بنجاح!", ephemeral=True)

@bot.tree.command(name="panel", description="إنشاء بانل تذاكر مستقل مع تخصيص وصف الزر واسمه")
@app_commands.describe(
    panel_description="وصف البانل الرئيسي داخل الإيمبد",
    button_label="اسم زر البانل (مثال: فتح تذكرة دعم)",
    button_description="وصف ما بداخل الزر أو رسالة التأكيد",
    panel_image="رابط صورة البانل (اختياري)"
)
async def panel(
    interaction: discord.Interaction,
    panel_description: str,
    button_label: str,
    button_description: str,
    panel_image: str = None
):
    embed = discord.Embed(
        title="❖ 𝙾𝙽𝙸𝚇 🭠 𝓣𝓲𝓬𝓴𝓮𝓽 𝓟𝓪𝓷𝓮𝓵",
        description=f"> {panel_description}",
        color=discord.Color.from_rgb(15, 15, 15)
    )
    if panel_image:
        embed.set_image(url=panel_image)
    embed.set_footer(text="ONIX Community • Click button below")

    view = SingleTicketButtonView(button_label, button_description)
    view.children[0].label = button_label

    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✨ تم إنشاء بانل الزر المستقل بنجاح!", ephemeral=True)

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎉 مشاركة", style=discord.ButtonStyle.success, custom_id="join_giveaway_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ تم تسجيل مشاركتك في المسابقة بنجاح!", ephemeral=True)

@bot.tree.command(name="giveaway", description="إنشاء مسابقة قيف أوي جديدة بشكل فخم")
@app_commands.describe(
    prize="جائزة المسابقة",
    duration_minutes="مدة المسابقة بالدقائق",
    winners_count="عدد الفائزين",
    channel="روم إرسال المسابقة"
)
async def giveaway(interaction: discord.Interaction, prize: str, duration_minutes: int, winners_count: int, channel: discord.TextChannel):
    end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    embed = discord.Embed(
        title="🎉 **قيف أوي جديد | GIVEAWAY** 🎉",
        description=f"> **الجائزة:** `{prize}`\n> **عدد الفائزين:** `{winners_count}`\n> **ينتهي خلال:** `{duration_minutes} دقائق`\n\nاضغط على الزر أدناه للمشاركة بالمسابقة!",
        color=discord.Color.from_rgb(255, 215, 0)
    )
    embed.set_footer(text=f"أنشئ بواسطة {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

    view = GiveawayView()
    msg = await channel.send(content="@everyone قيف أوي جديد اشتعل!", embed=embed, view=view)
    
    await interaction.response.send_message(f"✅ تم بدء القيف أوي بنجاح في الروم {channel.mention}!", ephemeral=True)

    await asyncio.sleep(duration_minutes * 60)
    
    try:
        fetched_msg = await channel.fetch_message(msg.id)
        for child in view.children:
            child.disabled = True
        
        end_embed = discord.Embed(
            title="🎉 **انتهت المسابقة | GIVEAWAY ENDED** 🎉",
            description=f"> **الجائزة:** `{prize}`\n> **انتهى الوقت المحدد للمسابقة!**",
            color=discord.Color.from_rgb(150, 50, 50)
        )
        await fetched_msg.edit(embed=end_embed, view=view)
        await channel.send(f"🎊 انتهى القيف أوي على الجائزة: **{prize}**!")
    except Exception as e:
        print(f"خطأ في انهاء القيف أوي: {e}")

@bot.tree.command(name="set-ping", description="تحديد الروم الذي سيتم إرسال رسالة Ping تلقائية إليه كل 5 دقائق")
@app_commands.describe(channel="اختر الروم لإرسال البينج إليه")
async def set_ping(interaction: discord.Interaction, channel: discord.TextChannel):
    global ping_channel_id
    ping_channel_id = channel.id
    await interaction.response.send_message(f"✅ تم تفعيل بنج البوت التلقائي بنجاح في الروم: {channel.mention} (كل 5 دقائق).", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
