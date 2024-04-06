from unittest.mock import AsyncMock, call
import pytest
from bot.main import parse_streamers_from_command
from twitchAPI.twitch import Twitch


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
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_from_logins.assert_not_called()
        mock_validate_streamer_ids.assert_called_once()
        assert sorted(mock_validate_streamer_ids.call_args[0][1]) == sorted(['123', '456', '789'])

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
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2', 'streamer3'])
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
        assert set(result) == {'123', '456'}
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
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
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids.assert_called_once()
        assert sorted(mock_validate_streamer_ids.call_args[0][1]) == sorted(['123'])

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
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(streamers)
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
        mock_validate_streamer_ids.assert_called_once()
        assert sorted(mock_validate_streamer_ids.call_args[0][1]) == sorted(streamers)

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
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(['https://invalid.com/streamer1', 'invalid_streamer2'])
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

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_duplicate_ids(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', '456', '123', '789', '456']
        mock_streamer_get_ids_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_validate_streamer_ids.assert_called_once()
        assert sorted(mock_validate_streamer_ids.call_args[0][1]) == sorted(['123', '456', '789'])
        mock_streamer_get_ids_from_logins.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_duplicate_names(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['streamer1', 'streamer2', 'streamer1', 'streamer3', 'streamer2']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(
            ['streamer1', 'streamer2', 'streamer3'])
        mock_validate_streamer_ids.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_duplicate_urls(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['https://twitch.tv/streamer1', 'https://twitch.tv/streamer2', 'https://twitch.tv/streamer1']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=['123', '456'])
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456'}
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_streamers_from_command_with_mixed_duplicates(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', 'streamer1', '123', 'https://twitch.tv/streamer1', 'streamer2',
                     'https://twitch.tv/streamer2']
        mock_streamer_get_ids_from_logins = AsyncMock(return_value=['123', '456'])
        mocker.patch('bot.main.streamer_get_ids_from_logins', mock_streamer_get_ids_from_logins)
        mock_validate_streamer_ids = AsyncMock(return_value=['123'])
        mocker.patch('bot.main.validate_streamer_ids', mock_validate_streamer_ids)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456'}
        mock_streamer_get_ids_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids.assert_called_once()
        assert sorted(mock_validate_streamer_ids.call_args[0][1]) == sorted(['123'])
