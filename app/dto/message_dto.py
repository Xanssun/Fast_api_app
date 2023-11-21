from pydantic import BaseModel


class Message(BaseModel):
    date: str
    title: str
    count_of_x: int
    len_text_data: float
