import os
import logging
from time import sleep
import aio_pika
from aio_pika.channel import Channel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# конфиг для того, что бы протестировать приложение с дефолт значениями
RMQ_LOGIN = os.environ.get("RMQ_LOGIN", "guest")
RMQ_PASSWORD = os.environ.get("RMQ_PASSWORD", "guest")
RMQ_HOST = os.environ.get("RMQ_HOST", "127.0.0.1")
RMQ_PORT = os.environ.get("RMQ_PORT", "5672")
BROKER_CONNECTION = None
BROKER_CHANNEL = None

async def connect_to_broker() -> Channel:
    """Подключение к брокеру и возвращат канал для работы с брокером."""
    global BROKER_CONNECTION
    global BROKER_CHANNEL

    retries = 0
    while not BROKER_CONNECTION:
        conn_str = f"amqp://{RMQ_LOGIN}:{RMQ_PASSWORD}@{RMQ_HOST}:{RMQ_PORT}/"
        logger.info(f"Пытаюсь установить соединение с брокером: {conn_str}")
        try:
            BROKER_CONNECTION = await aio_pika.connect_robust(conn_str)
            logger.info(f"Подключился к брокеру ({type(BROKER_CONNECTION)} ID {id(BROKER_CONNECTION)})")
        except Exception as e:
            retries += 1
            logger.warning(f"Не подключился к брокеру {retries} time({e.__class__.__name__}:{e}). Повторить черз 5 сек.")
            sleep(5)

    if not BROKER_CHANNEL:
        logger.info("Пытаюсь создать канал для брокера")
        BROKER_CHANNEL = await BROKER_CONNECTION.channel()
        logger.info("Получен канал для брокера")

    return BROKER_CHANNEL

async def send_message_to_queue(channel: Channel, message: str, exchange_name: str, routing_key: str, queue_name: str,
                                exchange_type='direct', durable=True, auto_delete=False):
    """Отправка сообщения в обменник с маршрутизацией в очередь."""
    exchange = await channel.declare_exchange(exchange_name, type=exchange_type, durable=durable, auto_delete=auto_delete)
    queue = await channel.declare_queue(queue_name, durable=durable)

    await queue.bind(exchange, routing_key=routing_key)

    await exchange.publish(
        aio_pika.Message(body=message.encode()),
        routing_key=routing_key
    )
    logger.info(f"Отправлено сообщение для обмена {exchange_name} с ключом {routing_key} и привязан к очереди {queue_name}: {message}")
