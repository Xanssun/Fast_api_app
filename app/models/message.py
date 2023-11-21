from sqlalchemy import Float, Column, Integer, String
from database import Base


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True, index=True, unique=True)
    date = Column(String)
    title = Column(String, unique=True, index=True)
    count_of_x = Column(Integer)
    len_text_data = Column(Float)
