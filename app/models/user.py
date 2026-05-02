from sqlalchemy.sql import func

from app.core.database import Base
from sqlalchemy import TIMESTAMP, Column, ForeignKey,Integer,String, Text

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    first_name=Column(String(50))
    last_name=Column(String(50))
    email=Column(String(100),unique=True)
    password=Column(String(250))

class Conversation(Base):
    __tablename__ = "conversations"

    thread_id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    thread_id = Column(String)
    role = Column(String)
    content = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())