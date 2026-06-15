"""
Creates the connection to a database and a session factory

Session factory creates sessions, which run queries and transactions
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./lm_chat.db"

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False, future=True)
