import os

import discord
import twitchAPI.helper
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Twitch stuff
client_id = 'lgzs735eq4rb8o04gbpprk7ia3vge1'


@tasks.loop(seconds=10)
async def stream_live_loop(twitch):
    stream = await twitchAPI.helper.first(twitch.get_streams(user_id=['90492842'], stream_type='live'))

    if stream is not None:
        await bot.get_channel(1076360774882185268).send('YIPPIE! Akula is live')
    else:
        await bot.get_channel(1076360774882185268).send('Akula is not GAMING :(')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    twitch = await Twitch(client_id, client_secret)
    # Check for live users every couple of seconds
    stream_live_loop.start(twitch)

bot.run(TOKEN)
