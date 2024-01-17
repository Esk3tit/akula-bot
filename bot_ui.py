import discord
from datetime import datetime
from discord import ui, Interaction


class ConfigButtonView(discord.ui.View):
    channel = None

    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Configure Bot", style=discord.ButtonStyle.primary, custom_id="configure_bot")
    async def configure_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_config_modal = GuildConfig()
        await interaction.response.send_modal(guild_config_modal)
        self.channel = guild_config_modal.channel.values
        self.stop()


class GuildConfig(ui.Modal, title='Akula Bot Server Configuration'):
    # channel = ui.ChannelSelect(channel_types=[discord.ChannelType.text],
    #                            placeholder='Select channel for bot to send notifications to')
    channel = ui.ChannelSelect(placeholder='Select channel for bot to send notifications to')

    async def on_submit(self, interaction: Interaction) -> None:
        embed = discord.Embed(title=self.title, description=f'Notifications channel: {self.channel.values}',
                              timestamp=datetime.now(), color=discord.Color.blue())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
        await interaction.response.send_message(embed=embed)
