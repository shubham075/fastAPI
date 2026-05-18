#This file repersents actual sql server tables

from sqlalchemy import Column, Integer, String
from app.datbase import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email_id = Column(String(255), index=True, unique=True, nullable=False)

    