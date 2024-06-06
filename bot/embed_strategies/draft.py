from datetime import datetime
import discord
from twitchAPI.object.eventsub import StreamOnlineEvent
from .base import EmbedCreationStrategy


class DraftEmbedStrategy(EmbedCreationStrategy):
    thumbnail_url = 'https://media.istockphoto.com/id/893424506/vector/smiley-saluting-in-army.jpg?s=612x612&w=0&k=20&c=eJfX306BVuNLZFTJGmmO6xP1Hd6Xw3NVyvRkBHi0NsQ='
    image_url = 'https://i.imgur.com/beTJRFF.png'

    def create_embed(self,
                     data: StreamOnlineEvent,
                     author_name,
                     author_icon_url
                     ) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color.dark_gold(),
            description=f'You have been drafted to stream snipe {data.event.broadcaster_user_name}\n\n'
                        f'Report to your nearest stream sniping channel IMMEDIATELY!\n\n'
                        f'Failure to do so is a felony and is punishable by fines up to $250,000 '
                        f'and/or prison terms up to 30 years. :saluting_face:',
            title=':rotating_light: MANDATORY STREAM SNIPING DRAFT :rotating_light:',
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=author_name, icon_url=author_icon_url)
        embed.set_thumbnail(url=DraftEmbedStrategy.thumbnail_url)
        embed.set_image(url=DraftEmbedStrategy.image_url)

        embed.add_field(name='Target', value=f'`{data.event.broadcaster_user_name}`', inline=False)
        embed.add_field(name='Last Seen', value=f'`{data.event.started_at}`')
        embed.add_field(name='Link', value=f'Click [Me](https://www.twitch.tv/{data.event.broadcaster_user_login})')
        return embed
