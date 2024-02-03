import asyncio
import os

import discord
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from discord.ext import commands
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv
from twitchAPI.eventsub.webhook import EventSubWebhook

from bot_ui import ConfigView
from models import Base, Guild, UserSubscriptions

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')
WEBHOOK_URL = 'https://cf1b-208-82-96-48.ngrok-free.app'
postgres_connection_str = os.getenv('POSTGRESQL_URL')

engine = create_engine(postgres_connection_str, echo=True)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Twitch stuff
client_id = 'lgzs735eq4rb8o04gbpprk7ia3vge1'

Base.metadata.create_all(engine)


async def on_stream_online(data: StreamOnlineEvent):
    async def send_message():
        channel = bot.get_channel(1076360774882185268)
        if channel:
            await channel.send(f'YIPPIE! {data.event.broadcaster_user_name} is live')

    # Schedule in the discord.py's event loop
    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)


@bot.event
async def on_guild_join(guild):
    # Send message to first available text channel (top to bottom)
    # to configure
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            config_button = ConfigView(guild.owner.id, bot.user)
            await channel.send("What's up chat! Please select a channel for streamsnipe notifications",
                               view=config_button)
            await config_button.wait()

            new_server = Guild(guild_id=str(guild.id),
                               notification_channel_id=str(config_button.channel or guild.text_channels[0].id))
            with Session(engine) as session:
                session.add(new_server)
                session.commit()


@bot.event
async def on_guild_remove(guild):
    # Remove guild from guilds DB
    pass


@bot.hybrid_command(name='notify', description='Get notified when a streamer goes live!')
async def notify(ctx):
    # Add user to user subscription table
    # Handle duplicate inserts
    user_sub = UserSubscriptions(user_id=str(ctx.author.id), guild_id=str(ctx.guild.id), streamer_id='90492842')
    with Session(engine) as session:
        try:
            session.add(user_sub)
            session.commit()
            await ctx.send(f'{ctx.author.mention} will now be notified of when Akula is live!')
        except IntegrityError:
            session.rollback()
            await ctx.send(f'{ctx.author.mention} you are already subscribed to the streamer!')


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
    await bot.tree.sync()

bot.run(TOKEN)
