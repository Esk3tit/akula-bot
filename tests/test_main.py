from unittest.mock import AsyncMock

import pytest
from twitchAPI.type import TwitchAPIException
from typing import AsyncGenerator
from bot.main import streamer_get_names_from_ids, streamer_get_ids_from_logins, parse_streamers_from_command
from twitchAPI.twitch import Twitch
from twitchAPI.object.api import TwitchUser


class TestStreamerGetNamesFromIds:
    @pytest.mark.asyncio
    async def test_streamer_get_names_from_ids_single_user(self, mocker):
        # mock twitch and user
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user = mocker.Mock(spec=TwitchUser, id='123', display_name='user1')

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            yield mock_user

        mock_twitch.get_users.return_value = mock_get_users(user_ids=['123'])

        # Call mocked function
        result = await streamer_get_names_from_ids(mock_twitch, ['123'])

        # Assert results
        assert result == {'123': 'user1'}
        mock_twitch.get_users.assert_called_once_with(user_ids=['123'])

    @pytest.mark.asyncio
    async def test_streamer_get_names_from_ids_multiple_users(self, mocker):
        # Create a mock Twitch object
        mock_twitch = mocker.Mock(spec=Twitch)

        # Create mock TwitchUser objects
        mock_user1 = mocker.Mock(spec=TwitchUser, id='123', display_name='TestStreamer1')
        mock_user2 = mocker.Mock(spec=TwitchUser, id='456', display_name='TestStreamer2')

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            for user in [mock_user1, mock_user2]:
                yield user

        # Configure the mock twitch.get_users method to return the mock TwitchUser objects
        mock_twitch.get_users.return_value = mock_get_users(user_ids=['123', '456'])

        # Call the function with the mock Twitch object and multiple user IDs
        result = await streamer_get_names_from_ids(mock_twitch, ['123', '456'])

        # Assert that the result is as expected
        assert result == {'123': 'TestStreamer1', '456': 'TestStreamer2'}
        mock_twitch.get_users.assert_called_once_with(user_ids=['123', '456'])

    @pytest.mark.asyncio
    async def test_streamer_get_names_from_ids_exception(self, mocker):
        # Create a mock Twitch object
        mock_twitch = mocker.Mock(spec=Twitch)

        # Configure the mock twitch.get_users method to raise a TwitchAPIException
        mock_twitch.get_users.side_effect = TwitchAPIException('API error')

        # Call the function with the mock Twitch object and a list of IDs
        ids = ['123', '456']
        result = await streamer_get_names_from_ids(mock_twitch, ids)

        # Assert that the result is None when an exception is raised
        assert result is None
        mock_twitch.get_users.assert_called_once_with(user_ids=ids)


