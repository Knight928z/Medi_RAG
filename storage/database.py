from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_engine_from_url(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


@contextmanager
def get_session(database_url: str) -> Generator:
    engine = create_engine_from_url(database_url)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
