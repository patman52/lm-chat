from sqlalchemy import Column, Index, Integer, String

from db_base.base import Base


class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)

    __table_args__ = (
            Index('idx_title', 'title'),
        )
