"""
Creates the connection to a database and a session factory

Session factory creates sessions, which run queries and transactions
"""

import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./lm_chat.db"

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
	# SQLite requires this pragma per connection for FK actions like ON DELETE CASCADE.
	if isinstance(dbapi_connection, sqlite3.Connection):
		cursor = dbapi_connection.cursor()
		cursor.execute("PRAGMA foreign_keys=ON")
		cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False, future=True, expire_on_commit=False)
