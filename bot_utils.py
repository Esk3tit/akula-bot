import discord


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == interaction.guild.owner_id


def get_first_text_channel(guild: discord.Guild) -> discord.TextChannel | None:
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel
    return None
