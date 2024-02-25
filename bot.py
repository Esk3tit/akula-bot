import asyncio
import os
import pprint
from datetime import datetime
from urllib.parse import urlparse

import discord
from sqlalchemy import create_engine, select, delete, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from discord.ext import commands
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.type import TwitchAPIException

from bot_ui import ConfigView
from models import Base, Guild, UserSubscription, Streamer

# Load dotenv if on local env (check for prod only env var)
if not os.getenv('FLY_APP_NAME'):
    load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
postgres_connection_str = os.getenv('POSTGRESQL_URL')

engine = create_engine(postgres_connection_str, echo=True, pool_pre_ping=True, pool_recycle=300)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

pp = pprint.PrettyPrinter(indent=4)

# Twitch stuff
client_id = 'lgzs735eq4rb8o04gbpprk7ia3vge1'

Base.metadata.create_all(engine)


# Global references
twitch_obj = None
webhook_obj = None


async def on_stream_online(data: StreamOnlineEvent):
    embed = discord.Embed(
        color=discord.Color.dark_gold(),
        description=f'You have been drafted to stream snipe {data.event.broadcaster_user_name}\n\n'
                    f'Report to your nearest stream sniping channel IMMEDIATELY!\n\n'
                    f'Failure to do so is a felony and is punishable by fines up to $250,000 '
                    f'and/or prison terms up to 30 years. :saluting_face:',
        title=':rotating_light: MANDATORY STREAM SNIPING DRAFT :rotating_light:',
        timestamp=datetime.now()
    )
    embed.set_author(name=bot.user.name, icon_url=bot.user.avatar)
    embed.set_thumbnail(
        url='https://media.istockphoto.com/id/893424506/vector/smiley-saluting-in-army.jpg?s=612x612&w=0&k=20&c=eJfX306BVuNLZFTJGmmO6xP1Hd6Xw3NVyvRkBHi0NsQ=')
    embed.set_image(url='https://i.imgur.com/beTJRFF.png')

    embed.add_field(name='Target', value=f'`{data.event.broadcaster_user_name}`')
    embed.add_field(name='Last Seen', value=f'`{data.event.started_at}`')
    embed.add_field(name='Link', value=f'`https://www.twitch.tv/{data.event.broadcaster_user_login}`')

    async def send_messages():
        # Fetch data on all the servers and users we need to notify for this streamer
        guild_users_map = {}
        stmt = select(Guild, UserSubscription.user_id).join(Guild.user_subscriptions).join(
            UserSubscription.streamer).where(Streamer.streamer_id == str(data.event.broadcaster_user_id))
        with Session(engine) as session:
            for row in session.execute(stmt).all():
                if row[0].guild_id not in guild_users_map:
                    guild_users_map[row[0].guild_id] = {'notif_channel_id': row[0].notification_channel_id,
                                                        'user_ids': []}
                guild_users_map[row[0].guild_id]['user_ids'].append(row[1])

        # Iterate through all servers and notify users in each one
        for user_sub_obj in guild_users_map.values():
            channel = bot.get_channel(int(user_sub_obj['notif_channel_id']))
            if channel:
                await channel.send(embed=embed)
                await channel.send(''.join(f"<@{user_id}>" for user_id in user_sub_obj['user_ids']))

    # Schedule in the discord.py's event loop
    asyncio.run_coroutine_threadsafe(send_messages(), bot.loop)


async def subscribe_all(webhook):
    """
    Get all streamers from DB and subscribe to them
    using the Twitch API webhook (param)

    :return: None
    """
    with Session(engine) as session:
        for s_id in session.scalars(select(Streamer.streamer_id)).all():
            await webhook.listen_stream_online(s_id, on_stream_online)


async def streamer_get_names_from_ids(twitch: Twitch, broadcaster_ids: str | list[str]):
    channels = await twitch.get_channel_information(broadcaster_ids)
    return [channel.broadcaster_name for channel in channels]


async def streamer_get_ids_from_logins(twitch: Twitch, broadcaster_logins: str | list[str]):
    try:
        return [user.id async for user in twitch.get_users(logins=broadcaster_logins)]
    except TwitchAPIException:
        return None


async def parse_streamers_from_command(streamers):
    if twitch_obj is None:
        raise ValueError("Global variable not initialized.")
    res = []
    need_conversion = []
    for streamer in streamers:
        if streamer.isdigit():
            res.append(streamer)
        elif urlparse(streamer).scheme:
            path_segments = urlparse(streamer).path.split('/')
            streamer_name = path_segments[-1]  # Assuming last segment is the streamer name
            need_conversion.append(streamer_name)
        else:
            need_conversion.append(streamer)

    if need_conversion:
        ids = await streamer_get_ids_from_logins(twitch_obj, need_conversion)
        if ids:
            res.extend(ids)
        else:
            res = None
    await twitch_obj.close()
    return res


