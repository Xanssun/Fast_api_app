from models.message import Message  # Update the import if needed
from sqlalchemy.orm import Session
from dto import message_dto

def create_message(data: message_dto.Message, db: Session):
    # Fix the variable name here
    message = Message(date=data.date, title=data.title, count_of_x=data.count_of_x, len_text_data=data.len_text_data)

    try:
        db.add(message)  # Fix the variable name here
        db.commit()
    except Exception as e:
        print(e)
    
    return message  # Fix the variable name here