from sqlalchemy import BaseRow, Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Quotes(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True)
    message = Column(String)