from typing import List

import discord
from discord.ext import commands
from discord.ext.commands import Context
from twitchAPI.twitch import Twitch
from twitchAPI.type import TwitchAPIException
from sqlalchemy import select, Engine
from sqlalchemy.orm import Session
from bot.models import Guild


def is_owner_or_optin_mode(engine: Engine):
    def predicate(ctx: Context) -> bool:
        with Session(engine) as session:
            guild_notif_mode = session.scalar(
                select(Guild.notification_mode).where(Guild.guild_id == str(ctx.guild.id)))
            return guild_notif_mode == 'optin' or ctx.author.id == ctx.guild.owner.id
    return commands.check(predicate)


def is_owner(interaction: discord.Interaction) -> bool:
    print(f'Command Level is owner check: {interaction.user.id == interaction.guild.owner.id}')
    return interaction.user.id == interaction.guild.owner.id


def get_first_text_channel(guild: discord.Guild) -> discord.TextChannel | None:
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel
    return None


async def streamer_get_names_from_ids(twitch: Twitch, ids: list[str]):
    try:
        return {user.id: user.display_name async for user in twitch.get_users(user_ids=ids)}
    except TwitchAPIException as e:
        print(e)
        return []


async def streamer_get_ids_from_logins(twitch: Twitch, broadcaster_logins: list[str]):
    try:
        return [user.id async for user in twitch.get_users(logins=broadcaster_logins)]
    except TwitchAPIException as e:
        print(e)
        return []


async def validate_streamer_ids(twitch: Twitch, ids: List[str]) -> List[str]:
    try:
        return [user.id async for user in twitch.get_users(user_ids=ids)]
    except TwitchAPIException as e:
        print(e)
        return []
