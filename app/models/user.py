from app.core.database import Base
from sqlalchemy import Column,Integer,String

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    first_name=Column(String(50))
    last_name=Column(String(50))
    email=Column(String(100),unique=True)
    password=Column(String(250))