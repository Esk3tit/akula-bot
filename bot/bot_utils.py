from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Context
from twitchAPI.twitch import Twitch
from twitchAPI.type import TwitchAPIException
from sqlalchemy import select, Engine
from sqlalchemy.orm import Session
from bot.models import Guild, GetUsersStreamer


def is_owner_or_optin_mode(engine: Engine):
    """
    Check if the author of a command is the owner of the guild or if the guild's notification mode is 'optin'.
    Used as a decorator for checking permissions of command handlers

    Parameters:
    - engine (Engine): The SQLAlchemy engine to use for database operations.
    - ctx (Context): The context of the command being invoked.

    Returns:
    - bool: True if the author is the guild owner or the guild's notification mode is 'optin', False otherwise.
    """
    def predicate(ctx: Context) -> bool:
        with Session(engine) as session:
            guild_notif_mode = session.scalar(
                select(Guild.notification_mode).where(Guild.guild_id == str(ctx.guild.id)))
            return guild_notif_mode.lower() == 'optin' or ctx.author.id == ctx.guild.owner.id
    return commands.check(predicate)


def is_owner(interaction: discord.Interaction) -> bool:
    """
    Check if the author of an interaction is the owner of the guild.
    Used as a decorator for checking permissions of command handlers

    Parameters:
    - interaction (discord.Interaction): The interaction object representing the command being invoked.

    Returns:
    - bool: True if the author of the interaction is the guild owner, False otherwise.
    """

    if interaction.guild is None or interaction.user is None or interaction.guild.owner is None:
        return False
    user_is_owner = interaction.user.id == interaction.guild.owner.id
    print(f'Command Level is owner check: {user_is_owner}')
    return user_is_owner


def get_first_sendable_text_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    """
    Returns the first text channel in the guild that the bot has permission to send messages to.

    Parameters:
    - guild (discord.Guild): The guild to search for a sendable text channel.

    Returns:
    - Optional[discord.TextChannel]: The first text channel in the guild that the bot can send messages to, or None if no such channel is found.
    """

    return next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages), None)


async def streamer_get_ids_names_from_logins(twitch: Twitch, broadcaster_logins: list[str]) -> list[GetUsersStreamer]:
    """
    Get a list of GetUsersStreamer objects by providing a list of broadcaster logins.

    Parameters:
    - twitch (Twitch): An instance of the Twitch class.
    - broadcaster_logins (list[str]): A list of broadcaster logins for which to retrieve user information.

    Returns:
    - list[GetUsersStreamer]: A list of GetUsersStreamer objects containing the id and name of each broadcaster.
    """

    try:
        return [GetUsersStreamer(user.id, user.display_name) async for user in twitch.get_users(logins=broadcaster_logins)]
    except TwitchAPIException as e:
        print(e)
        return []


async def validate_streamer_ids_get_names(twitch: Twitch, ids: list[str]) -> list[GetUsersStreamer]:
    """
    Validate the given list of user ids by fetching their display names from the Twitch API.

    Parameters:
    - twitch (Twitch): An instance of the Twitch class used to make API calls.
    - ids (list[str]): A list of user ids to validate.

    Returns:
    - list[GetUsersStreamer]: A list of GetUsersStreamer objects containing the id and display name of each user.
    """

    try:
        return [GetUsersStreamer(user.id, user.display_name) async for user in twitch.get_users(user_ids=ids)]
    except TwitchAPIException as e:
        print(e)
        return []
