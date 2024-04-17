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
    def predicate(ctx: Context) -> bool:
        with Session(engine) as session:
            guild_notif_mode = session.scalar(
                select(Guild.notification_mode).where(Guild.guild_id == str(ctx.guild.id)))
            return guild_notif_mode == 'optin' or ctx.author.id == ctx.guild.owner.id
    return commands.check(predicate)


def is_owner(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or interaction.user is None or interaction.guild.owner is None:
        return False
    user_is_owner = interaction.user.id == interaction.guild.owner.id
    print(f'Command Level is owner check: {user_is_owner}')
    return user_is_owner


def get_first_sendable_text_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    """
    Get the first text channel in the guild that the bot has permission to send messages to.

    Args:
        guild (discord.Guild): The guild to search for the text channel in.

    Returns:
        discord.TextChannel | None: The first text channel that the bot can send messages to, or None if no such channel exists.
    """
    return next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages), None)


async def streamer_get_ids_names_from_logins(twitch: Twitch, broadcaster_logins: list[str]) -> list[GetUsersStreamer]:
    try:
        return [GetUsersStreamer(user.id, user.display_name) async for user in twitch.get_users(logins=broadcaster_logins)]
    except TwitchAPIException as e:
        print(e)
        return []


async def validate_streamer_ids_get_names(twitch: Twitch, ids: list[str]) -> list[GetUsersStreamer]:
    try:
        return [GetUsersStreamer(user.id, user.display_name) async for user in twitch.get_users(user_ids=ids)]
    except TwitchAPIException as e:
        print(e)
        return []
