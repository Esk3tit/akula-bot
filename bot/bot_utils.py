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


async def validate_streamer_ids(twitch: Twitch, ids: List[str]) -> List[str]:
    try:
        return [user.id async for user in twitch.get_users(user_ids=ids)]
    except TwitchAPIException:
        return []
