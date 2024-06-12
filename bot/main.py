import asyncio
import os
import re
import random

import discord
from discord import app_commands
from sqlalchemy import create_engine, select, delete, insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from discord.ext import commands
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOnlineData
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from dotenv import load_dotenv
from twitchAPI.eventsub.webhook import EventSubWebhook

from bot.bot_ui import ConfigView, create_config_embed, EmbedCreationContext
from bot.embed_strategies.draft import DraftEmbedStrategy
from bot.embed_strategies.isis import IsisEmbedStrategy
from bot.bot_utils import is_owner, get_first_sendable_text_channel, validate_streamer_ids_get_names, streamer_get_ids_names_from_logins, is_owner_or_optin_mode
from bot.embed_strategies.prigozhin import PrigozhinEmbedStrategy
from bot.embed_strategies.sfw import SafeForWorkEmbedStrategy
from bot.models import Base, Guild, UserSubscription, Streamer

# Load dotenv if on local env (check for prod only env var)
if not os.getenv('FLY_APP_NAME'):
    load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client_secret = os.getenv('TWITCH_CLIENT_SECRET')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
postgres_connection_str = os.getenv('POSTGRESQL_URL')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# DB Init
engine = create_engine(postgres_connection_str, echo=True, pool_pre_ping=True, pool_recycle=300)
Base.metadata.create_all(engine)

# Twitch stuff
client_id = 'lgzs735eq4rb8o04gbpprk7ia3vge1'

# Global references
twitch_obj: Twitch | None = None
webhook_obj: EventSubWebhook | None = None


async def on_stream_online(data: StreamOnlineEvent):
    """
    Handle the event when a streamer goes online. Selects a random embed strategy from a list of strategies and creates an embed using the selected strategy.
    Fetches data on servers and users to notify for the streamer going online, based on their subscriptions.
    Generates a SafeForWork embed if the notification mode is 'global' or 'passive' and the server is censored.
    Notifies users in each server based on their notification mode and subscription status.

    Parameters:
    - data (StreamOnlineEvent): The event data for the streamer going online.

    Returns:
    - None
    """

    embed_strategies = [
        DraftEmbedStrategy(),
        IsisEmbedStrategy(),
        PrigozhinEmbedStrategy()
    ]
    selected_embed_strategy = random.choice(embed_strategies)
    context = EmbedCreationContext(selected_embed_strategy)
    embed = context.create_embed(data, bot.user.name, bot.user.avatar)

    async def send_messages():
        # Fetch data on all the servers and users we need to notify for this streamer
        guild_users_map = {}
        stmt = select(Guild, UserSubscription.user_id).join(Guild.user_subscriptions).join(
            UserSubscription.streamer).where(Streamer.streamer_id == str(data.event.broadcaster_user_id))
        with Session(engine) as session:
            for row in session.execute(stmt).all():
                if row[0].guild_id not in guild_users_map:
                    guild_users_map[row[0].guild_id] = {'notif_channel_id': row[0].notification_channel_id,
                                                        'user_ids': set(),
                                                        'notif_mode': row[0].notification_mode,
                                                        'is_censored': row[0].is_censored}
                guild_users_map[row[0].guild_id]['user_ids'].add(row[1])

        # Iterate through all servers and notify users in each one
        for guild_id, user_sub_obj in guild_users_map.items():
            channel = bot.get_channel(int(user_sub_obj['notif_channel_id']))
            if channel:
                # Check notification mode and act accordingly, only send if server owner
                # is subbed in global or passive mode
                notification_mode = user_sub_obj['notif_mode']
                guild = bot.get_guild(int(guild_id))

                # Censorship check and dynamic SFW embed generation
                is_censored = user_sub_obj['is_censored']
                sfw_context = EmbedCreationContext(SafeForWorkEmbedStrategy())
                twitch_user = await first(twitch_obj.get_users(user_ids=[data.event.broadcaster_user_id]))
                sfw_embed = sfw_context.create_embed_custom_images(
                    data,
                    bot.user.name,
                    bot.user.avatar,
                    guild.icon.url,
                    twitch_user.profile_image_url
                )
                if notification_mode == 'global' or notification_mode == 'passive':
                    owner_id = str(guild.owner_id)
                    if owner_id in user_sub_obj['user_ids']:
                        await channel.send(embed=embed if not is_censored else sfw_embed)
                        # Send embed now for both global and passive, but only mention everyone
                        # or here if global
                        if notification_mode == 'global':
                            if guild.me.guild_permissions.mention_everyone:
                                await channel.send('@everyone')
                            else:
                                await channel.send(
                                    "The bot doesn't have permission to mention everyone. Mentioning here instead.")
                                await channel.send('@here')
                else:
                    await channel.send(embed=embed if not is_censored else sfw_embed)
                    await channel.send(' '.join(f"<@{user_id}>" for user_id in user_sub_obj['user_ids']))

    # Schedule in the discord.py's event loop
    asyncio.run_coroutine_threadsafe(send_messages(), bot.loop)


