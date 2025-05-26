from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.Base import Base

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String)
    content = Column(Text)
    conversation_id = Column(String, ForeignKey('conversations.id'))

    conversation = relationship("Conversation", back_populates="messages")