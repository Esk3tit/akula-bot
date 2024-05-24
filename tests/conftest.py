import os
from unittest.mock import MagicMock

import discord
import pytest
from discord.ext.commands import Context, Bot
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOnlineData

from bot.models import Base

# Load dotenv if on local env (check for prod only env var)
if not os.getenv('FLY_APP_NAME'):
    load_dotenv()
postgres_test_connection_str = os.getenv('POSTGRESQL_TEST_URL')


@pytest.fixture(scope='session')
def test_engine():
    engine = create_engine(postgres_test_connection_str, echo=True, pool_pre_ping=True, pool_recycle=300)
    Base.metadata.create_all(engine)
    yield engine


@pytest.fixture(scope='function')
def test_connection(test_engine):
    connection = test_engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope='function')
def test_transaction(test_connection):
    transaction = test_connection.begin()
    yield transaction
    transaction.rollback()


@pytest.fixture(scope='function')
def test_session(test_transaction, test_connection):
    session = sessionmaker(bind=test_connection)()
    session.begin_nested()

    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(_session, transaction):
        if transaction.nested and not transaction._parent.nested:
            _session.expire_all()
            _session.begin_nested()

    yield session

    session.close()


@pytest.fixture(scope='function')
def bot():
    bot_user = MagicMock(spec=discord.ClientUser)
    bot_user.display_name = 'Bot'
    bot_user.display_avatar = 'bot_avatar_url'
    bot_user.name = 'Bot'
    bot_instance = MagicMock(spec=Bot)
    bot_instance.user = bot_user
    return bot_instance


@pytest.fixture(scope='function')
def ctx():
    context = MagicMock(spec=Context)
    context.guild.id = 1076360773879738380
    context.guild.name = 'TestGuild'
    context.author.id = 123
    context.author.name = 'TestUser'
    context.author.display_name = 'TestUser'
    context.author.display_avatar = 'test_avatar_url'
    return context


@pytest.fixture(scope='function')
def mock_stream_online_data(mocker):
    mock_data = mocker.Mock(spec=StreamOnlineEvent)
    mock_data.event = mocker.Mock(spec=StreamOnlineData)
    mock_data.event.broadcaster_user_name = "test_user"
    mock_data.event.broadcaster_user_login = "test_user_login"
    mock_data.event.started_at = "2022-01-01 12:00:00"
    return mock_data