class TestStreamerGetIdsFromLogins:

    #  Returns a list of user ids when given a list of valid broadcaster logins
    @pytest.mark.asyncio
    async def test_valid_broadcaster_logins(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user1 = mocker.Mock(spec=TwitchUser, id='123')
        mock_user2 = mocker.Mock(spec=TwitchUser, id='456')
        mock_user3 = mocker.Mock(spec=TwitchUser, id='789')

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            for user in [mock_user1, mock_user2, mock_user3]:
                yield user

        mock_twitch.get_users.return_value = mock_get_users(logins=['broadcaster1', 'broadcaster2', 'broadcaster3'])

        # Call the function under test
        result = await streamer_get_ids_from_logins(mock_twitch, ['broadcaster1', 'broadcaster2', 'broadcaster3'])

        # Assert the result
        assert result == ['123', '456', '789']
        mock_twitch.get_users.assert_called_once_with(logins=['broadcaster1', 'broadcaster2', 'broadcaster3'])

    #  Returns None when given a list of invalid broadcaster logins
    @pytest.mark.asyncio
    async def test_invalid_broadcaster_logins(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        # Configure the mock twitch.get_users method to raise a TwitchAPIException
        mock_twitch.get_users.side_effect = TwitchAPIException('API error')

        # Call the function under test
        result = await streamer_get_ids_from_logins(mock_twitch, ['invalid1', 'invalid2', 'invalid3'])

        # Assert the result
        assert result is None
        mock_twitch.get_users.assert_called_once_with(logins=['invalid1', 'invalid2', 'invalid3'])

    #  Returns None when given a single invalid broadcaster login
    @pytest.mark.asyncio
    async def test_single_invalid_broadcaster_login(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock()
        # Configure the mock twitch.get_users method to raise a TwitchAPIException
        mock_twitch.get_users.side_effect = TwitchAPIException('API error')

        # Call the function under test
        result = await streamer_get_ids_from_logins(mock_twitch, ['invalid'])

        # Assert the result
        assert result is None
        mock_twitch.get_users.assert_called_once_with(logins=['invalid'])

    #  Returns a list of user ids when given a single valid broadcaster login
    @pytest.mark.asyncio
    async def test_single_valid_broadcaster_login(self, mocker):
        # Mock Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user = mocker.Mock(spec=TwitchUser, id='123456789')

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            yield mock_user

        mock_twitch.get_users.return_value = mock_get_users(logins=['broadcaster'])

        # Call the function under test
        result = await streamer_get_ids_from_logins(mock_twitch, ['broadcaster'])

        # Assert the result
        assert result == ['123456789']
        mock_twitch.get_users.assert_called_once_with(logins=['broadcaster'])


class TestParseStreamersFromCommand:

    #  Should return a list of streamer IDs when given a list of streamer IDs
    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_ids(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', '456', '789']
        mock_streamer_get_ids_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert result == ['123', '456', '789']
        mock_streamer_get_ids_from_logins.assert_not_called()
        mock_validate_streamer_ids.assert_called_once_with(mocker.ANY, streamers)

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_names(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['streamer1', 'streamer2', 'streamer3']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert result == ['123', '456', '789']
        mock_streamer_get_ids_from_logins.assert_called_once_with(mocker.ANY, streamers)
        mock_validate_streamer_ids.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_urls(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['https://twitch.tv/streamer1', 'https://twitch.tv/streamer2']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=['123', '456'])
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert result == ['123', '456']
        mock_streamer_get_ids_from_logins.assert_called_once_with(mocker.ANY, ['streamer1', 'streamer2'])
        mock_validate_streamer_ids.assert_not_called()

    # User gives no parameters to notify command which results in empty tuple
    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_no_parameters(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        mock_streamer_get_ids_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        streamers = ()  # Empty tuple to simulate no parameters passed
        result = await parse_streamers_from_command(streamers)
        assert result == []
        mock_validate_streamer_ids.assert_not_called()
        mock_streamer_get_ids_from_logins.assert_not_called()

    #  Should return a list of streamer IDs when given a mix of streamer IDs, names, and URLs
    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_mixed_inputs(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', 'streamer1', 'https://twitch.tv/streamer2']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=['456', '789'])
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock(return_value=['123'])
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert result == ['123', '456', '789']
        mock_streamer_get_ids_from_logins.assert_called_once_with(mocker.ANY, ['streamer1', 'streamer2'])
        mock_validate_streamer_ids.assert_called_once_with(mocker.ANY, ['123'])

    #  Should return [] when given a list of streamer names that don't exist
    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_invalid_names(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['invalid_streamer1', 'invalid_streamer2']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=None)
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert result == []
        mock_streamer_get_ids_from_logins.assert_called_once_with(mocker.ANY, streamers)
        mock_validate_streamer_ids.assert_not_called()

    #  Should return [] when given a list with a non-existent streamer ID
    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_nonexistent_streamer_id(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', '456']
        mock_streamer_get_ids_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock(return_value=[])
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        # Call the parse_streamers_from_command function with a list containing a non-existent streamer ID
        result = await parse_streamers_from_command(streamers)

        # Check that the result is []
        assert result == []
        mock_streamer_get_ids_from_logins.assert_not_called()
        mock_validate_streamer_ids.assert_called_once_with(mocker.ANY, streamers)

    #  Should return None when given a list with non-existent URLs or incorrect ones
    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_invalid_urls(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['https://invalid.com/streamer1', 'https://twitch.tv/invalid_streamer2']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=None)
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert result == []
        mock_streamer_get_ids_from_logins.assert_called_once_with(mocker.ANY, ['https://invalid.com/streamer1', 'invalid_streamer2'])
        mock_validate_streamer_ids.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_uninitialized_twitch_obj(self, mocker):
        # Mock the global twitch_obj as None
        mocker.patch('bot.main.twitch_obj', None)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)
        mock_streamer_get_ids_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)

        streamers = ['123', 'streamer1']
        with pytest.raises(ValueError) as excinfo:
            await parse_streamers_from_command(streamers)
        assert str(excinfo.value) == "Global variable not initialized."
        mock_validate_streamer_ids.assert_not_called()
        mock_streamer_get_ids_from_logins.assert_not_called()
