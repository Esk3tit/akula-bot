from typing import List

import discord
from twitchAPI.twitch import Twitch
from twitchAPI.type import TwitchAPIException


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
