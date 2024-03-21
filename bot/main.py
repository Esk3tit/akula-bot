import asyncio
import os
import pprint
from urllib.parse import urlparse

import discord
from discord import app_commands
from sqlalchemy import create_engine, select, delete, insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from discord.ext import commands
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.type import TwitchAPIException

from bot.bot_ui import ConfigView, create_streamsnipe_draft_embed, create_config_embed
from bot.bot_utils import is_owner, get_first_text_channel
from bot.models import Base, Guild, UserSubscription, Streamer

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
twitch_obj: Twitch | None = None
webhook_obj: EventSubWebhook | None = None


async def on_stream_online(data: StreamOnlineEvent):
    embed = create_streamsnipe_draft_embed(data, bot.user.name, bot.user.avatar)

    async def send_messages():
        # Fetch data on all the servers and users we need to notify for this streamer
        guild_users_map = {}
        stmt = select(Guild, UserSubscription.user_id).join(Guild.user_subscriptions).join(
            UserSubscription.streamer).where(Streamer.streamer_id == str(data.event.broadcaster_user_id))
        with Session(engine) as session:
            for row in session.execute(stmt).all():
                if row[0].guild_id not in guild_users_map:
                    guild_users_map[row[0].guild_id] = {'notif_channel_id': row[0].notification_channel_id,
                                                        'user_ids': [],
                                                        'notif_mode': row[0].notification_mode}
                guild_users_map[row[0].guild_id]['user_ids'].append(row[1])

        # Iterate through all servers and notify users in each one
        for guild_id, user_sub_obj in guild_users_map.items():
            channel = bot.get_channel(int(user_sub_obj['notif_channel_id']))
            if channel:
                await channel.send(embed=embed)

                # Check notification mode and act accordingly
                notification_mode = user_sub_obj['notif_mode']
                if notification_mode == 'global':
                    guild = bot.get_guild(int(guild_id))
                    if guild.me.guild_permissions.mention_everyone:
                        await channel.send('@everyone')
                    else:
                        await channel.send(
                            "The bot doesn't have permission to mention everyone. Mentioning here instead.")
                        await channel.send('@here')
                elif notification_mode == 'optin':
                    await channel.send(' '.join(f"<@{user_id}>" for user_id in user_sub_obj['user_ids']))

    # Schedule in the discord.py's event loop
    asyncio.run_coroutine_threadsafe(send_messages(), bot.loop)


async def subscribe_all(webhook):
    """
    Get all streamers from DB and subscribe to them
    using the Twitch API webhook (param)

    :return: None
    """
    with Session(engine) as session:
        for s in session.scalars(select(Streamer)).all():
            s.topic_sub_id = await webhook.listen_stream_online(s.streamer_id, on_stream_online)
        session.commit()


async def streamer_get_names_from_ids(twitch: Twitch, ids: list[str]):
    try:
        return {user.id: user.display_name async for user in twitch.get_users(user_ids=ids)}
    except TwitchAPIException:
        return None


async def streamer_get_ids_from_logins(twitch: Twitch, broadcaster_logins: list[str]):
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
    return res


