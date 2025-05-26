import uuid

from sqlalchemy import Column, String, Integer, ForeignKey, Text, UUID
from sqlalchemy.orm import relationship
from models.Base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    conversations = relationship("Conversation", back_populates="user")