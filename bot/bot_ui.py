from typing import Optional

import discord
from datetime import datetime
from discord import Interaction
from twitchAPI.object.eventsub import StreamOnlineEvent


class EmbedCreationContext:
    """
    Class representing a context for creating Discord embeds.

    Parameters:
    - strategy: The strategy object used for creating the embeds.

    Attributes:
    - _strategy: The strategy object used for creating the embeds.

    Methods:
    - create_embed(data, author_name, author_icon_url): Creates a Discord embed using the provided data, author name, and author icon URL.
    - create_embed_custom_images(data, author_name, author_icon_url, thumbnail_url, image_url): Creates a Discord embed with custom thumbnail and image URLs.
    """

    def __init__(self, strategy):
        self._strategy = strategy

    def create_embed(self,
                     data: StreamOnlineEvent,
                     author_name,
                     author_icon_url
                     ) -> discord.Embed:
        return self._strategy.create_embed(data, author_name, author_icon_url)

    def create_embed_custom_images(self,
                                   data: StreamOnlineEvent,
                                   author_name,
                                   author_icon_url,
                                   thumbnail_url,
                                   image_url
                                   ) -> discord.Embed:
        return self._strategy.create_embed(data, author_name, author_icon_url, thumbnail_url, image_url)


def create_config_embed(
        channel_name: str,
        channel_mode: str,
        is_censored: str,
        author_name: str,
        author_icon_url: discord.Asset,
        embed_author: str,
        embed_author_icon: discord.Asset
) -> discord.Embed:
    """
    Create an embed for configuring the bot.

    Parameters:
    - channel_name (str): The name of the current notification channel.
    - channel_mode (str): The mode of the current notification channel.
    - is_censored (str): The current SFW/Censorship notification status.
    - author_name (str): The name of the author.
    - author_icon_url (discord.Asset): The icon URL of the author.
    - embed_author (str): The name of the embed author.
    - embed_author_icon (discord.Asset): The icon URL of the embed author.

    Returns:
    - discord.Embed: The embed created for configuring the bot.
    """

    embed = discord.Embed(
        title="What's up chat! 👋",
        description="Use the select menu options below to configure me for your server and then hit Save!",
        color=0x00FFFF
    )
    embed.set_author(name=author_name, icon_url=author_icon_url)
    embed.add_field(name='Current Notification Channel', value=channel_name, inline=False)
    embed.add_field(name='Current Notification Channel Mode', value=channel_mode, inline=False)
    embed.add_field(name='Current SFW/Censorship Notification Status', value=is_censored, inline=False)
    embed.set_footer(text=f"Requested by {embed_author}", icon_url=embed_author_icon)
    return embed


def create_config_confirmation_embed(
        channel_name: str,
        channel_mode: str,
        is_censored: str,
        author_name: str,
        author_icon_url: discord.Asset,
) -> discord.Embed:
    """
    Creates an embed for confirming the configuration settings.

    Parameters:
    - channel_name (str): The name of the notification channel.
    - channel_mode (str): The mode of the notification channel.
    - is_censored (str): Indicates if the notifications are censored or not.
    - author_name (str): The name of the author.
    - author_icon_url (discord.Asset): The URL of the author's icon.

    Returns:
    - discord.Embed: An embed displaying the configuration settings.
    """

    embed = discord.Embed(title='Akula Bot Configuration',
                          description=f'The following settings have been saved...',
                          timestamp=datetime.now(), color=discord.Color.green())
    embed.set_author(name=author_name, icon_url=author_icon_url)
    embed.add_field(name='Notification Channel', value=channel_name, inline=False)
    embed.add_field(name='Notification Channel Mode', value=channel_mode, inline=False)
    embed.add_field(name='SFW/Censored Notifications?', value=is_censored, inline=False)
    return embed


class ConfigView(discord.ui.View):
    """
    Represents a custom Discord UI view for configuring bot settings.

    Parameters:
    - owner_id (int): The ID of the owner of the configuration view.
    - embed_author (discord.ClientUser): The author of the embed associated with the configuration.
    - guild (discord.Guild): The guild where the configuration is taking place.
    - timeout (Optional[int]): The timeout duration for the view.

    Attributes:
    - owner_id (int): The ID of the owner of the configuration view.
    - embed_author (discord.ClientUser): The author of the embed associated with the configuration.
    - guild (discord.Guild): The guild where the configuration is taking place.
    - channel (Optional[discord.TextChannel]): The selected notification channel.
    - message (Optional[discord.Message]): The message associated with the view.
    - notification_mode (str): The selected notification mode ('optin', 'global', 'passive').
    - is_censored (bool): Indicates if notifications are censored or not.

    Methods:
    - disable_all_items(): Disables all items in the view.
    - select_channels(interaction, select): Selects a notification channel.
    - select_mode(interaction, select): Selects a notification mode.
    - select_censorship(interaction, select): Selects whether notifications are censored.
    - save_config(interaction, button): Saves the configuration settings and displays a confirmation message.
    - interaction_check(interaction: Interaction) -> bool: Checks if the interaction user is the owner of the view.

    Returns:
    - None
    """

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
        self.message = None
        self.notification_mode = 'optin'
        self.is_censored = False
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
                description='Users must opt-in for notifications with the `!notify` command. Notifications will mention user.',
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
                description='The bot will post notifications in the designated notification channel without mentioning anyone.',
                default=False
            )
        ]
    )
    async def select_mode(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.notification_mode = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder='Enable Safe For Work/Censored Notifications?',
        options=[
            discord.SelectOption(
                label='Yes',
                value='true',
                description='Safe For Work Notifications will be shown instead of the special randomly selected ones',
                default=False
            ),
            discord.SelectOption(
                label='No',
                value='false',
                description='Special randomly selected notifications will be shown (default)',
                default=True
            )
        ]
    )
    async def select_censorship(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.is_censored = True if select.values[0] == 'true' else False
        await interaction.response.defer()

    @discord.ui.button(emoji='💾', style=discord.ButtonStyle.primary, label='Save')
    async def save_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable selects and button
        await self.disable_all_items()
        embed = create_config_confirmation_embed(
            self.channel.name,
            self.notification_mode,
            str(self.is_censored),
            self.embed_author.name,
            self.embed_author.avatar
        )
        await interaction.response.send_message('Configuration settings saved!', embed=embed, ephemeral=True)
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        print(f'View Level is owner check: {interaction.user.id == self.owner_id}')
        return interaction.user.id == self.owner_id
