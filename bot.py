import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

scheduler = AsyncIOScheduler(timezone=timezone('Asia/Seoul'))

async def send_warning():
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@everyone 🚨 5분 후 불결한 결계가 생성됩니다! 준비하세요!")

async def send_spawn():
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@everyone 🚨 불결한 결계가 생성되었습니다!")

async def send_test_alert():
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@everyone 🧪 [테스트] 불결한 결계 테스트 알림!")

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    scheduler.start()

    # 기존 스케줄 등록
    for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
        scheduler.add_job(send_warning, 'cron', hour=(hour-1)%24, minute=55)
        scheduler.add_job(send_spawn, 'cron', hour=hour, minute=0)

    # (1) 즉시 테스트 알림 보내기
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@everyone 🧪 [즉시 테스트] 봇 정상 작동 확인 알림!")

    # (2) 추가로 5분 뒤에도 테스트 알림 예약
    test_time = datetime.now(timezone('Asia/Seoul')) + timedelta(minutes=5)
    scheduler.add_job(send_test_alert, 'date', run_date=test_time)
    print(f"🧪 테스트 알림 예약 완료: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")

client.run(TOKEN)
