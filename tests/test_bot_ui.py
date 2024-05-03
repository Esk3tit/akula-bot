from datetime import datetime
from unittest import mock

import discord
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOnlineData
from bot.embed_strategies.draft import DraftEmbedStrategy
from bot.embed_strategies.isis import IsisEmbedStrategy


class TestCreateStreamsnipeDraftEmbed:

    #  Function returns a discord.Embed object
    def test_returns_embed_object(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "John Doe"
        author_icon_url = "https://example.com/icon.png"

        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert isinstance(embed, discord.Embed)

    #  Embed has a dark gold color
    def test_embed_has_dark_gold_color(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "John Doe"
        author_icon_url = "https://example.com/icon.png"

        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert embed.color == discord.Color.dark_gold()

    #  Embed description includes the text "Report to your nearest stream sniping channel IMMEDIATELY!"
    def test_embed_description_includes_report_text(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert "Report to your nearest stream sniping channel IMMEDIATELY!" in embed.description

    #  Embed timestamp is set to the current time
    @mock.patch("bot.embed_strategies.draft.datetime", wraps=datetime)
    def test_embed_timestamp_is_set_to_current_time(self, mock_datetime, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        mock_datetime.utcnow.return_value=datetime(2022, 1, 1, 12, 0, 0)
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert embed.timestamp.replace(tzinfo=None) == datetime(2022, 1, 1, 12, 0, 0)

    #  Embed has an author name and icon
    def test_embed_has_author_name_and_icon(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"

        # Create mock author name and icon URL
        author_name = "test_author"
        author_icon_url = "https://example.com/test_icon.png"

        # Call the function under test
        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the embed has the correct author name and icon
        assert embed.author.name == author_name
        assert embed.author.icon_url == author_icon_url

    #  Embed has a thumbnail with a saluting smiley
    def test_embed_has_saluting_smiley_thumbnail(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert the thumbnail URL is correct
        assert embed.thumbnail.url == 'https://media.istockphoto.com/id/893424506/vector/smiley-saluting-in-army.jpg?s=612x612&w=0&k=20&c=eJfX306BVuNLZFTJGmmO6xP1Hd6Xw3NVyvRkBHi0NsQ='

    #  Embed has an image with a picture of a draft notice
    def test_embed_has_draft_image(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the embed has the correct image URL
        assert embed.image.url == 'https://i.imgur.com/beTJRFF.png'

    #  Embed has a field with the target's username
    def test_embed_has_target_username_field(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        mock_data.event.broadcaster_user_name = "target_username"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the embed has a field with the target's username
        assert embed.fields[0].name == "Target"
        assert embed.fields[0].value == "`target_username`"

    #  Embed has a field with the target's last seen time
    def test_embed_has_last_seen_field(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.started_at = "2022-01-01T00:00:00Z"
        mock_data.event.broadcaster_user_login = "test_user_login"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the last seen field is present in the embed
        assert embed.fields[1].name == "Last Seen"
        assert embed.fields[1].value == "`2022-01-01T00:00:00Z`"

    #  Embed has a field with a clickable link to the target's Twitch channel
    def test_embed_has_clickable_link(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 00:00:00"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert the embed has the expected field with a clickable link
        expected_link = f'Click [Me](https://www.twitch.tv/{mock_data.event.broadcaster_user_login})'
        assert embed.fields[2].value == expected_link

    #  Embed has a title with the text "MANDATORY STREAM SNIPING DRAFT"
    def test_embed_title(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = DraftEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert embed.title == ":rotating_light: MANDATORY STREAM SNIPING DRAFT :rotating_light:"


class TestCreateStreamsnipeISISEmbed:

    #  Function returns a discord.Embed object
    def test_returns_embed_object(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "John Doe"
        author_icon_url = "https://example.com/icon.png"

        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert isinstance(embed, discord.Embed)

    #  Embed has a dark gold color
    def test_embed_has_dark_gold_color(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "John Doe"
        author_icon_url = "https://example.com/icon.png"

        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert embed.color == discord.Color.dark_gold()

    #  Embed description includes the text "Report to your nearest stream sniping channel IMMEDIATELY!"
    def test_embed_description_includes_call_to_action_text(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert "Brave warriors of Islam, it is time to rise up and defend our faith against the infidels who seek to destroy us." in embed.description

    #  Embed timestamp is set to the current time
    @mock.patch("bot.embed_strategies.isis.datetime", wraps=datetime)
    def test_embed_timestamp_is_set_to_current_time(self, mock_datetime, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        mock_datetime.utcnow.return_value=datetime(2022, 1, 1, 12, 0, 0)
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert embed.timestamp.replace(tzinfo=None) == datetime(2022, 1, 1, 12, 0, 0)

    #  Embed has an author name and icon
    def test_embed_has_author_name_and_icon(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"

        # Create mock author name and icon URL
        author_name = "test_author"
        author_icon_url = "https://example.com/test_icon.png"

        # Call the function under test
        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the embed has the correct author name and icon
        assert embed.author.name == author_name
        assert embed.author.icon_url == author_icon_url

    #  Embed has a thumbnail with a saluting smiley
    def test_embed_has_isis_flag_thumbnail(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert the thumbnail URL is correct
        assert embed.thumbnail.url == 'https://i.redd.it/0v56nkk1v3891.jpg'

    #  Embed has an image with a picture of a draft notice
    def test_embed_has_draft_image(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the embed has the correct image URL
        assert embed.image.url == 'https://i.imgur.com/rC4do2n.png'

    #  Embed has a field with the infidel's username
    def test_embed_has_infidel_username_field(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        mock_data.event.broadcaster_user_name = "infidel_username"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the embed has a field with the target's username
        assert embed.fields[0].name == "Infidel"
        assert embed.fields[0].value == "`infidel_username`"

    #  Embed has a field with the target's last seen time
    def test_embed_has_last_seen_field(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.started_at = "2022-01-01T00:00:00Z"
        mock_data.event.broadcaster_user_login = "test_user_login"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert that the last seen field is present in the embed
        assert embed.fields[1].name == "Last Seen"
        assert embed.fields[1].value == "`2022-01-01T00:00:00Z`"

    #  Embed has a field with a clickable link to the target's Twitch channel
    def test_embed_has_clickable_link(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 00:00:00"
        author_name = "author_name"
        author_icon_url = "author_icon_url"

        # Call the function under test
        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        # Assert the embed has the expected field with a clickable link
        expected_link = f'Click [Me](https://www.twitch.tv/{mock_data.event.broadcaster_user_login})'
        assert embed.fields[2].value == expected_link

    #  Embed has a title with the text "CALLING ALL SONS OF IRAQ"
    def test_embed_title(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = IsisEmbedStrategy().create_embed(mock_data, author_name, author_icon_url)

        assert embed.title == ":rotating_light: CALLING ALL SONS OF IRAQ :rotating_light:"
