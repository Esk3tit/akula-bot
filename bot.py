import os

import discord
import twitchAPI.helper
from discord.ext import commands, tasks
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv
from twitchAPI.eventsub.webhook import EventSubWebhook

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')
WEBHOOK_URL = "https://145a-67-170-149-50.ngrok-free.app"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Twitch stuff
client_id = 'lgzs735eq4rb8o04gbpprk7ia3vge1'


# @tasks.loop(seconds=10)
# async def stream_live_loop(twitch):
#     stream = await twitchAPI.helper.first(twitch.get_streams(user_id=['90492842'], stream_type='live'))
#
#     if stream is not None:
#         await bot.get_channel(1076360774882185268).send('YIPPIE! Akula is live')
#     else:
#         await bot.get_channel(1076360774882185268).send('Akula is not GAMING :(')

async def on_stream_online(data: StreamOnlineEvent):
    await bot.get_channel(1076360774882185268).send(f'YIPPIE! {data.event.broadcaster_user_name} is live')


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
    await webhook.listen_stream_online('90492842', on_stream_online)

bot.run(TOKEN)
