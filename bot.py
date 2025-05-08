import discord
from discord.ext import tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
client = discord.Client(intents=intents)

scheduler = AsyncIOScheduler(timezone=timezone('Asia/Seoul'))
SETTINGS_FILE = 'user_settings.json'

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)

def get_users_to_notify(content_type, hour):
    settings = load_settings()
    result = []
    for user_id, mode in settings.items():
        if mode == "off":
            continue
        if content_type == "field" and mode == "no_field":
            continue
        if content_type == "barrier":
            if mode == "night_exclude" and hour in [0, 3, 6]:
                continue
        result.append(int(user_id))
    return result

async def send_alert(content_type, message, hour):
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    users = get_users_to_notify(content_type, hour)
    mentions = " ".join(f"<@{uid}>" for uid in users)
    await channel.send(f"{mentions} {message}" if mentions else f"🔔 {message}")

def schedule_all():
    barrier_hours = [0, 3, 6, 9, 12, 15, 18, 21]
    field_hours = [12, 18, 20, 22]

    for hour in barrier_hours:
        scheduler.add_job(send_alert, 'cron', hour=(hour - 1) % 24, minute=55, args=["barrier", "5분 후 불길한 소환의 결계가 생성됩니다!", hour])
        scheduler.add_job(send_alert, 'cron'림", style=discord.ButtonStyle.primary)
    async def all_barrier(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "all")

    @discord.ui.button(label="결계-심야제외", style=discord.ButtonStyle.primary)
    async def barrier_no_night(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "night_exclude")

    @discord.ui.button(label="필드보스 알림 제외", style=discord.ButtonStyle.secondary)
    async def no_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "no_field")

    @discord.ui.button(label="모든 알림 제외", style=discord.ButtonStyle.danger)
    async def off(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "off")

    async def set_setting(self, interaction, mode):
        settings = load_settings()
        settings[str(interaction.user.id)] = mode
        save_settings(settings)
        await interaction.response.send_message(f"{interaction.user.mention} 알림 설정이 변경되었습니다: `{mode}`", ephemeral=True)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    scheduler.start()
    schedule_all()

    try:
        await client.wait_until_ready()
        channel = client.get_channel(CHANNEL_ID)
        await channel.send(
            content="\ud83d\udce3\ufe0f \ud544\ub4dc/\uacbd\uacc4 \uc54c\ub9bc \uc124\uc815 \ubc84\ud2bc\uc744 \ub204\ub974\uc5b4 \uc54c\ub9bc \uc218\uc2e0 \uc0c1\ud0dc\ub97c \uc120\ud0dd\ud558\uc138\uc694!",
            view=AlertSettingView()
        )
    except Exception as e:
        print("\ucd08\uae30 \uba54\uc2dc\uc9c0 \uc804\uc1a1 \uc2e4\ud328:", e)

client.run(TOKEN)
