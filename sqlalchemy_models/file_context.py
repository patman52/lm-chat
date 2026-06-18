from sqlalchemy import Column, ForeignKey, Index, Integer, String

from db_base.base import Base


class FileContext(Base):
    __tablename__ = 'file_contexts'
    id = Column(Integer, primary_key=True)
    chat_message_id = Column(Integer, ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False)
    file_name = Column(String(255), nullable=False)
    content = Column(String, nullable=False)

    __table_args__ = (
            Index('idx_file_name', 'file_name'),
        )
