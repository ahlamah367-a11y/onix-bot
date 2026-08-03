import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import re

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

# دوال وKlasses القيف أواي
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

        if winner:
            winner_text = winner.mention
        else:
            winner_text = f"<@{winner_id}>"

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

# --- نظام الـ Panel داخل إيمبد فخم ---
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

bot.run(os.getenv("DISCORD_TOKEN"))

