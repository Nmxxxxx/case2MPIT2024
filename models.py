from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Item(Base):
    __tablename__ = 'giga' 

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    tags = Column(String)