import pytest
from twitchAPI.type import TwitchAPIException
from typing import AsyncGenerator
from bot.main import streamer_get_names_from_ids
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
