import os
import uvicorn
from fastapi import FastAPI, File, UploadFile
from database import engine, Base, get_db
import json
from aio_pika import IncomingMessage
from rabbit.server import connect_to_broker, send_message_to_queue
from service.bd_save import create_message 
from dto.message_dto import Message as MessageDTO
from models.message import Message
from fastapi import Depends
from sqlalchemy.orm import Session

import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# конфиг для того, что бы протестировать приложение с дефолт значениями
EXCHANGE_NAME = os.environ.get("EXCHANGE_NAME", "my_exchange_name")
ROUTING_KEY = os.environ.get("ROUTING_KEY", "my_routing_key")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "my_queue_name")


app = FastAPI(docs_url='/')
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def startup_event():
    """Устанавливаем соединение с брокером при запуске приложения."""
    channel = await connect_to_broker()
    app.state.rabbitmq_channel = channel

    await consume_from_queue(channel)


@app.post("/file/upload-bytes")
async def upload_file_bytes(file: UploadFile = File(...)):
    """Создаем точку для скачивания файла.
    Далее данные из файла счиываются и отправляются в брокер."""
    contents = await file.read()
    data = json.loads(contents.decode())

    channel = app.state.rabbitmq_channel
    await send_message_to_queue(channel, json.dumps(data), EXCHANGE_NAME, ROUTING_KEY, QUEUE_NAME)

    logger.info("Данные файла отправлены в брокер")


async def consume_from_queue(channel):
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    async def callback(message: IncomingMessage):
        """Получение данных из брокера и сохраняем в базу"""
        async with message.process():
            data = json.loads(message.body.decode())
            date = data.get('datetime', '')
            title = data.get('title', '')
            text_data = data.get('text', '')

            count_of_x = text_data.lower().count('x')
            len_text_data = len(text_data)

            db = next(get_db())

            create_message_data = MessageDTO(date=date, title=title, count_of_x=count_of_x, len_text_data=len_text_data)
            create_message(create_message_data, db)

    await queue.consume(callback)


@app.get("/message/{message_id}")
async def read_message(message_id: int, db: Session = Depends(get_db)):
    """Получение данных из базы данных по ID."""
    message = db.query(Message).filter(Message.id == message_id).first()
    if message:
        x_avg_count_in_line = message.count_of_x / message.len_text_data
        return {"id": message.id, "date": message.date, "title": message.title, "x_avg_count_in_line": x_avg_count_in_line}
    logger.warning("Cообщения с этим id не существует в базе")


def main():
    uvicorn.run(
        f"main:app",
        host='0.0.0.0', port=8888,
        debug=True,
    )

if __name__ == '__main__':
    main()
