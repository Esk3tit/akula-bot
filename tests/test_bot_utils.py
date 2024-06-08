from bot.bot_utils import validate_streamer_ids_get_names, streamer_get_ids_names_from_logins, \
    get_first_sendable_text_channel, is_owner, is_owner_or_optin_mode
from twitchAPI.twitch import Twitch
from twitchAPI.type import TwitchAPIException
from twitchAPI.object.api import TwitchUser
from typing import AsyncGenerator
import pytest
import discord

from bot.models import GetUsersStreamer


@pytest.mark.asyncio
class TestStreamerGetIdsFromLogins:

    #  Returns a list of GetUsersStreamers when given a list of valid broadcaster logins
    async def test_valid_broadcaster_logins(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user1 = mocker.Mock(spec=TwitchUser, id='123', display_name='Broadcaster1')
        mock_user2 = mocker.Mock(spec=TwitchUser, id='456', display_name='Broadcaster2')
        mock_user3 = mocker.Mock(spec=TwitchUser, id='789', display_name='Broadcaster3')
        mock_logins = ['broadcaster1', 'broadcaster2', 'broadcaster3']

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            for user in [mock_user1, mock_user2, mock_user3]:
                yield user

        mock_twitch.get_users.return_value = mock_get_users(logins=mock_logins)

        # Call the function under test
        result = await streamer_get_ids_names_from_logins(mock_twitch, mock_logins)

        # Assert the result
        assert result == [
            GetUsersStreamer(id='123', name='Broadcaster1'),
            GetUsersStreamer(id='456', name='Broadcaster2'),
            GetUsersStreamer(id='789', name='Broadcaster3')
        ]
        mock_twitch.get_users.assert_called_once_with(logins=mock_logins)

    #  Returns an empty list when given a list of invalid broadcaster logins
    async def test_invalid_broadcaster_logins(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        # Configure the mock twitch.get_users method to raise a TwitchAPIException
        mock_twitch.get_users.side_effect = TwitchAPIException('API error')
        mock_invalid_logins = ['invalid1', 'invalid2', 'invalid3']

        # Call the function under test
        result = await streamer_get_ids_names_from_logins(mock_twitch, mock_invalid_logins)

        # Assert the result
        assert result == []
        mock_twitch.get_users.assert_called_once_with(logins=mock_invalid_logins)

    #  Returns an empty list when given a single invalid broadcaster login
    async def test_single_invalid_broadcaster_login(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock()
        # Configure the mock twitch.get_users method to raise a TwitchAPIException
        mock_twitch.get_users.side_effect = TwitchAPIException('API error')
        mock_invalid_login = ['invalid']

        # Call the function under test
        result = await streamer_get_ids_names_from_logins(mock_twitch, mock_invalid_login)

        # Assert the result
        assert result == []
        mock_twitch.get_users.assert_called_once_with(logins=mock_invalid_login)

    #  Returns a list of GetUsersStreamers when given a single valid broadcaster login
    async def test_single_valid_broadcaster_login(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user = mocker.Mock(spec=TwitchUser, id='123456789', display_name='Broadcaster')
        mock_login = ['broadcaster']

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            yield mock_user

        mock_twitch.get_users.return_value = mock_get_users(logins=mock_login)

        # Call the function under test
        result = await streamer_get_ids_names_from_logins(mock_twitch, mock_login)

        # Assert the result
        assert result == [
            GetUsersStreamer(id='123456789', name='Broadcaster')
        ]
        mock_twitch.get_users.assert_called_once_with(logins=mock_login)


@pytest.mark.asyncio
class TestValidateStreamerIds:

    #  The function returns a list of GetUsersStreamers when given a valid list of user ids.
    async def test_valid_user_ids(self, mocker):
        # Mock the Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user1 = mocker.Mock(spec=TwitchUser, id='123', display_name='Streamer1')
        mock_user2 = mocker.Mock(spec=TwitchUser, id='456', display_name='Streamer2')
        mock_user3 = mocker.Mock(spec=TwitchUser, id='789', display_name='Streamer3')
        mock_ids = ['123', '456', '789']

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            for user in [mock_user1, mock_user2, mock_user3]:
                yield user

        mock_twitch.get_users.return_value = mock_get_users(user_ids=mock_ids)

        # Call the function under test
        result = await validate_streamer_ids_get_names(mock_twitch, mock_ids)

        # Assert the result
        assert result == [
            GetUsersStreamer(id='123', name='Streamer1'),
            GetUsersStreamer(id='456', name='Streamer2'),
            GetUsersStreamer(id='789', name='Streamer3')
        ]
        mock_twitch.get_users.assert_called_once_with(user_ids=mock_ids)

    # The function returns a list of a single GetUsersStreamer when given a list of a single valid id
    async def test_valid_user_id(self, mocker):
        # Mock the Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user = mocker.Mock(spec=TwitchUser, id='123', display_name='Streamer1')
        mock_id = ['123']

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            yield mock_user

        mock_twitch.get_users.return_value = mock_get_users(user_ids=mock_id)

        # Call the function under test
        result = await validate_streamer_ids_get_names(mock_twitch, mock_id)

        # Assert the result
        assert result == [
            GetUsersStreamer(id='123', name='Streamer1'),
        ]
        mock_twitch.get_users.assert_called_once_with(user_ids=mock_id)

    #  The function returns an empty list when given a list of invalid user ids.
    async def test_invalid_user_ids(self, mocker):
        # Mock the Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_twitch.get_users.side_effect = TwitchAPIException()

        # Call the function under test
        ids = ['42069', '1488']
        result = await validate_streamer_ids_get_names(mock_twitch, ids)

        # Assert the result
        assert result == []
        mock_twitch.get_users.assert_called_once_with(user_ids=ids)

    #  The function returns an empty list when given a list of valid and invalid user ids.
    #  The invalid ids result in exception, so even with valid ids mixed in the entire API call is invalid
    async def test_valid_and_invalid_ids(self, mocker):
        # Mock the Twitch API response for get_users
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_twitch.get_users.side_effect = TwitchAPIException()

        ids = ['333', '666']

        # Call the function with a list of valid and invalid ids
        result = await validate_streamer_ids_get_names(mock_twitch, ids)

        # Assert that the result is a list of user ids
        assert result == []

        # Assert that get_users was called with the correct arguments
        mock_twitch.get_users.assert_called_once_with(user_ids=ids)


class TestGetFirstTextChannel:

    #  Returns the first text channel in the guild that the bot has permission to send messages to.
    def test_returns_first_text_channel(self, mocker):
        guild = mocker.Mock(spec=discord.Guild)
        channel1 = mocker.Mock(spec=discord.TextChannel)
        channel2 = mocker.Mock(spec=discord.TextChannel)
        channel3 = mocker.Mock(spec=discord.TextChannel)
        guild.text_channels = [channel1, channel2, channel3]
        channel1.permissions_for.return_value.send_messages = False
        channel2.permissions_for.return_value.send_messages = True
        channel3.permissions_for.return_value.send_messages = True

        result = get_first_sendable_text_channel(guild)

        assert result == channel2

    #  Returns None if the guild has no text channels.
    def test_returns_none_if_no_text_channels(self, mocker):
        guild = mocker.Mock(spec=discord.Guild)
        guild.text_channels = []

        result = get_first_sendable_text_channel(guild)

        assert result is None

    #  Returns None if the bot does not have permission to send messages in any text channel.
    def test_bot_without_permission(self, mocker):
        guild = mocker.Mock(spec=discord.Guild)
        text_channel1 = mocker.Mock(spec=discord.TextChannel)
        text_channel2 = mocker.Mock(spec=discord.TextChannel)
        text_channel3 = mocker.Mock(spec=discord.TextChannel)
        guild.text_channels = [text_channel1, text_channel2, text_channel3]

        text_channel1.permissions_for.return_value.send_messages = False
        text_channel2.permissions_for.return_value.send_messages = False
        text_channel3.permissions_for.return_value.send_messages = False

        result = get_first_sendable_text_channel(guild)

        assert result is None


class TestIsOwner:

    #  Returns True if the interaction user is the guild owner.
    def test_returns_true_if_interaction_user_is_guild_owner(self, mocker):
        interaction = mocker.Mock(spec=discord.Interaction)
        interaction.user.id = 123
        interaction.guild.owner.id = 123

        result = is_owner(interaction)
        assert result is True

    #  Returns False if the interaction user is not the guild owner.
    def test_returns_false_if_interaction_user_is_not_guild_owner(self, mocker):
        interaction = mocker.Mock(spec=discord.Interaction)
        interaction.user.id = 123
        interaction.guild.owner.id = 456

        result = is_owner(interaction)
        assert result is False

    #  Returns False if the interaction user is None.
    def test_returns_false_if_interaction_user_is_none(self, mocker):
        interaction = mocker.Mock(spec=discord.Interaction)
        interaction.user = None

        result = is_owner(interaction)
        assert result is False

    #  Returns False if the guild is None.
    def test_returns_false_if_guild_is_none(self, mocker):
        interaction = mocker.Mock(spec=discord.Interaction)
        interaction.guild = None

        result = is_owner(interaction)
        assert result is False

    #  Returns False if the guild owner is None.
    def test_returns_false_if_guild_owner_is_none(self, mocker):
        interaction = mocker.Mock(spec=discord.Interaction)
        interaction.guild.owner = None

        result = is_owner(interaction)
        assert result is False


@pytest.mark.asyncio
class TestIsOwnerOrOptinMode:

    # returns True if guild notification mode is 'optin' and author is not guild owner
    async def test_optin_mode_not_owner(self, ctx, test_session, test_engine, mocker):
        test_session.scalar = mocker.MagicMock(return_value='optin')
        mocker.patch('bot.bot_utils.Session', return_value=test_session)

        check_function = is_owner_or_optin_mode(test_engine).predicate
        result = await check_function(ctx)

        assert result is True

    # returns True if guild notification mode is not 'optin' and author is guild owner
    async def test_global_mode_and_author_is_owner(self, ctx, test_session, test_engine, mocker):
        ctx.guild.owner.id = ctx.author.id
        test_session.scalar = mocker.MagicMock(return_value='global')
        mocker.patch('bot.bot_utils.Session', return_value=test_session)

        check_function = is_owner_or_optin_mode(test_engine).predicate
        result = await check_function(ctx)

        assert result is True

    # returns False if guild notification mode is not 'optin' and author is not guild owner
    async def test_returns_false_if_not_optin_and_not_owner(self, ctx, test_session, test_engine, mocker):
        test_session.scalar = mocker.MagicMock(return_value='passive')
        mocker.patch('bot.bot_utils.Session', return_value=test_session)

        check_function = is_owner_or_optin_mode(test_engine).predicate
        result = await check_function(ctx)

        assert result is False

    # returns True if guild notification mode is 'optin' and author is guild owner
    async def test_optin_mode_and_owner(self, ctx, test_session, test_engine, mocker):
        ctx.guild.owner.id = ctx.author.id
        test_session.scalar = mocker.MagicMock(return_value='optin')
        mocker.patch('bot.bot_utils.Session', return_value=test_session)

        check_function = is_owner_or_optin_mode(test_engine).predicate
        result = await check_function(ctx)

        assert result is True
