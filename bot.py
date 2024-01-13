import asyncio
import os

import discord
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from discord.ext import commands, tasks
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv
from twitchAPI.eventsub.webhook import EventSubWebhook

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')
WEBHOOK_URL = 'https://ff93-67-170-149-50.ngrok-free.app'
postgres_connection_str = os.getenv('POSTGRESQL_URL')

engine = create_engine(postgres_connection_str, echo=True)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Twitch stuff
client_id = 'lgzs735eq4rb8o04gbpprk7ia3vge1'


async def on_stream_online(data: StreamOnlineEvent):
    async def send_message():
        channel = bot.get_channel(1076360774882185268)
        if channel:
            await channel.send(f'YIPPIE! {data.event.broadcaster_user_name} is live')

    # Schedule in the discord.py's event loop
    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    twitch = await Twitch(client_id, client_secret)
    # Check for live users every couple of seconds
    print(twitch.app_id, twitch.app_secret)
    # Set up EventSub webhook
    # port specifies port to run internal backend on for webhook
    # url needs to be a proxy url to this port (ex. ngrok http <port>)
    # so that twitch sends notifs to internal server
    webhook = EventSubWebhook(WEBHOOK_URL, 8080, twitch)
    await webhook.unsubscribe_all()
    webhook.start()
    await bot.get_channel(1076360774882185268).send('BOT IS ONLINE')
    print("Subscribing to notif")
    await webhook.listen_stream_online('90492842', on_stream_online)
    # await webhook.listen_stream_online('162656602', on_stream_online)
    with Session(engine) as session:
        result = session.execute(text("SELECT 'Hello World'"))
        print(result.all())
    print("Subscribed to notif!")

bot.run(TOKEN)
