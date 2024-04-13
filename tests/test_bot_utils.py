from bot.bot_utils import validate_streamer_ids_get_names, streamer_get_ids_names_from_logins
from twitchAPI.twitch import Twitch
from twitchAPI.type import TwitchAPIException
from twitchAPI.object.api import TwitchUser
from typing import AsyncGenerator
import pytest

from bot.models import GetUsersStreamer


class TestStreamerGetIdsFromLogins:

    #  Returns a list of GetUsersStreamers when given a list of valid broadcaster logins
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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


class TestValidateStreamerIds:

    #  The function returns a list of GetUsersStreamers when given a valid list of user ids.
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
