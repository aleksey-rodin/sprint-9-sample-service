from datetime import datetime
from logging import Logger
from typing import Any
from uuid import uuid4

from lib.kafka_connect.kafka_connectors import KafkaConsumer, KafkaProducer
from cdm_loader.repository.cdm_repository import CDMRepository
from cdm_loader.repository.cdm_dto import ProductCountersDTO


class CDMMessageProcessor:
    def __init__(self,
                 consumer: KafkaConsumer,
                 cdm_repository: CDMRepository,
                 batch_size: int,
                 logger: Logger) -> None:
        self._logger = logger
        self._consumer = consumer
        self._cdm_repository = cdm_repository
        self._batch_size = batch_size

    # функция, которая будет вызываться по расписанию.
    def run(self) -> None:
        # Пишем в лог, что джоб был запущен.
        self._logger.info(f"{datetime.utcnow()}: START")

        # Имитация работы. Здесь будет реализована обработка сообщений.
        for _ in range(self._batch_size):
            msg = self._consumer.consume()
            if not msg:
                break

            user_products_data = msg.get("message")
            user_products = [ProductCountersDTO(**x) for x in user_products_data]
            for product in user_products:
                self._cdm_repository.user_product_counters_insert(product)

            user_id = msg.get("user_id")
            self._cdm_repository.user_category_counters_insert(user_id)

        # Пишем в лог, что джоб успешно завершен.
        self._logger.info(f"{datetime.utcnow()}: FINISH")
