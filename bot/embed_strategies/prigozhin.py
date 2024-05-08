from datetime import datetime
import discord
from twitchAPI.object.eventsub import StreamOnlineEvent
from .base import EmbedCreationStrategy


class PrigozhinEmbedStrategy(EmbedCreationStrategy):
    def create_embed(self, data: StreamOnlineEvent, author_name, author_icon_url) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color.dark_magenta(),
            description="""
            I represent the private military company, Wagner, maybe you've heard of it. The war is tough, doesn't look anything like the Chechen war.
            
            You all are the scum of society, but I'm giving you a chance to redeem yourselves and prove that you are useful to your nation. However,
            there are some important things that you worms need to be aware of before you commit yourselves to the frontlines.
            
            The first sin is desertion. No one backs out and no one retreats. No one turns themselves in. When you will be undergoing training, they will tell you about the two grenades you'll have to have if you turn captive.
            The second thing is drugs and alcohol. During all the time you are with us, and for six months you will be with us in the combat zone.
            And the third is marauding, including any sexual contacts with local women, flora, fauna, men, anything.
            
            The minimum age that we accept is 22. If you are younger, then we need a paper signed by one of your relatives saying they don't mind.
            Maximum age is approximately 50 but if you are strong we will do basic tests right here during the interviews, we see how strong you are.
            
            For the dead, the bodies will be delivered to locations that you indicate in your will, to your relatives or they are buried wherever you say. Everyone is buried in the Alleys of Heroes in the cities where they exist. Those who don't know where to bury them, we bury them near the Wagner's Chapel in Goryachiy Kluch.

            Next, in six months you go home after receiving pardon. Those who want to stay with us can stay with us. So you have no option to return to prison. Those who arrive to the frontline and on the first day say this is not a place for them we mark them as deserters and that is followed by an execution by firing squad.
            
            Guys, if you have questions ask. After that you line up for the interviews. You have five minutes to make a decision.
            When we leave, that time is up. After that it's all up to luck. Regarding trust and guarantees, do you have anyone who can get you out of prison alive?
            There are two who can get you out of prison - Allah and God. I am taking you out of here alive.
            But it's not always that I bring you back alive. So, guys, any questions?
            """,
            title=':rotating_light: ATTENTION WORTHLESS MAGGOTS :rotating_light:',
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=author_name, icon_url=author_icon_url)
        embed.set_thumbnail(
            url='https://i.imgur.com/egYCwpv.jpg')
        embed.set_image(
            url='https://www.aljazeera.com/wp-content/uploads/2023/08/AP23235625627301-1692854633.jpg?resize=730%2C410&quality=80')

        embed.add_field(name='Target', value=f'`{data.event.broadcaster_user_name}`', inline=False)
        embed.add_field(name='Last Seen', value=f'`{data.event.started_at}`')
        embed.add_field(name='Link', value=f'Click [Me](https://www.twitch.tv/{data.event.broadcaster_user_login})')
        return embed
