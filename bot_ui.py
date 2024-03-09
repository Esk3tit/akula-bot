import discord
from datetime import datetime
from discord import Interaction
from twitchAPI.object.eventsub import StreamOnlineEvent


def create_streamsnipe_draft_embed(data: StreamOnlineEvent, author_name, author_icon_url) -> discord.Embed:
    embed = discord.Embed(
        color=discord.Color.dark_gold(),
        description=f'You have been drafted to stream snipe {data.event.broadcaster_user_name}\n\n'
                    f'Report to your nearest stream sniping channel IMMEDIATELY!\n\n'
                    f'Failure to do so is a felony and is punishable by fines up to $250,000 '
                    f'and/or prison terms up to 30 years. :saluting_face:',
        title=':rotating_light: MANDATORY STREAM SNIPING DRAFT :rotating_light:',
        timestamp=datetime.now()
    )
    embed.set_author(name=author_name, icon_url=author_icon_url)
    embed.set_thumbnail(
        url='https://media.istockphoto.com/id/893424506/vector/smiley-saluting-in-army.jpg?s=612x612&w=0&k=20&c=eJfX306BVuNLZFTJGmmO6xP1Hd6Xw3NVyvRkBHi0NsQ=')
    embed.set_image(url='https://i.imgur.com/beTJRFF.png')

    embed.add_field(name='Target', value=f'`{data.event.broadcaster_user_name}`', inline=False)
    embed.add_field(name='Last Seen', value=f'`{data.event.started_at}`')
    embed.add_field(name='Link', value=f'Click [Me](https://www.twitch.tv/{data.event.broadcaster_user_login})')
    return embed


def create_config_embed(
        channel_name: str,
        channel_mode: str,
        author_name: str,
        author_icon_url: discord.Asset,
        embed_author: str,
        embed_author_icon: discord.Asset
) -> discord.Embed:
    embed = discord.Embed(
        title="What's up chat! 👋",
        description="Use the select menu options below to configure me for your server and then hit Save!",
        color=0x00FFFF
    )
    embed.set_author(name=author_name, icon_url=author_icon_url)
    embed.add_field(name='Current Notification Channel', value=channel_name, inline=False)
    embed.add_field(name='Current Notification Channel Mode', value=channel_mode, inline=False)
    embed.set_footer(text=f"Requested by {embed_author}", icon_url=embed_author_icon)
    return embed


def create_config_confirmation_embed(
        channel_name: str,
        channel_mode: str,
        author_name: str,
        author_icon_url: discord.Asset,
) -> discord.Embed:
    embed = discord.Embed(title='Akula Bot Configuration',
                          description=f'The following settings have been saved...',
                          timestamp=datetime.now(), color=discord.Color.green())
    embed.set_author(name=author_name, icon_url=author_icon_url)
    embed.add_field(name='Notification Channel', value=channel_name, inline=False)
    embed.add_field(name='Notification Channel Mode', value=channel_mode, inline=False)
    return embed


class ConfigView(discord.ui.View):
    def __init__(
            self,
            owner_id,
            embed_author: discord.ClientUser,
            guild: discord.Guild,
            timeout=None
    ):
        self.owner_id = owner_id
        self.embed_author = embed_author
        self.guild = guild
        self.channel = None
        self.notification_mode = 'optin'
        super().__init__(timeout=timeout)

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder='Notification Channel'
    )
    async def select_channels(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.channel = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder='Notification Mode',
        options=[
            discord.SelectOption(
                label='Opt-In',
                value='optin',
                description='The user must opt-in to get notifications by using the `!notify` command. Notifications mention users separately.',
                default=True
            ),
            discord.SelectOption(
                label='Global',
                value='global',
                description='The bot will mention `@everyone` or `@here` if it has permissions when posting notifications.',
                default=False
            ),
            discord.SelectOption(
                label='Passive',
                value='passive',
                description='The bot will just post the notifications in the designated notification channel without mentioning anyone.',
                default=False
            )
        ]
    )
    async def select_mode(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.notification_mode = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(emoji='💾', style=discord.ButtonStyle.primary, label='Save')
    async def save_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable selects and button
        self.children[0].disabled = True
        self.children[1].disabled = True
        self.children[2].disabled = True
        await self.disable_all_items()
        embed = create_config_confirmation_embed(
            self.channel.name,
            self.notification_mode,
            self.embed_author.name,
            self.embed_author.avatar
        )
        await interaction.response.send_message('Configuration settings saved!', embed=embed, ephemeral=True)
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.owner_id
