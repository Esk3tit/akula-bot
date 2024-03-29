from bot.bot_utils import validate_streamer_ids
from twitchAPI.twitch import Twitch
from twitchAPI.type import TwitchAPIException
from twitchAPI.object.api import TwitchUser
from typing import AsyncGenerator
import pytest


class TestValidateStreamerIds:

    #  The function returns a list of user ids when given a valid list of user ids.
    @pytest.mark.asyncio
    async def test_valid_user_ids(self, mocker):
        # Mock the Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_user1 = mocker.Mock(spec=TwitchUser, id='123')
        mock_user2 = mocker.Mock(spec=TwitchUser, id='456')
        mock_user3 = mocker.Mock(spec=TwitchUser, id='789')

        async def mock_get_users(user_ids=None, logins=None) -> AsyncGenerator[TwitchUser, None]:
            for user in [mock_user1, mock_user2, mock_user3]:
                yield user

        mock_twitch.get_users.return_value = mock_get_users(user_ids=['123', '456', '789'])

        # Call the function under test
        result = await validate_streamer_ids(mock_twitch, ['123', '456', '789'])

        # Assert the result
        assert result == ['123', '456', '789']
        mock_twitch.get_users.assert_called_once_with(user_ids=['123', '456', '789'])

    #  The function returns an empty list when given a list of invalid user ids.
    @pytest.mark.asyncio
    async def test_invalid_user_ids(self, mocker):
        # Mock the Twitch API response
        mock_twitch = mocker.Mock(spec=Twitch)
        mock_twitch.get_users.side_effect = TwitchAPIException()

        # Call the function under test
        ids = ['42069', '1488']
        result = await validate_streamer_ids(mock_twitch, ids)

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
        result = await validate_streamer_ids(mock_twitch, ids)

        # Assert that the result is a list of user ids
        assert result == []

        # Assert that get_users was called with the correct arguments
        mock_twitch.get_users.assert_called_once_with(user_ids=ids)

    # #  The function returns a list of user ids when given a list of duplicate user ids.
    # @pytest.mark.asyncio
    # async def test_duplicate_user_ids(self, mocker):
    #     # Mock the Twitch API response
    #     mock_twitch = mocker.Mock(spec=Twitch)
    #     mock_response = [
    #         {"id": "12345"},
    #         {"id": "12345"},
    #         {"id": "12345"}
    #     ]
    #     mocker.patch.object(Twitch, "get_users", return_value=mock_response)
    #
    #     # Create a Twitch instance
    #     twitch = Twitch("client_id", "client_secret")
    #
    #     # Call the function under test
    #     result = await validate_streamer_ids(twitch, ["12345", "12345", "12345"])
    #
    #     # Assert the result is the expected list of user ids
    #     assert result == ["12345", "12345", "12345"]