@bot.event
async def on_guild_join(guild):
    # Send message to first available text channel (top to bottom)
    # to configure
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            config_button = ConfigView(guild.owner.id, bot.user)
            await channel.send("What's up chat! Please select a channel for stream snipe notifications",
                               view=config_button)
            await config_button.wait()

            new_server = Guild(guild_id=str(guild.id),
                               notification_channel_id=str(config_button.channel.id or guild.text_channels[0].id))
            with Session(engine) as session:
                session.add(new_server)
                session.commit()
            break


@bot.event
async def on_guild_remove(guild):
    # Remove guild from guilds DB, don't have objects of guild
    # so need to do it with Core/non-Unit of Work pattern
    with Session(engine) as session:
        session.execute(delete(Guild).where(Guild.guild_id == str(guild.id)))

        # Cascade occurs and user subs table should have some entries removed
        # if it referred to the guild just deleted. See if we need to prune
        # streamer table as well since we might have deleted all refs to a streamer
        # in user sub table with cascade
        stmt = select(Streamer).outerjoin(UserSubscription).where(UserSubscription.streamer_id == None)
        streamers_to_delete = session.scalars(stmt).all()
        for streamer in streamers_to_delete:
            session.delete(streamer)
        session.commit()


@bot.command(name='notify', description='Get notified when a streamer goes live!')
async def notify(ctx, *streamers):
    if webhook_obj is None:
        raise ValueError('Global reference not initialized...')
    with Session(engine) as session:
        # Check if we need to insert streamer into streamer table
        # (if it is first time streamer is ever being watched)
        # Don't need to commit here since we do it in try catch
        clean_streamers = await parse_streamers_from_command(streamers)
        if not clean_streamers:
            return await ctx.send(f'{ctx.author.mention} Unable to find given streamer, please try again... MAGGOT!')
        for s in clean_streamers:
            streamer = session.scalar(select(Streamer).where(Streamer.streamer_id == s))
            if not streamer:
                streamer = Streamer(streamer_id=s)
                session.add(streamer)
                await webhook_obj.listen_stream_online(s, on_stream_online)
                session.commit()

        # If streamer already in streamer table and user runs dupe notify
        # then this try catch block will handle dupe command
        try:
            session.execute(
                insert(UserSubscription),
                [
                    {
                        "user_id": str(ctx.author.id),
                        "guild_id": str(ctx.guild.id),
                        "streamer_id": s
                    } for s in clean_streamers
                ]
            )
            session.commit()
            await ctx.send(f'{ctx.author.mention} will now be notified of when the streamer(s) are live!')
        except IntegrityError:
            session.rollback()
            await ctx.send(
                f'{ctx.author.mention} you are already subscribed to some or all of the streamer(s)! Reverting...'
            )


@bot.command(name='unnotify', description='Unsubscribe from notification when a streamer goes live!')
async def unnotify(ctx, *streamers):
    success = []
    fail = []
    with Session(engine) as session:
        clean_streamers = await parse_streamers_from_command(streamers)
        if not clean_streamers:
            return await ctx.send(f'{ctx.author.mention} Unable to find given streamer, please try again... MAGGOT!')
        for s in clean_streamers:
            user_sub = session.scalar(
                select(UserSubscription).where(
                    UserSubscription.user_id == str(ctx.author.id),
                    UserSubscription.guild_id == str(ctx.guild.id),
                    UserSubscription.streamer_id == s
                )
            )
            if user_sub:
                session.delete(user_sub)
                success.append(s)

                # Check if streamer references are still in user subs, remove from streamer table if not
                # Can just check for existence of one (first) record, don't need to query all records if
                # there is at least one record
                streamer_refs = session.scalars(
                    select(UserSubscription).where(UserSubscription.streamer_id == s)).first()
                if not streamer_refs:
                    session.execute(delete(Streamer).where(Streamer.streamer_id == s))
            else:
                fail.append(s)

        session.commit()

    if success:
        await ctx.send(f'{ctx.author.mention} You will no longer be notified for: {", ".join(success)}!')
    if fail:
        await ctx.send(f'{ctx.author.mention} Unable to unsubscribe from: {", ".join(fail)}!')


# @bot.hybrid_command(name='test', description='for testing code when executed')
# async def test(ctx, streamer_id):
#     pass


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    twitch = await Twitch(client_id, client_secret)
    global twitch_obj
    twitch_obj = twitch
    # Set up EventSub webhook
    # port specifies port to run internal backend on for webhook
    # url needs to be a proxy url to this port (ex. ngrok http <port>)
    # so that twitch sends notifs to internal server
    webhook = EventSubWebhook(WEBHOOK_URL, 8080, twitch)
    global webhook_obj
    webhook.unsubscribe_on_stop = False
    await webhook.unsubscribe_all()
    webhook.start()
    webhook_obj = webhook
    # await bot.get_channel(1076360774882185268).send('BOT IS ONLINE')
    print("Subscribing to notif")
    # await webhook.listen_stream_online('90492842', on_stream_online)
    # await webhook.listen_stream_online('162656602', on_stream_online)
    await subscribe_all(webhook)
    print("Subscribed to notif!")
    await bot.tree.sync()


bot.run(TOKEN)
