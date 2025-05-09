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

def get_users_to_notify(content_type, hour, is_warning):
    settings = load_settings()
    result = []
    for user_id, mode in settings.items():
        if mode == "off":
            continue
        if content_type == "field" and mode == "no_field":
            continue
        if content_type == "barrier":
            if mode == "night_exclude" and hour in [3, 6]:
                continue
            if mode == "night_exclude" and is_warning and ((hour + 1) % 24) in [3, 6]:
                continue
        result.append(int(user_id))
    return result

async def send_alert(content_type, message, hour, is_warning=False):
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    users = get_users_to_notify(content_type, hour, is_warning)
    mentions = " ".join(f"<@{uid}>" for uid in users)
    await channel.send(f"{mentions} {message}" if mentions else f"🔔 {message}")

def schedule_all():
    barrier_hours = [0, 3, 6, 9, 12, 15, 18, 21]
    field_hours = [12, 18, 20, 22]

    for hour in barrier_hours:
        scheduler.add_job(send_alert, 'cron', hour=(hour - 1) % 24, minute=55, args=["barrier", "5분 후 불길한 소환의 결계가 생성됩니다!", hour, True])
        scheduler.add_job(send_alert, 'cron', hour=hour, minute=0, args=["barrier", "불길한 소환의 결계가 생성되었습니다!", hour, False])

    for hour in field_hours:
        scheduler.add_job(send_alert, 'cron', hour=(hour - 1) % 24, minute=55, args=["field", "5분 후 필드보스가 등장합니다!", hour, True])
        scheduler.add_job(send_alert, 'cron', hour=hour, minute=0, args=["field", "필드보스가 등장했습니다!", hour, False])

class AlertSettingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="결계-모든시간", style=discord.ButtonStyle.primary)
    async def all_barrier(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "all")

    @discord.ui.button(label="결계-심야제외", style=discord.ButtonStyle.primary)
    async def barrier_no_night(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "night_exclude")

    @discord.ui.button(label="필드보스 알림 제외", style=discord.ButtonStyle.secondary)
    async def no_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_setting(interaction, "no_field")

    @discord.ui.button(label="모든 알림 끄기", style=discord.ButtonStyle.danger)
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
            content="📣 필드/결계 알림 설정 버튼을 눌러 알림 수신 상태를 선택하세요!",
            view=AlertSettingView()
        )
    except Exception as e:
        print("초기 메시지 전송 실패:", e)

client.run(TOKEN)

