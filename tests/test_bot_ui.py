from datetime import datetime
from unittest import mock

import discord
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOnlineData

from bot.bot_ui import create_streamsnipe_draft_embed


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

        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

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

        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

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

        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

        assert "Report to your nearest stream sniping channel IMMEDIATELY!" in embed.description

    #  Embed description includes the text "Failure to do so is a felony and is punishable by fines up to $250,000 and/or prison terms up to 30 years."
    def test_embed_description_contains_failure_message(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"
        author_name = "Test Author"
        author_icon_url = "https://example.com/icon.png"

        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

        assert "Failure to do so is a felony and is punishable by fines up to $250,000 and/or prison terms up to 30 years." in embed.description

    #  Embed has a field with the label "Target"
    def test_embed_has_target_field(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

        # Assert that the embed has a field with the label "Target"
        assert embed.fields[0].name == "Target"

    #  Embed timestamp is set to the current time
    @mock.patch("bot.bot_ui.datetime", wraps=datetime)
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

        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

        assert embed.timestamp.replace(tzinfo=None) == datetime(2022, 1, 1, 12, 0, 0)

    #  Embed has a field with the label "Last Seen"
    def test_embed_has_last_seen_field(self, mocker):
        # Create a mock StreamOnlineEvent object
        mock_data = mocker.Mock(spec=StreamOnlineEvent)
        mock_data.event = mocker.Mock(spec=StreamOnlineData)
        mock_data.event.broadcaster_user_name = "test_user"
        mock_data.event.broadcaster_user_login = "test_user_login"
        mock_data.event.started_at = "2022-01-01 12:00:00"

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

        # Assert that the embed has a field with the label "Last Seen"
        assert any(field.name == "Last Seen" for field in embed.fields)

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
        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

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

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

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

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

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

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

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

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

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

        # Call the function under test
        embed = create_streamsnipe_draft_embed(mock_data, "author_name", "author_icon_url")

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

        embed = create_streamsnipe_draft_embed(mock_data, author_name, author_icon_url)

        assert embed.title == ":rotating_light: MANDATORY STREAM SNIPING DRAFT :rotating_light:"
