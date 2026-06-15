"""
Defines the Base class for all SQLAlchemy models
Ensures all constraints and indexes have consistent names when performing migrations

"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from db_base.load_models import load_models

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

class Base(DeclarativeBase):
    metadata = metadata

load_models()