async def subscribe_all(webhook):
    """
    Execute a database session to iterate over all Streamer objects,
    updating their topic_sub_id attribute by calling the webhook's listen_stream_online method with the streamer's ID
    and the on_stream_online callback function. Finally, commit the changes made in the session.

    Parameters:
    - webhook (EventSubWebhook): The event data for the streamer going online.

    Returns:
    - None
    """
    with Session(engine) as session:
        for s in session.scalars(select(Streamer)).all():
            s.topic_sub_id = await webhook.listen_stream_online(s.streamer_id, on_stream_online)
        session.commit()


async def parse_streamers_from_command(streamers):
    """
    Parse the given list of streamers to extract valid streamer IDs and names.

    Parameters:
    - streamers (list): A list of strings representing streamer IDs, streamer names, or Twitch URLs.

    Returns:
    - list: A list of valid streamer IDs and names extracted from the input streamers.

    Raises:
    - ValueError: If the global variable 'twitch_obj' is not initialized.

    The function first checks if the 'twitch_obj' global variable is initialized. Then, it iterates over the input streamers to identify streamer IDs, streamer names, and Twitch URLs. It validates the streamer IDs using the 'validate_streamer_ids_get_names' function and converts streamer names to IDs using the 'streamer_get_ids_names_from_logins' function. Finally, it returns a list of valid streamer IDs and names extracted from the input streamers.
    """

    if twitch_obj is None:
        raise ValueError("Global variable not initialized.")
    res = set()
    need_conversion = set()
    need_validation = set()

    # Robustly match twitch URLs, so that we don't convert streamer names from invalid domains
    # even if the streamer name there is valid
    twitch_url_pattern = re.compile(r'^https?://(?:www\.)?twitch\.tv/(\w+)(?:/.*)?$')
    for streamer in streamers:
        if streamer.isdigit():
            need_validation.add(streamer)
        else:
            url_match = twitch_url_pattern.match(streamer)
            if url_match:
                streamer_name = url_match.group(1)
                need_conversion.add(streamer_name)
            else:
                need_conversion.add(streamer)

    if need_validation:
        valid_ids_names = await validate_streamer_ids_get_names(twitch_obj, list(need_validation))
        if valid_ids_names:
            res.update(valid_ids_names)
        else:
            return []

    if need_conversion:
        ids_names = await streamer_get_ids_names_from_logins(twitch_obj, list(need_conversion))
        if ids_names:
            res.update(ids_names)
        else:
            return []
    return list(res)


@bot.event
async def on_guild_join(guild: discord.Guild):
    """
    Async function to handle actions when the bot joins a new guild.

    Parameters:
    - guild (discord.Guild): The guild that the bot has joined.

    Returns:
    - None
    """

    # Send message to first available text channel (top to bottom)
    # to configure, if no permission channel then send DM to owner
    channel = get_first_sendable_text_channel(guild)
    if channel is None:
        try:
            await guild.owner.send("Error: Bot has no channel that it has permission to post in.")
            print(f"Message sent to the guild owner: {guild.owner}")
        except discord.HTTPException as e:
            print(f"Failed to send message to the guild owner: {guild.owner}")
            print(f"Error: {e}")
        return

    config_view = ConfigView(guild.owner.id, bot.user, guild)
    embed = create_config_embed(
        'No channel configured yet',
        'default is Opt-In',
        'default is False',
        bot.user.display_name,
        bot.user.display_avatar,
        guild.owner.display_name,
        guild.owner.display_avatar
    )
    await channel.send(f'{guild.owner.mention}')
    await channel.send(embed=embed)
    config_view.message = await channel.send(view=config_view)
    await config_view.wait()

    new_server = Guild(guild_id=str(guild.id),
                       notification_channel_id=str(config_view.channel.id or channel.id),
                       notification_mode=config_view.notification_mode)
    with Session(engine) as session:
        session.add(new_server)
        session.commit()


