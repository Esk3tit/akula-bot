from abc import ABC, abstractmethod

import discord
from twitchAPI.object.eventsub import StreamOnlineEvent


class EmbedCreationStrategy(ABC):
    @abstractmethod
    def create_embed(self, data: StreamOnlineEvent, author_name, author_icon_url, thumbnail_url, image_url) -> discord.Embed:
        pass
