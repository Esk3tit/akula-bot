import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
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

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(_session, transaction):
        if transaction.nested and not transaction._parent.nested:
            _session.expire_all()
            _session.begin_nested()

    yield session

    session.close()
