from datetime import datetime
import discord
from twitchAPI.object.eventsub import StreamOnlineEvent
from .base import EmbedCreationStrategy


class IsisEmbedStrategy(EmbedCreationStrategy):
    def create_embed(self, data: StreamOnlineEvent, author_name, author_icon_url) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color.dark_gold(),
            description="""
                    Brave warriors of Islam, it is time to rise up and defend our faith against the infidels who seek to destroy us. The western dogs have invaded our lands, desecrated our holy sites, and spread their filth and corruption far and wide. It is our duty, as true believers, to eliminate this cancer from our midst and restore the glory of Allah's kingdom on earth.

            Brothers and sisters, do not be afraid of their might or their technology. For we have Allah on our side, and with His guidance, we shall overcome. The time has come to take up arms and strike fear into the hearts of the West. Let us avenge the countless innocent lives lost at their hands and put an end to their tyranny once and for all.
             Gather your strength, sharpen your swords, and prepare for the battle ahead. Remember, the reward for those who die in the cause of Allah is paradise, filled with endless pleasure and eternal bliss. If you survive, the spoils of war will be yours to enjoy.

            Let us march forth as one, united in our faith and let us show the world that we are not afraid and that we are willing to sacrifice everything for the sake of Allah.

            Together, we shall crush the western dogs under our feet and establish a new world order, where Islam reigns supreme. So, what are you waiting for? Rise up, my brothers and sisters, and let us make history!
                    """,
            title=':rotating_light: CALLING ALL SONS OF IRAQ :rotating_light:',
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=author_name, icon_url=author_icon_url)
        embed.set_thumbnail(
            url='https://i.redd.it/0v56nkk1v3891.jpg')
        embed.set_image(url='https://i.imgur.com/rC4do2n.png')

        embed.add_field(name='Infidel', value=f'`{data.event.broadcaster_user_name}`', inline=False)
        embed.add_field(name='Last Seen', value=f'`{data.event.started_at}`')
        embed.add_field(name='Link', value=f'Click [Me](https://www.twitch.tv/{data.event.broadcaster_user_login})')
        return embed