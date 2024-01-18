import discord
from datetime import datetime
from discord import ui, Interaction


class ConfigView(discord.ui.View):
    def __init__(self, owner_id, embed_author: discord.ClientUser, timeout=None):
        self.owner_id = owner_id
        self.embed_author = embed_author
        self.channel = None
        super().__init__(timeout=timeout)

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text])
    async def select_channels(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.channel = select.values[0]
        embed = discord.Embed(title='Akula Bot Configuration',
                              description=f'Notifications channel: {self.channel.name}',
                              timestamp=datetime.now(), color=discord.Color.blue())
        embed.set_author(name=self.embed_author.name, icon_url=self.embed_author.avatar)
        return await interaction.response.send_message(
            f'You selected {self.channel.name} for stream snipe notifications',
            embed=embed
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.owner_id
