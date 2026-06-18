"""
db.py

This module defines the Database class, which provides methods for interacting with the database using SQLAlchemy. 

The Database class includes the following methods:
- get_session: Returns a new session from the session factory.
- create_schema: Creates the database schema based on the provided Base class.
- create_chat: Creates a new chat in the database with the specified title.
- get_chat: Retrieves a chat by its ID or title.
- get_multiple_chats: Retrieves multiple chats, optionally filtered by a title query.
- delete_chat: Deletes a chat by its ID or title.
- create_chat_message: Creates a new chat message in the database for a specified chat ID,
    sender, and message content.

Author: P Tunis
"""

import logging
from typing import Dict, List, Optional

from db_base.session import SessionLocal, engine
from db_base.base import Base
from sqlalchemy_models.chat import Chat
from sqlalchemy_models.chat_message import ChatMessage
from sqlalchemy_models.file_context import FileContext

logger = logging.getLogger(__name__)


class Database:
    """
    Database class that provides a session factory for creating sessions to interact with the database.
    """

    def __init__(self, session_factory, engine):
        self.session_factory = session_factory
        self.engine = engine

    def get_session(self):
        """
        Get a new session from the session factory.
        """
        return self.session_factory()
    
    def create_schema(self):
        """
        Create the database schema based on the provided Base class.

        Args:
            Base: The declarative base class that defines the database models.
        """
        Base.metadata.create_all(bind=self.engine)
    
    def create_chat(self, chat_title: str) -> Chat:
        """
        Create a new chat in the database.

        Args:
            chat_title: The title of the chat to be created in the database.

        Returns:
            The created Chat object.
        """
        with self.get_session() as session:
            try:
                chat = Chat(title=chat_title)
                session.add(chat)
                session.commit()
                session.refresh(chat)
                logger.info(f"Created chat with ID {chat.id} and title '{chat.title}'")
                return chat
            except:
                session.rollback()
                logger.exception("Failed to create chat")
                raise

    def get_chat(self, chat_id: Optional[int] = None, chat_title: Optional[str] = None) -> Optional[Chat]:
        """
        Get a chat by its ID or title.

        Args:
            chat_id: The ID of the chat to retrieve.
            chat_title: The title of the chat to retrieve.

        Returns:
            The Chat object if found, otherwise None.
        """
        if chat_id is None and chat_title is None:
            raise ValueError("Either chat_id or chat_title must be provided.")
        with self.get_session() as session:
            if chat_id is not None:
                return session.query(Chat).filter(Chat.id == chat_id).first()
            if chat_title is not None:
                return session.query(Chat).filter(Chat.title == chat_title).first()


    def get_multiple_chats(self, title_query: Optional[str] = None, max_results: int = 25) -> list[Chat]:
        """
        Get multiple chats, optionally filtered by a title query.

        Args:
            title_query: An optional string to filter chats by title (case-insensitive, partial match).
            max_results: The maximum number of chat results to return.

        Returns:
            A list of Chat objects.
        """
        with self.get_session() as session:
            query = session.query(Chat)
            if title_query:
                query = query.filter(Chat.title.ilike(f"%{title_query}%"))
            return query.order_by(Chat.id.desc()).limit(max_results).all()


    def delete_chat(self, chat_id: Optional[int] = None, chat_title: Optional[str] = None) -> None:
        """
        Delete a chat by its ID or title.

        Args:
            chat_id: The ID of the chat to delete.
            chat_title: The title of the chat to delete.
        """

        if chat_id is None and chat_title is None:
            raise ValueError("Either chat_id or chat_title must be provided.")
        with self.get_session() as session:
            try:
                if chat_id is not None:
                    chat = session.query(Chat).filter(Chat.id == chat_id).first()
                elif chat_title is not None:
                    chat = session.query(Chat).filter(Chat.title == chat_title).first()
                if chat:
                    session.delete(chat)
                    session.commit()
                    logger.info(f"Deleted chat with ID {chat.id} and title '{chat.title}'")
            except:
                session.rollback()
                logger.exception("Failed to delete chat")
                raise

    def create_chat_message(self, chat_id: int, sender: str, message: str, file_context: Optional[List[Dict[str, str]]] = None) -> ChatMessage:
        """
        Create a new chat message in the database.

        Args:
            chat_id: The ID of the chat to which the message belongs.
            sender: The sender of the message ('user' or 'bot').
            message: The content of the message.
            file_context: Optional field for file attachment content. a dictionary with 'file_name' and 'content' keys.

        Returns:
            The created ChatMessage object.
        """
        with self.get_session() as session:
            try:
                chat_message = ChatMessage(chat_id=chat_id, sender=sender, message=message)
                session.add(chat_message)
                session.commit()
                session.refresh(chat_message)
                if file_context is not None:
                    for file_entry in file_context:
                        logger.debug(f"Creating file context for chat message ID {chat_message.id}: {file_entry}")
                        file_name = file_entry.get('file_name')
                        content = file_entry.get('content')
                        if file_name is None or content is None:
                            raise ValueError("file_context must contain 'file_name' and 'content' keys.")
                        
                        if not content.strip():
                            logger.warning(f"File context content is empty for file '{file_name}' in chat message ID {chat_message.id}. Skipping file context creation.")
                            continue
                        
                        file_context_entry = FileContext(chat_message_id=chat_message.id, file_name=file_name, content=content)
                        session.add(file_context_entry)
                        session.commit()

                logger.info(f"Created chat message with ID {chat_message.id} in chat ID {chat_id}")
                return chat_message
            except:
                session.rollback()
                logger.exception("Failed to create chat message")
                raise

    def _get_file_context_for_message(self, session, chat_message_id: int, get_file_content: bool) -> Optional[List[Dict[str, str]]]:
        """
        Get the associated file context for a given chat message ID.

        Args:
            session: The SQLAlchemy session to use for the query.
            chat_message_id: The ID of the chat message for which to retrieve the file context.
            get_file_content: If True, retrieves the associated file content. If False, only retrieves the file name without content.
        Returns:
            A list of dictionaries representing the file context associated with the specified chat message ID, or None if no file context is found.
        """
        file_context_entries = session.query(FileContext).filter(FileContext.chat_message_id == chat_message_id).all()

        if get_file_content:
            return [{"file_name": entry.file_name, "content": entry.content} for entry in file_context_entries]
        else:
            # Return only the file names without content
            return [{"file_name": entry.file_name, "content": None} for entry in file_context_entries]


    def get_chat_messages(self, chat_id: int, get_file_content: bool = False) -> list[ChatMessage]:
        """
        Get all chat messages for a given chat ID.

        Args:
            chat_id: The ID of the chat for which to retrieve messages.
            get_file_content: If True, retrieves the associated file content for each chat message. If False, only retrieves the file name without content.
        Returns:
            A list of ChatMessage objects associated with the specified chat ID.
        """
        with self.get_session() as session:
            chat_messages = session.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.id).all()
            # get the associated file context for each chat message
            for msg in chat_messages:   
                file_context = self._get_file_context_for_message(session, msg.id, get_file_content)
                msg.file_context = file_context if file_context else None
        return chat_messages

db = Database(SessionLocal, engine)

__all__ = ["db"]
