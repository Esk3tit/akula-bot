from datetime import datetime
import discord
from twitchAPI.object.eventsub import StreamOnlineEvent
from .base import EmbedCreationStrategy


class SafeForWorkEmbedStrategy(EmbedCreationStrategy):
    def create_embed(self,
                     data: StreamOnlineEvent,
                     author_name,
                     author_icon_url,
                     thumbnail_url,
                     image_url
                     ) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color.dark_green(),
            description='Streamer is currently live and ripe for sniping :relaxed:',
            title=f':rotating_light: {data.event.broadcaster_user_name} is LIVE! :rotating_light:',
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=author_name, icon_url=author_icon_url)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_image(url=image_url)

        embed.add_field(name='Target', value=f'`{data.event.broadcaster_user_name}`', inline=False)
        embed.add_field(name='Stream Started', value=f'`{data.event.started_at}`')
        embed.add_field(name='Link', value=f'Click [Here](https://www.twitch.tv/{data.event.broadcaster_user_login})')
        return embed