@bot.event
async def on_guild_join(guild: discord.Guild):
    # Send message to first available text channel (top to bottom)
    # to configure, if no permission channel then send DM to owner
    channel = get_first_text_channel(guild)
    if channel is None:
        try:
            await guild.owner.send("Error: Bot has no channel that it has permission to post in.")
            print(f"Message sent to the guild owner: {guild.owner}")
        except discord.HTTPException as e:
            print(f"Failed to send message to the guild owner: {guild.owner}")
            print(f"Error: {e}")
        return

    config_button = ConfigView(guild.owner.id, bot.user, guild)
    embed = create_config_embed(
        'No channel configured yet',
        'default is Opt-In',
        bot.user.display_name,
        bot.user.display_avatar,
        guild.owner.display_name,
        guild.owner.display_avatar
    )
    await channel.send(embed=embed)
    config_button.message = await channel.send(view=config_button)
    await config_button.wait()

    new_server = Guild(guild_id=str(guild.id),
                       notification_channel_id=str(config_button.channel.id or channel.id),
                       notification_mode=config_button.notification_mode)
    with Session(engine) as session:
        session.add(new_server)
        session.commit()


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
        # Commit before try catch to avoid foreign key constraint
        # Needs to exist in streamer table before insert into user sub
        clean_streamers = await parse_streamers_from_command(streamers)
        if clean_streamers is None:
            return await ctx.send(f'{ctx.author.mention} Unable to find given streamer, please try again... MAGGOT!')
        id_to_name = await streamer_get_names_from_ids(twitch_obj, clean_streamers)
        for s in clean_streamers:
            streamer = session.scalar(select(Streamer).where(Streamer.streamer_id == s))
            if not streamer:
                topic = await webhook_obj.listen_stream_online(s, on_stream_online)
                new_streamer = Streamer(streamer_id=s, streamer_name=id_to_name[s], topic_sub_id=topic)
                session.add(new_streamer)
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
    if not twitch_obj or not webhook_obj:
        raise ValueError('Global reference not initialized...')
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
                    streamer = session.scalar(select(Streamer))
                    status = await webhook_obj.unsubscribe_topic(streamer.topic_sub_id)
                    print(f'unsubbing topic {streamer.topic_sub_id} from streamer {streamer.streamer_name}')
                    if not status:
                        print(f'failed to unsubscribe from streamer through API!!!!')
                    session.execute(delete(Streamer).where(Streamer.streamer_id == s))
            else:
                fail.append(s)

        session.commit()

    if success:
        await ctx.send(f'{ctx.author.mention} You will no longer be notified for: {", ".join(success)}!')
    if fail:
        await ctx.send(f'{ctx.author.mention} Unable to unsubscribe from: {", ".join(fail)}!')


@bot.hybrid_command(name='notifs', description='Get current streamers that you are getting notifications for.')
async def notifs(ctx):
    with Session(engine) as session:
        notified_streamers = session.scalars(
            select(UserSubscription.streamer_id).where(
                UserSubscription.user_id == str(ctx.author.id),
                UserSubscription.guild_id == str(ctx.guild.id)
            )
        ).all()

        if notified_streamers:
            embed = discord.Embed(title="Your Notification Subscriptions",
                                  description=f"Here are the streamers you're subscribed to in {ctx.guild.name}:",
                                  color=0x00ff00)
            subscriptions_text = "\n".join([f"- {streamer_id}" for streamer_id in notified_streamers])
            if len(subscriptions_text) > 1024:
                # Handle cases where the text exceeds the field value limit
                embed.add_field(name="Subscribed Streamers", value="Too many subscriptions to display here!",
                                inline=False)
            else:
                embed.add_field(name="Subscribed Streamers", value=subscriptions_text, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'{ctx.author.mention} You are not receiving notifications in {ctx.guild.name}!')


@bot.hybrid_command(name='changeconfig', description='Change configuration of the bot server-wide.')
@app_commands.check(is_owner)
async def changeconfig(ctx):
    with Session(engine) as session:
        guild_config = session.scalar(select(Guild).where(Guild.guild_id == str(ctx.guild.id)))
        embed = create_config_embed(bot.get_channel(int(guild_config.notification_channel_id)).name,
                                    guild_config.notification_mode,
                                    bot.user.name,
                                    bot.user.display_avatar,
                                    ctx.author.display_name,
                                    ctx.author.display_avatar)
        await ctx.send(embed=embed)
    view = ConfigView(ctx.guild.owner.id, bot.user, ctx.guild)
    view.message = await ctx.send(view=view)
    await view.wait()

    # Write to DB here after getting values from view
    channel = get_first_text_channel(ctx.guild)
    with Session(engine) as session:
        session.execute(
            update(Guild).
            where(Guild.guild_id == str(ctx.guild.id)).
            values(
                notification_channel_id=str(view.channel.id or channel.id),
                notification_mode=view.notification_mode
            )
        )
        session.commit()


@changeconfig.error
async def changeconfig_error(ctx, error):
    await ctx.send(f"You do not have permission to use this command!, {error}", ephemeral=True)


# @bot.hybrid_command(name='test', description='for testing code when executed')
# async def test(ctx):
#     with Session(engine) as session:
#         streamer_ids = session.scalars(select(Streamer.streamer_id)).all()
#         async for user in twitch_obj.get_users(user_ids=streamer_ids):
#             streamer = session.scalar(select(Streamer))
#             streamer.streamer_name = user.display_name
#         session.commit()


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
    await subscribe_all(webhook)
    print("Subscribed to notif!")
    await bot.tree.sync()


if __name__ == '__main__':
    # When pytest imports this file this runs the bot without this check
    # since when importing the imported file is executed...
    bot.run(TOKEN)
