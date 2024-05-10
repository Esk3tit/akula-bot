import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
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
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='function')
def test_session(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()