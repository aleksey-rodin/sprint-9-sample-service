import json
import time
from datetime import datetime
from logging import Logger
from lib.kafka_connect.kafka_connectors import KafkaConsumer, KafkaProducer
from lib.redis.redis_client import RedisClient
from stg_loader.repository.stg_repository import StgRepository


class StgMessageProcessor:
    def __init__(self,
                 consumer: KafkaConsumer,
                 producer: KafkaProducer,
                 redis: RedisClient,
                 stg_repository: StgRepository,
                 batch_size: int,
                 logger: Logger) -> None:
        self._logger = logger
        self._consumer = consumer
        self._producer = producer
        self._redis = redis
        self._stg_repository = stg_repository
        self._batch_size = batch_size

    def save_msg(self, message) -> None:
        self._stg_repository.order_events_insert(
            message.get('object_id'),
            message.get('object_type'),
            message.get('sent_dttm'),
            json.dumps(message.get('payload'))
        )

    def user_info(self, user) -> dict[str, str]:
        result = {
            "id": user.get("_id"),
            "name": user.get("name"),
            "login": user.get("login"),
        }
        return result

    def restaurant_info(self, restaurant) -> dict[str, str]:
        result = {
            "id": restaurant.get("_id"),
            "name": restaurant.get("name"),
        }
        return result

    def format_items(self, order_items, restaurant) -> list[dict[str, str]]:
        items = []
        try:
            menu = restaurant["menu"]
            for it in order_items:
                menu_item = next(x for x in menu if x["_id"] == it["id"])
                dst_it = {
                    "id": it["id"],
                    "price": it["price"],
                    "quantity": it["quantity"],
                    "name": menu_item["name"],
                    "category": menu_item["category"]
                }
                items.append(dst_it)
        except StopIteration as e:
            pass
        return items

    def get_redis_item(self, k: str) -> dict[str, str]:
        result = self._redis.get(k)
        if result is None:
            return {}

        return result

    # функция, которая будет вызываться по расписанию.
    def run(self) -> None:
        # Пишем в лог, что джоб был запущен.
        self._logger.info(f"{datetime.utcnow()}: START")

        # Имитация работы. Здесь будет реализована обработка сообщений.
        for _ in range(self._batch_size):
            msg = self._consumer.consume()
            if not msg:
                break

            self._logger.info(f"{datetime.utcnow()}: Message received")

            if msg.get('object_id') is not None:
                self.save_msg(msg)

                payload = msg.get('payload')

                user_id = payload.get('user').get('id')
                if user_id is not None:
                    user = self.get_redis_item(user_id)

                restaurant_id = payload.get('restaurant').get('id')
                if restaurant_id is not None:
                    restaurant = self.get_redis_item(restaurant_id)

                dst_msg = {
                    "object_id": msg.get("object_id"),
                    "object_type": "order",
                    "payload": {
                        "id": msg.get("object_id"),
                        "date": payload.get("date"),
                        "cost": payload.get("cost"),
                        "payment": payload.get("payment"),
                        "status": payload.get("final_status"),
                        "restaurant": self.restaurant_info(restaurant),
                        "user": self.user_info(user),
                        "products": self.format_items(payload.get("order_items"), restaurant)
                    }
                }

                self._producer.produce(dst_msg)

        # Пишем в лог, что джоб успешно завершен.
        self._logger.info(f"{datetime.utcnow()}: FINISH")