@bot.event
async def on_guild_remove(guild: discord.Guild):
    """
    Remove a guild from the database and cascade delete related entries in the user subscriptions table and potentially in the streamer table.

    Parameters:
    - guild (discord.Guild): The guild to be removed from the database.

    Returns:
    - None
    """

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
@is_owner_or_optin_mode(engine)
async def notify(ctx, *streamers):
    """
    Notify users about the given streamers and handle subscriptions.

    Parameters:
    - ctx: The context of the command invocation.
    - *streamers: Variable number of streamers to notify users about.

    Returns:
    - None
    """

    if webhook_obj is None:
        raise ValueError('Global reference not initialized...')
    clean_streamers = await parse_streamers_from_command(streamers)
    if not clean_streamers:
        return await ctx.send(
            f'{ctx.author.mention} Unable to find one of the given streamer(s), please try again... MAGGOT!')
    with Session(engine) as session:
        # Check if we need to insert streamer into streamer table
        # (if it is first time streamer is ever being watched)
        # Commit before try catch to avoid foreign key constraint
        # Needs to exist in streamer table before insert into user sub
        for s in clean_streamers:
            streamer = session.scalar(select(Streamer).where(Streamer.streamer_id == s.id))
            if not streamer:
                topic = await webhook_obj.listen_stream_online(s.id, on_stream_online)
                new_streamer = Streamer(streamer_id=s.id, streamer_name=s.name, topic_sub_id=topic)
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
                        "streamer_id": s.id
                    } for s in clean_streamers
                ]
            )
            session.commit()
            await ctx.send(f'{ctx.author.mention} will now be notified of when the following streamers are live: `{", ".join([s.name for s in clean_streamers])}`')
        except IntegrityError:
            session.rollback()
            await ctx.send(
                f'{ctx.author.mention} you are already subscribed to some or all of the streamer(s)! Reverting...'
            )


@notify.error
async def notify_error(ctx, error):
    """
    Prints the error message and sends a permission denial message to the user.

    Parameters:
    - error: The error message to be printed.

    Returns:
    - None
    """

    print(error)
    await ctx.send(
        f"{ctx.author.mention} You don't have permission to use this command...",
        ephemeral=True
    )


@bot.command(name='unnotify', description='Unsubscribe from notification when a streamer goes live!')
@is_owner_or_optin_mode(engine)
async def unnotify(ctx, *streamers):
    """
    Unnotify users from receiving notifications for specific streamers.

    Parameters:
    - ctx (Context): The context of the command.
    - *streamers (str): Variable number of strings representing streamer IDs, streamer names, or Twitch URLs.

    Returns:
    - None

    Raises:
    - ValueError: If the global variable 'webhook_obj' is not initialized.

    The function checks if the 'webhook_obj' global variable is initialized. It then parses the input streamers to extract valid streamer IDs and names. For each streamer, it checks if the user is subscribed and removes the subscription. If no references to the streamer remain, it unsubscribes from the streamer's topic. Finally, it sends messages to the user indicating success or failure of the unsubscription process.
    """

    if webhook_obj is None:
        raise ValueError('Global reference not initialized...')
    success = []
    fail = []
    clean_streamers = await parse_streamers_from_command(streamers)
    if not clean_streamers:
        return await ctx.send(f'{ctx.author.mention} Unable to find given streamer, please try again... MAGGOT!')

    with Session(engine) as session:
        for original_arg, s in zip(streamers, clean_streamers):
            user_sub = session.scalar(
                select(UserSubscription).join(UserSubscription.streamer).where(
                    UserSubscription.user_id == str(ctx.author.id),
                    UserSubscription.guild_id == str(ctx.guild.id),
                    Streamer.streamer_id == s.id
                )
            )
            if user_sub:
                session.delete(user_sub)
                success.append(user_sub.streamer.streamer_name)

                # Check if streamer references are still in user subs, remove from streamer table if not
                # Can just check for existence of one (first) record, don't need to query all records if
                # there is at least one record
                streamer_refs = session.scalars(
                    select(UserSubscription).where(UserSubscription.streamer_id == s.id)).first()
                if not streamer_refs:
                    streamer = session.scalar(select(Streamer).where(Streamer.streamer_id == s.id))
                    status = await webhook_obj.unsubscribe_topic(streamer.topic_sub_id)
                    print(f'unsubbing topic {streamer.topic_sub_id} from streamer {streamer.streamer_name}')
                    if not status:
                        print(f'failed to unsubscribe from streamer through API!')
                    session.delete(streamer)
            else:
                fail.append(original_arg)

        session.commit()

    if success:
        await ctx.send(f'{ctx.author.mention} You will no longer be notified for: `{", ".join(success)}`!')
    if fail:
        await ctx.send(f'{ctx.author.mention} Unable to unsubscribe from: `{", ".join(fail)}`!')


