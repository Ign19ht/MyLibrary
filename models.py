from typing import List

from sqlalchemy import Column, Integer, String, DateTime
from db_manager import DeclarativeBase


# declare models for database


class Words(DeclarativeBase):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    description = Column(String, nullable=False)
    image_extension = Column(String, nullable=False)
    approve = Column(Integer, default=0)


class Admins(DeclarativeBase):
    __tablename__ = 'admins'
    username = Column(String, primary_key=True, nullable=False)
    password = Column(String, primary_key=True, nullable=False)


class Cookies(DeclarativeBase):
    __tablename__ = 'cookies'
    cookie = Column(String, primary_key=True, nullable=False)
    date = Column(DateTime, nullable=False)

