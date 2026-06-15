
from typing import Optional

from db_base.session import SessionLocal, engine
from db_base.base import Base
from sqlalchemy_models.chat import Chat
from sqlalchemy_models.chat_message import ChatMessage

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
        session = self.get_session()
        chat = Chat(title=chat_title)
        session.add(chat)
        session.commit()
        session.refresh(chat)
        return chat

    def update_chat_title(self, chat_id: int, new_title: str) -> None:
        """
        Update the title of an existing chat.

        Args:
            chat_id: The ID of the chat to be updated.
            new_title: The new title for the chat.

        Returns:
            None
        """
        session = self.get_session()
        chat = session.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            chat.title = new_title
            session.commit()

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
        session = self.get_session()
        if chat_id is not None:
            session = self.get_session()
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
        session = self.get_session()
        query = session.query(Chat)
        if title_query:
            query = query.filter(Chat.title.ilike(f"%{title_query}%"))
        return query.limit(max_results).all()

    def delete_chat(self, chat_id: Optional[int] = None, chat_title: Optional[str] = None) -> None:
        """
        Delete a chat by its ID or title.

        Args:
            chat_id: The ID of the chat to delete.
            chat_title: The title of the chat to delete.
        """

        if chat_id is None and chat_title is None:
            raise ValueError("Either chat_id or chat_title must be provided.")
        session = self.get_session()
        if chat_id is not None:
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
        elif chat_title is not None:
            chat = session.query(Chat).filter(Chat.title == chat_title).first()
        if chat:
            session.delete(chat)
            session.commit()
            
    def create_chat_message(self, chat_id: int, sender: str, message: str) -> ChatMessage:
        """
        Create a new chat message in the database.

        Args:
            chat_id: The ID of the chat to which the message belongs.
            sender: The sender of the message ('user' or 'bot').
            message: The content of the message.

        Returns:
            The created ChatMessage object.
        """
        session = self.get_session()
        chat_message = ChatMessage(chat_id=chat_id, sender=sender, message=message)
        session.add(chat_message)
        session.commit()
        session.refresh(chat_message)
        return chat_message

    def get_chat_messages(self, chat_id: int) -> list[ChatMessage]:
        """
        Get all chat messages for a given chat ID.

        Args:
            chat_id: The ID of the chat for which to retrieve messages.
        Returns:
            A list of ChatMessage objects associated with the specified chat ID.
        """
        session = self.get_session()
        return session.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.index).all()


db = Database(SessionLocal, engine)

__all__ = ["db"]
