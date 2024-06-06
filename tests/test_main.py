import asyncio
from unittest.mock import AsyncMock, call

import discord
import pytest
from sqlalchemy.exc import IntegrityError
from twitchAPI.eventsub.webhook import EventSubWebhook
from sqlalchemy import select

from bot.bot_ui import ConfigView
from bot.main import parse_streamers_from_command, on_guild_remove, on_guild_join, notifs, changeconfig, on_ready, \
    WEBHOOK_URL, notify_error, changeconfig_error, unnotify_error, subscribe_all, on_stream_online, notify
from twitchAPI.twitch import Twitch

from bot.models import Guild, UserSubscription, Streamer


@pytest.mark.asyncio
class TestSubscribeAll:
    async def test_subscribe_all_success(self, mocker, test_session):
        # Mock the Session and Streamer objects
        mock_streamer1 = mocker.MagicMock(spec=Streamer)
        mock_streamer1.streamer_id = "123"
        mock_streamer2 = mocker.MagicMock(spec=Streamer)
        mock_streamer2.streamer_id = "456"

        # Mock the scalars function and chain the return_value attributes
        mock_scalars = mocker.MagicMock()
        mock_scalars.return_value.all.return_value = [mock_streamer1, mock_streamer2]
        test_session.scalars = mock_scalars

        # Mock the commit method
        mock_commit = mocker.MagicMock()
        test_session.commit = mock_commit

        # Mock the webhook object
        mock_webhook = AsyncMock(spec=EventSubWebhook)
        mock_webhook.listen_stream_online.side_effect = ["topic1", "topic2"]

        # Patch the Session and EventSubWebhook classes
        mocker.patch('bot.main.Session', return_value=test_session)
        mocker.patch('twitchAPI.eventsub.webhook.EventSubWebhook', return_value=mock_webhook)

        # Call the subscribe_all function
        await subscribe_all(mock_webhook)

        # Assert that the listen_stream_online method was called for each streamer
        mock_webhook.listen_stream_online.assert_any_call(mock_streamer1.streamer_id, on_stream_online)
        mock_webhook.listen_stream_online.assert_any_call(mock_streamer2.streamer_id, on_stream_online)

        # Assert that the topic_sub_id was set for each streamer
        assert mock_streamer1.topic_sub_id == "topic1"
        assert mock_streamer2.topic_sub_id == "topic2"

        # Assert that the session was committed
        test_session.commit.assert_called_once()

    async def test_subscribe_all_no_streamers(self, mocker, test_session):
        # Mock the scalars function and chain the return_value attributes
        mock_scalars = mocker.MagicMock()
        mock_scalars.return_value.all.return_value = []
        test_session.scalars = mock_scalars

        # Mock the commit method
        mock_commit = mocker.MagicMock()
        test_session.commit = mock_commit

        # Mock the webhook object
        mock_webhook = AsyncMock(spec=EventSubWebhook)

        # Patch the Session and EventSubWebhook classes
        mocker.patch('bot.main.Session', return_value=test_session)
        mocker.patch('twitchAPI.eventsub.webhook.EventSubWebhook', return_value=mock_webhook)

        # Call the subscribe_all function
        await subscribe_all(mock_webhook)

        # Assert that the listen_stream_online method was not called
        mock_webhook.listen_stream_online.assert_not_called()

        # Assert that the session was not committed
        test_session.commit.assert_called_once()

    async def test_subscribe_all_exception(self, mocker, test_session):
        mock_streamer = mocker.MagicMock(spec=Streamer)
        mock_streamer.streamer_id = "123"

        # Mock the scalars function and chain the return_value attributes
        mock_scalars = mocker.MagicMock()
        mock_scalars.return_value.all.return_value = [mock_streamer]
        test_session.scalars = mock_scalars

        # Mock the commit method
        mock_commit = mocker.MagicMock()
        test_session.commit = mock_commit

        # Mock the webhook object to raise an exception
        mock_webhook = AsyncMock(spec=EventSubWebhook)
        mock_webhook.listen_stream_online.side_effect = Exception("Subscription failed")

        # Patch the Session and EventSubWebhook classes
        mocker.patch('bot.main.Session', return_value=test_session)
        mocker.patch('twitchAPI.eventsub.webhook.EventSubWebhook', return_value=mock_webhook)

        # Call the subscribe_all function and assert that it raises an exception
        with pytest.raises(Exception, match="Subscription failed"):
            await subscribe_all(mock_webhook)

        # Assert that the session was not committed
        test_session.commit.assert_not_called()


