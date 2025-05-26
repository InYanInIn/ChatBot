from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.Base import Base

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(String, primary_key=True)
    conversation_name = Column(String)
    user_id = Column(String, ForeignKey('users.id'))

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