@unnotify.error
async def unnotify_error(ctx, error):
    """
    Unnotify users from receiving notifications for specific streamers.

    Parameters:
    - ctx (Context): The context of the command.
    - error (Exception): The error that occurred during the unnotify process.

    Returns:
    - None

    The function prints the error message and sends a response to the user indicating that they do not have permission to use the command.
    """

    print(error)
    await ctx.send(
        f"{ctx.author.mention} You don't have permission to use this command...",
        ephemeral=True
    )


@bot.hybrid_command(name='notifs', description='Get current streamers that you are getting notifications for.')
async def notifs(ctx):
    """
    Function to display notification subscriptions for a user in a specific guild.

    Parameters:
    - ctx (discord.ext.commands.Context): The context object representing the invocation context of the command.

    Returns:
    - None
    """

    with Session(engine) as session:
        notified_streamers = session.scalars(
            select(Streamer.streamer_name).join(Streamer.user_subscriptions).where(
                UserSubscription.user_id == str(ctx.author.id),
                UserSubscription.guild_id == str(ctx.guild.id)
            )
        ).all()

        if notified_streamers:
            embed = discord.Embed(title="Your Notification Subscriptions",
                                  description=f"Here are the streamers you're subscribed to in {ctx.guild.name}:",
                                  color=0x00ff00)
            subscriptions_text = "\n".join([f"- {streamer_name}" for streamer_name in notified_streamers])
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
    """
    Change configuration of the bot server-wide.

    Parameters:
    - ctx (discord.Context): The context of the command invocation.

    Returns:
    - None
    """

    with Session(engine) as session:
        guild_config = session.scalar(select(Guild).where(Guild.guild_id == str(ctx.guild.id)))
        embed = create_config_embed(bot.get_channel(int(guild_config.notification_channel_id)).name,
                                    guild_config.notification_mode,
                                    str(guild_config.is_censored),
                                    bot.user.name,
                                    bot.user.display_avatar,
                                    ctx.author.display_name,
                                    ctx.author.display_avatar)
        await ctx.send(embed=embed)
    view = ConfigView(ctx.guild.owner.id, bot.user, ctx.guild)
    view.message = await ctx.send(view=view)
    await view.wait()

    # Write to DB here after getting values from view
    channel = get_first_sendable_text_channel(ctx.guild)
    with Session(engine) as session:
        session.execute(
            update(Guild).
            where(Guild.guild_id == str(ctx.guild.id)).
            values(
                notification_channel_id=str(view.channel.id or channel.id),
                notification_mode=view.notification_mode,
                is_censored=view.is_censored,
            )
        )
        session.commit()


@changeconfig.error
async def changeconfig_error(ctx, error):
    """
    Change configuration error handler function.

    Parameters:
    - ctx (discord.Context): The context of the command invocation.
    - error (Exception): The error that occurred during the execution of the command.

    Returns:
    - None
    """

    print(error)
    await ctx.send(
        f"{ctx.author.mention} You don't have permission to use this command...",
        ephemeral=True
    )


@bot.hybrid_command(name='test', description='for testing code when executed')
async def test(ctx):
    test_data = StreamOnlineEvent()
    test_data.event = StreamOnlineData()
    test_data.event.broadcaster_user_name = "Test"
    test_data.event.started_at = "2021-02-02"
    test_data.event.broadcaster_user_login = "test"
    embed_strategies = [
        PrigozhinEmbedStrategy()
    ]
    selected_embed_strategy = random.choice(embed_strategies)
    context = EmbedCreationContext(selected_embed_strategy)
    embed = context.create_embed(test_data, bot.user.name, bot.user.avatar)
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    """
    Handle the event when the bot is ready and connected to Discord.
    Initialize the Twitch API client, set up the EventSub webhook, subscribe to streamers, and synchronize the bot's internal state.

    Parameters:
    - None

    Returns:
    - None
    """

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
    print("Subscribing to streamers... Please wait...")
    await subscribe_all(webhook)
    print("Successfully subscribed to all streamers in the DB!")
    await bot.tree.sync()


if __name__ == '__main__':
    # When pytest imports this file this runs the bot without this check
    # since when importing the imported file is executed...
    bot.run(TOKEN)