@pytest.mark.asyncio
class TestParseStreamersFromCommand:

    #  Should return a list of streamer IDs when given a list of streamer IDs
    async def test_parse_streamers_from_command_with_ids(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', '456', '789']
        mock_streamer_get_ids_names_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_names_from_logins.assert_not_called()
        mock_validate_streamer_ids_get_names.assert_called_once()
        assert sorted(mock_validate_streamer_ids_get_names.call_args[0][1]) == sorted(['123', '456', '789'])

    async def test_parse_streamers_from_command_with_names(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['streamer1', 'streamer2', 'streamer3']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(
            ['streamer1', 'streamer2', 'streamer3'])
        mock_validate_streamer_ids_get_names.assert_not_called()

    async def test_parse_streamers_from_command_with_urls(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['https://twitch.tv/streamer1', 'https://twitch.tv/streamer2']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=['123', '456'])
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456'}
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids_get_names.assert_not_called()

    # User gives no parameters to notify command which results in empty tuple
    async def test_parse_streamers_from_command_with_no_parameters(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        mock_streamer_get_ids_names_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        streamers = ()  # Empty tuple to simulate no parameters passed
        result = await parse_streamers_from_command(streamers)
        assert result == []
        mock_validate_streamer_ids_get_names.assert_not_called()
        mock_streamer_get_ids_names_from_logins.assert_not_called()

    #  Should return a list of streamer IDs when given a mix of streamer IDs, names, and URLs
    async def test_parse_streamers_from_command_with_mixed_inputs(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', 'streamer1', 'https://twitch.tv/streamer2']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=['456', '789'])
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock(return_value=['123'])
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids_get_names.assert_called_once()
        assert sorted(mock_validate_streamer_ids_get_names.call_args[0][1]) == sorted(['123'])

    #  Should return [] when given a list of streamer names that don't exist
    async def test_parse_streamers_from_command_with_invalid_names(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['invalid_streamer1', 'invalid_streamer2']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=None)
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert result == []
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(streamers)
        mock_validate_streamer_ids_get_names.assert_not_called()

    #  Should return [] when given a list with a non-existent streamer ID
    async def test_parse_streamers_from_command_with_nonexistent_streamer_id(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', '456']
        mock_streamer_get_ids_names_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock(return_value=[])
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        # Call the parse_streamers_from_command function with a list containing a non-existent streamer ID
        result = await parse_streamers_from_command(streamers)

        # Check that the result is []
        assert result == []
        mock_streamer_get_ids_names_from_logins.assert_not_called()
        mock_validate_streamer_ids_get_names.assert_called_once()
        assert sorted(mock_validate_streamer_ids_get_names.call_args[0][1]) == sorted(streamers)

    #  Should return None when given a list with non-existent URLs or incorrect ones
    async def test_parse_streamers_from_command_with_invalid_urls(self, mocker):
        # Mock the global twitch_obj
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['https://invalid.com/streamer1', 'https://twitch.tv/invalid_streamer2']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=None)
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert result == []
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(
            ['https://invalid.com/streamer1', 'invalid_streamer2'])
        mock_validate_streamer_ids_get_names.assert_not_called()

    async def test_parse_streamers_from_command_with_uninitialized_twitch_obj(self, mocker):
        # Mock the global twitch_obj as None
        mocker.patch('bot.main.twitch_obj', None)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)
        mock_streamer_get_ids_names_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)

        streamers = ['123', 'streamer1']
        with pytest.raises(ValueError) as excinfo:
            await parse_streamers_from_command(streamers)
        assert str(excinfo.value) == "Global variable not initialized."
        mock_validate_streamer_ids_get_names.assert_not_called()
        mock_streamer_get_ids_names_from_logins.assert_not_called()

    async def test_parse_streamers_from_command_with_duplicate_ids(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', '456', '123', '789', '456']
        mock_streamer_get_ids_names_from_logins = AsyncMock()
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_validate_streamer_ids_get_names.assert_called_once()
        assert sorted(mock_validate_streamer_ids_get_names.call_args[0][1]) == sorted(['123', '456', '789'])
        mock_streamer_get_ids_names_from_logins.assert_not_called()

    async def test_parse_streamers_from_command_with_duplicate_names(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['streamer1', 'streamer2', 'streamer1', 'streamer3', 'streamer2']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=['123', '456', '789'])
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456', '789'}
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(
            ['streamer1', 'streamer2', 'streamer3'])
        mock_validate_streamer_ids_get_names.assert_not_called()

    async def test_parse_streamers_from_command_with_duplicate_urls(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['https://twitch.tv/streamer1', 'https://twitch.tv/streamer2', 'https://twitch.tv/streamer1']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=['123', '456'])
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock()
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456'}
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids_get_names.assert_not_called()

    async def test_parse_streamers_from_command_with_mixed_duplicates(self, mocker):
        mocker.patch('bot.main.twitch_obj', mocker.MagicMock(spec=Twitch))

        streamers = ['123', 'streamer1', '123', 'https://twitch.tv/streamer1', 'streamer2',
                     'https://twitch.tv/streamer2']
        mock_streamer_get_ids_names_from_logins = AsyncMock(return_value=['123', '456'])
        mocker.patch('bot.main.streamer_get_ids_names_from_logins', mock_streamer_get_ids_names_from_logins)
        mock_validate_streamer_ids_get_names = AsyncMock(return_value=['123'])
        mocker.patch('bot.main.validate_streamer_ids_get_names', mock_validate_streamer_ids_get_names)

        result = await parse_streamers_from_command(streamers)
        assert set(result) == {'123', '456'}
        mock_streamer_get_ids_names_from_logins.assert_called_once()
        assert sorted(mock_streamer_get_ids_names_from_logins.call_args[0][1]) == sorted(['streamer1', 'streamer2'])
        mock_validate_streamer_ids_get_names.assert_called_once()
        assert sorted(mock_validate_streamer_ids_get_names.call_args[0][1]) == sorted(['123'])


@pytest.mark.asyncio
class TestOnGuildRemove:

    async def test_on_guild_remove_deletes_guild(self, mocker, test_session):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1076360773879738380
        mocker.patch('bot.main.Session', return_value=test_session)
        await on_guild_remove(guild)
        assert test_session.scalar(select(Guild).where(Guild.guild_id == str(guild.id))) is None

    async def test_on_guild_remove_cascade_deletes_user_subscriptions_and_streamers(self, mocker, test_session):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1076360773879738380
        mocker.patch('bot.main.Session', return_value=test_session)
        await on_guild_remove(guild)
        assert test_session.scalars(
            select(UserSubscription).where(UserSubscription.guild_id == str(guild.id))).all() == []
        assert test_session.scalar(select(Streamer).where(Streamer.streamer_id == '6')) is None
        assert test_session.scalar(select(Streamer).where(Streamer.streamer_id == '7')) is None
        assert test_session.scalar(select(Streamer).where(Streamer.streamer_id == '8')) is None
        assert test_session.scalar(select(Streamer).where(Streamer.streamer_id == '9')) is None

    async def test_on_guild_streamer_still_subbed_not_deleted(self, mocker, test_session):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1076360773879738380
        mocker.patch('bot.main.Session', return_value=test_session)
        await on_guild_remove(guild)
        assert test_session.scalar(select(Streamer).where(Streamer.streamer_id == '433451304')) is not None
        assert test_session.scalar(select(Streamer).where(Streamer.streamer_id == '162656602')) is not None


@pytest.mark.asyncio
class TestOnGuildJoin:

    async def test_on_guild_join_creates_guild(self, mocker, bot, test_session):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1234567890
        guild.owner = mocker.MagicMock(spec=discord.Member)
        guild.owner.display_name = "Guild Owner"
        guild.owner.display_avatar = "owner_avatar_url"

        channel = mocker.MagicMock(spec=discord.TextChannel)
        channel.id = 9876543210

        config_button = mocker.MagicMock(spec=ConfigView)
        config_button.channel = channel
        config_button.notification_mode = "optin"

        mocker.patch('bot.main.bot', new=bot)
        mocker.patch('bot.main.get_first_sendable_text_channel', return_value=channel)
        mocker.patch('bot.main.ConfigView', return_value=config_button)
        mocker.patch('bot.main.Session', return_value=test_session)

        await on_guild_join(guild)

        assert test_session.scalar(select(Guild).where(Guild.guild_id == str(guild.id))) is not None

    async def test_on_guild_join_sends_embed_and_config_button(self, mocker, bot):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1234567890
        guild.owner = mocker.MagicMock(spec=discord.Member)
        guild.owner.display_name = "Guild Owner"
        guild.owner.display_avatar = "owner_avatar_url"

        channel = mocker.MagicMock(spec=discord.TextChannel)
        channel.id = 9876543210

        config_button = mocker.MagicMock(spec=ConfigView)
        config_button.channel = channel
        config_button.notification_mode = "global"

        mocker.patch('bot.main.bot', new=bot)
        mocker.patch('bot.main.get_first_sendable_text_channel', return_value=channel)
        mocker.patch('bot.main.ConfigView', return_value=config_button)
        mocker.patch('bot.main.Session', return_value=mocker.MagicMock())

        await on_guild_join(guild)

        channel.send.assert_any_call(f'{guild.owner.mention}')
        channel.send.assert_any_call(embed=mocker.ANY)
        channel.send.assert_any_call(view=mocker.ANY)

    async def test_on_guild_join_sends_dm_to_owner_if_no_channel(self, mocker, capfd):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1234567890
        guild.owner = mocker.MagicMock(spec=discord.Member)
        guild.owner.display_name = "Guild Owner"
        guild.owner.display_avatar = "owner_avatar_url"
        mocker.patch('bot.main.get_first_sendable_text_channel', return_value=None)

        await on_guild_join(guild)

        out, err = capfd.readouterr()
        guild.owner.send.assert_called_once_with("Error: Bot has no channel that it has permission to post in.")
        assert "Message sent to the guild owner" in out

    async def test_on_guild_join_handles_dm_to_owner_exception(self, mocker, capfd):
        guild = mocker.MagicMock(spec=discord.Guild)
        guild.id = 1234567890
        mocker.patch('bot.main.get_first_sendable_text_channel', return_value=None)
        guild.owner.send = AsyncMock(
            side_effect=discord.HTTPException(response=mocker.MagicMock(), message="Test Exception"))

        await on_guild_join(guild)

        out, err = capfd.readouterr()
        assert "Failed to send message to the guild owner" in out
        assert "Test Exception" in out


@pytest.mark.asyncio
class TestNotifs:
    async def test_notifs_with_subscriptions(self, mocker, ctx, test_session):
        # Create test data in the database
        streamer1 = Streamer(streamer_id='1', streamer_name='Streamer1', topic_sub_id='a')
        streamer2 = Streamer(streamer_id='2', streamer_name='Streamer2', topic_sub_id='b')
        test_session.add_all([streamer1, streamer2])
        test_session.flush()

        subscription1 = UserSubscription(
            user_id='123', guild_id='1076360773879738380', streamer_id=streamer1.streamer_id
        )
        subscription2 = UserSubscription(
            user_id='123', guild_id='1076360773879738380', streamer_id=streamer2.streamer_id
        )
        test_session.add_all([subscription1, subscription2])
        test_session.commit()

        mocker.patch('bot.main.Session', return_value=test_session)

        # Call the function
        await notifs(ctx)

        # Check if the correct embed message is sent
        ctx.send.assert_called_once()
        send_kwargs = ctx.send.call_args.kwargs
        assert 'embed' in send_kwargs
        embed = send_kwargs['embed']
        assert isinstance(embed, discord.Embed)
        assert embed.title == "Your Notification Subscriptions"
        assert "Streamer1" in embed.fields[0].value
        assert "Streamer2" in embed.fields[0].value

    async def test_notifs_no_subscriptions(self, mocker, ctx, test_session):
        # Patch the Session in bot.main with the test_session
        mocker.patch('bot.main.Session', return_value=test_session)

        # Call the function
        await notifs(ctx)

        # Check if the correct message is sent
        ctx.send.assert_called_once_with(
            f'{ctx.author.mention} You are not receiving notifications in {ctx.guild.name}!'
        )

    async def test_notifs_exceeds_embed_limit(self, mocker, ctx, test_session):
        # Create test data in the database
        streamers = [Streamer(streamer_id=str(i), streamer_name=f'Streamer{i}', topic_sub_id=f'a{i}') for i in
                     range(200, 401)]
        test_session.add_all(streamers)
        test_session.flush()

        subscriptions = [
            UserSubscription(user_id='123', guild_id='1076360773879738380', streamer_id=streamer.streamer_id) for
            streamer
            in streamers]
        test_session.add_all(subscriptions)
        test_session.commit()

        # Patch the Session in bot.main with the test_session
        mocker.patch('bot.main.Session', return_value=test_session)

        # Call the function
        await notifs(ctx)

        # Check if the correct embed message is sent
        ctx.send.assert_called_once()
        send_kwargs = ctx.send.call_args.kwargs
        assert 'embed' in send_kwargs
        embed = send_kwargs['embed']
        assert isinstance(embed, discord.Embed)
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Subscribed Streamers"
        assert embed.fields[0].value == "Too many subscriptions to display here!"


@pytest.mark.asyncio
class TestChangeConfig:

    async def test_changeconfig_update_database(self, ctx, bot, mocker, test_session):
        guild_config = Guild(guild_id='123',
                             notification_channel_id='789',
                             notification_mode='optin',
                             is_censored=False
                             )
        test_session.add(guild_config)
        test_session.commit()

        ctx.guild.id = 123
        init_channel = mocker.MagicMock(spec=discord.TextChannel)
        init_channel.id = 777
        init_channel.name = 'test-channel'
        channel = mocker.MagicMock(spec=discord.TextChannel)
        channel.id = 321
        backup_channel = mocker.MagicMock(spec=discord.TextChannel)
        backup_channel.id = 420
        bot.get_channel.return_value = init_channel

        config_view = mocker.MagicMock(spec=ConfigView)
        config_view.channel = channel
        config_view.notification_mode = 'passive'
        config_view.is_censored = True
        config_view.wait = AsyncMock()

        mocker.patch('bot.main.Session', return_value=test_session)
        mocker.patch('bot.main.ConfigView', return_value=config_view)
        mocker.patch('bot.main.get_first_sendable_text_channel', return_value=backup_channel)
        mocker.patch('bot.main.bot', return_value=bot)

        await changeconfig(ctx)

        assert ctx.send.call_count == 2
        print(ctx.send.call_args_list)
        send_embed_kwargs = ctx.send.call_args_list[0].kwargs
        send_view_kwargs = ctx.send.call_args_list[1].kwargs

        assert 'embed' in send_embed_kwargs
        embed = send_embed_kwargs['embed']
        assert isinstance(embed, discord.Embed)

        assert 'view' in send_view_kwargs
        view = send_view_kwargs['view']
        assert isinstance(view, ConfigView)

        updated_config = test_session.query(Guild).filter(Guild.guild_id == '123').first()
        assert updated_config.notification_channel_id == '321'
        assert updated_config.notification_mode == 'passive'
        assert updated_config.is_censored is True


@pytest.mark.asyncio
class TestOnReady:
    async def test_on_ready_successful(self, bot, mocker):
        mock_print = mocker.patch('builtins.print')
        mocker.patch('bot.main.bot', new=bot)
        mock_bot_tree_sync = mocker.patch('bot.main.bot.tree.sync', new_callable=AsyncMock)
        twitch_obj_mock = mocker.patch('bot.main.twitch_obj', new=mocker.MagicMock())
        mocker.patch('bot.main.webhook_obj', new=mocker.MagicMock())
        mocker.patch('twitchAPI.eventsub.webhook.EventSubWebhook',
                     mocker.MagicMock(spec=EventSubWebhook,
                                      callback_url=WEBHOOK_URL, port=8080, twitch=twitch_obj_mock,
                                      start=AsyncMock))
        mock_subscribe_all = mocker.patch('bot.main.subscribe_all', new_callable=AsyncMock)
        await on_ready()

        mock_print.assert_has_calls([
            call(f'{bot.user.name} has connected to Discord!'),
            call("Subscribing to streamers... Please wait..."),
            call("Successfully subscribed to all streamers in the DB!")
        ])
        mock_bot_tree_sync.assert_called_once()
        mock_subscribe_all.assert_called_once()

    async def test_on_ready_invalid_twitch_credentials(self, bot, mocker):
        mock_print = mocker.patch('builtins.print')
        mocker.patch('bot.main.bot', new=bot)
        mocker.patch('bot.main.bot.tree.sync', new_callable=AsyncMock)
        mocker.patch('bot.main.Twitch', AsyncMock(side_effect=Exception("Invalid credentials")))

        try:
            await on_ready()
        except Exception as e:
            assert str(e) == "Invalid credentials"
        else:
            assert False, "Expected exception was not raised"

        mock_print.assert_has_calls([
            call(f'{bot.user.name} has connected to Discord!')
        ])


@pytest.mark.asyncio
class TestChangeConfigError:
    async def test_changeconfig_error(self, mocker, ctx):
        error = mocker.MagicMock()
        mock_print = mocker.patch('builtins.print')

        await changeconfig_error(ctx, error)

        mock_print.assert_called_once_with(error)
        ctx.send.assert_called_once_with(f"{ctx.author.mention} You don't have permission to use this command...",
                                         ephemeral=True)


@pytest.mark.asyncio
class TestUnnotifyError:
    async def test_unnotify_error(self, mocker, ctx):
        error = mocker.MagicMock()
        mock_print = mocker.patch('builtins.print')

        await unnotify_error(ctx, error)

        mock_print.assert_called_once_with(error)
        ctx.send.assert_called_once_with(f"{ctx.author.mention} You don't have permission to use this command...",
                                         ephemeral=True)


@pytest.mark.asyncio
class TestNotifyError:
    async def test_notify_error(self, mocker, ctx):
        error = mocker.MagicMock()
        mock_print = mocker.patch('builtins.print')

        await notify_error(ctx, error)

        mock_print.assert_called_once_with(error)
        ctx.send.assert_called_once_with(f"{ctx.author.mention} You don't have permission to use this command...",
                                         ephemeral=True)


@pytest.mark.asyncio
class TestNotify:
    async def test_notify_success(self, ctx, test_session, mocker):
        streamer1 = mocker.MagicMock(spec=Streamer)
        streamer1.id = '789'
        streamer1.name = 'streamer1'

        streamer2 = mocker.MagicMock(spec=Streamer)
        streamer2.id = '012'
        streamer2.name = 'streamer2'

        clean_streamers = [streamer1, streamer2]

        mock_parse_streamers = mocker.patch('bot.main.parse_streamers_from_command', return_value=clean_streamers)
        mock_webhook_obj = mocker.patch('bot.main.webhook_obj')
        mock_listen_stream_online = mocker.AsyncMock(side_effect=['topic1', 'topic2'])
        mock_webhook_obj.listen_stream_online = mock_listen_stream_online
        test_session.scalar = mocker.MagicMock(return_value=None)
        test_session.execute = mocker.MagicMock()
        test_session.add = mocker.MagicMock()
        test_session.commit = mocker.MagicMock()

        mocker.patch('bot.main.Session', return_value=test_session)
        await notify(ctx, 'streamer1', 'streamer2')

        mock_parse_streamers.assert_called_once_with(('streamer1', 'streamer2'))
        mock_listen_stream_online.assert_any_call('789', on_stream_online)
        mock_listen_stream_online.assert_any_call('012', on_stream_online)
        test_session.add.assert_any_call(mocker.ANY)
        test_session.commit.assert_called()
        ctx.send.assert_called_once_with(
            f'{ctx.author.mention} will now be notified of when the following streamers are live: `streamer1, streamer2`'
        )

    async def test_notify_unable_to_find_streamer(self, ctx, mocker):
        mock_parse_streamers = mocker.patch('bot.main.parse_streamers_from_command', return_value=[])
        mocker.patch('bot.main.webhook_obj')

        await notify(ctx, 'streamer1', 'streamer2')

        mock_parse_streamers.assert_called_once_with(('streamer1', 'streamer2'))
        ctx.send.assert_called_once_with(
            f'{ctx.author.mention} Unable to find one of the given streamer(s), please try again... MAGGOT!'
        )

    async def test_notify_streamer_already_exists(self, ctx, test_session, mocker):
        streamer1 = mocker.MagicMock(spec=Streamer)
        streamer1.id = '666777'
        streamer1.name = 'streamer1'

        clean_streamers = [streamer1]

        mock_parse_streamers = mocker.patch('bot.main.parse_streamers_from_command', return_value=clean_streamers)
        mock_webhook_obj = mocker.patch('bot.main.webhook_obj')
        mock_listen_stream_online = mocker.AsyncMock(side_effect=['topic1'])
        mock_webhook_obj.listen_stream_online = mock_listen_stream_online
        test_session.scalar = mocker.MagicMock(return_value=Streamer(streamer_id='666777', streamer_name='streamer1', topic_sub_id='topic1'))
        test_session.execute = mocker.MagicMock()
        test_session.add = mocker.MagicMock()
        test_session.commit = mocker.MagicMock()

        mocker.patch('bot.main.Session', return_value=test_session)
        await notify(ctx, 'streamer1')

        mock_parse_streamers.assert_called_once_with(('streamer1',))
        test_session.add.assert_not_called()
        test_session.commit.assert_called()
        ctx.send.assert_called_once_with(
            f'{ctx.author.mention} will now be notified of when the following streamers are live: `streamer1`'
        )

    async def test_notify_already_subscribed(self, ctx, test_session, mocker):
        streamer1 = mocker.MagicMock(spec=Streamer)
        streamer1.id = '789'
        streamer1.name = 'streamer1'

        clean_streamers = [streamer1]

        mock_parse_streamers = mocker.patch('bot.main.parse_streamers_from_command', return_value=clean_streamers)
        mocker.patch('bot.main.webhook_obj')
        test_session.scalar = mocker.MagicMock(return_value=Streamer(streamer_id='789', streamer_name='streamer1', topic_sub_id='topic1'))
        test_session.execute = mocker.MagicMock(side_effect=IntegrityError(None, None, None))
        test_session.add = mocker.MagicMock()
        test_session.rollback = mocker.MagicMock()

        mocker.patch('bot.main.Session', return_value=test_session)
        await notify(ctx, 'streamer1')

        mock_parse_streamers.assert_called_once_with(('streamer1',))
        test_session.rollback.assert_called_once()
        test_session.add.assert_not_called()
        ctx.send.assert_called_once_with(
            f'{ctx.author.mention} you are already subscribed to some or all of the streamer(s)! Reverting...'
        )

    async def test_notify_webhook_obj_not_initialized(self, ctx, mocker):
        mocker.patch('bot.main.webhook_obj', None)

        with pytest.raises(ValueError, match='Global reference not initialized...'):
            await notify(ctx, 'streamer1')
