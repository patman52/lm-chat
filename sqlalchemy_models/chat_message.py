from sqlalchemy import Column, Index, Integer, String, ForeignKey

from db_base.base import Base

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    index = Column(Integer, nullable=False)  # order of messages in a chat
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    sender = Column(String(50), nullable=False)  # 'user' or 'bot'
    message = Column(String, nullable=False)

    __table_args__ = (
            Index('idx_chat_id', 'chat_id'),
        )
