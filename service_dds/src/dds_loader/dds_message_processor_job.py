import time
from datetime import datetime
from logging import Logger
from typing import Any
from uuid import uuid4

from lib.kafka_connect.kafka_connectors import KafkaConsumer, KafkaProducer
from dds_loader.repository.dds_repository import DDSRepository
from service_dds.src.dds_loader.repository.dds_dto import *


class DDSMessageProcessor:
    def __init__(self,
                 consumer: KafkaConsumer,
                 producer: KafkaProducer,
                 dds_repository: DDSRepository,
                 batch_size: int,
                 logger: Logger) -> None:
        self._logger = logger
        self._consumer = consumer
        self._producer = producer
        self._dds_repository = dds_repository
        self._batch_size = batch_size

    def order_info(self, order) -> dict[str, Any]:
        result = {
            "h_order_pk": uuid4(),
            "order_id": order.get("id"),
            "order_dt": order.get("date"),
            "cost": order.get("cost"),
            "payment": order.get("payment"),
            "hk_order_cost_hashdiff": self._dds_repository.generate_uuid(str(order.get("id"))),
            "status": order.get("status"),
            "hk_order_status_hashdiff": self._dds_repository.generate_uuid(str(order.get("id"))),
        }
        return result

    def product_info(self, products) -> list[dict[str, Any]]:
        result = []
        for product in products:
            item = {
                "h_product_pk": uuid4(),
                "product_id": product.get("id"),
                "product_name": product.get("name"),
                "hk_product_names_hashdiff": self._dds_repository.generate_uuid(product.get("id")),
                "category_name": product.get("category")
            }
            result.append(item)
        return result

    def restaurant_info(self, restaurant) -> dict[str, Any]:
        result = {
            "h_restaurant_pk": uuid4(),
            "restaurant_id": restaurant.get("id"),
            "restaurant_name": restaurant.get("name"),
            "hk_restaurant_names_hashdiff": self._dds_repository.generate_uuid(restaurant.get("id")),
        }
        return result

    def user_info(self, user) -> dict[str, Any]:
        result = {
            "h_user_pk": uuid4(),
            "user_id": user.get("id"),
            "user_name": user.get("name"),
            "user_login": user.get("login"),
        }
        return result

    def category_info(self, products) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for category in products:
            item = {
                "category_name": category.get("category"),
                "h_category_pk": self._dds_repository.generate_uuid(category.get("category"))
            }
            pk = item["h_category_pk"]
            if pk not in seen:
                seen.add(pk)
                result.append(item)

        return result

    def format_outputmsg(self, output_msg, user_id) -> dict[str, Any]:
        result = {
            "user_id": user_id,
            "message": [
                {
                    "user_id": str(obj.user_id),
                    "product_id": str(obj.product_id),
                    "product_name": str(obj.product_name),
                    "order_cnt": obj.order_cnt
                }
                for obj in output_msg
            ]
        }
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

            if msg.get('payload') is not None:
                self._logger.info(f"{datetime.utcnow()}: Inserting hubs")

                order_data = self.order_info(msg.get("payload"))
                order = OrderDTO(**order_data)
                self._dds_repository.h_order_insert(
                    order=order,
                    load_src='kafka_stg'
                )

                products_data = self.product_info(msg.get("payload").get("products"))
                products = [ProductDTO(**x) for x in products_data]
                for item in products:
                    self._dds_repository.h_product_insert(
                        product=item,
                        load_src='kafka_stg'
                    )

                restaurant_data = self.restaurant_info(msg.get("payload").get("restaurant"))
                restaurant = RestaurantDTO(**restaurant_data)
                self._dds_repository.h_restaurant_insert(
                    restaurant=restaurant,
                    load_src='kafka_stg'
                )

                user_data = self.user_info(msg.get("payload").get("user"))
                user = UserDTO(**user_data)
                self._dds_repository.h_user_insert(
                    user=user,
                    load_src='kafka_stg'
                )

                category_data = self.category_info(msg.get("payload").get("products"))
                category = [CategoryDTO(**x) for x in category_data]
                for item in category:
                    self._dds_repository.h_category_insert(
                        category=item,
                        load_src='kafka_stg'
                    )

                self._logger.info(f"{datetime.utcnow()}: Inserting links")
                for item in products:
                    self._dds_repository.l_order_product_insert(
                        order=order,
                        product=item,
                        load_src="kafka_stg"
                    )
                    self._dds_repository.l_product_restaurant_insert(
                        restaurant=restaurant,
                        product=item,
                        load_src="kafka_stg"
                    )
                    self._dds_repository.l_product_category_insert(
                        product=item,
                        load_src="kafka_stg"
                    )
                self._dds_repository.l_order_user_insert(
                    user=user,
                    order=order,
                    load_src="kafka_stg"
                )

                self._logger.info(f"{datetime.utcnow()}: Inserting satellites")
                self._dds_repository.s_user_names_insert(
                    user=user,
                    load_src="kafka_stg"
                )
                for item in products:
                    self._dds_repository.s_product_names_insert(
                        product=item,
                        load_src="kafka_stg"
                    )
                self._dds_repository.s_restaurant_names_insert(
                    restaurant=restaurant,
                    load_src="kafka_stg"
                )
                self._dds_repository.s_order_cost_insert(
                    order=order,
                    load_src="kafka_stg"
                )
                self._dds_repository.s_order_status_insert(
                    order=order,
                    load_src="kafka_stg"
                )

                self._logger.info(f"{datetime.utcnow()}: Generate output message kafka")
                product_ids = tuple(f"{product.product_id}" for product in products)
                output_msg = self._dds_repository.output_message(
                    user=user,
                    product_ids=product_ids
                )

                if output_msg:
                    first_user_id = output_msg[0].user_id
                    dst_msg = self.format_outputmsg(
                        output_msg=output_msg,
                        user_id=first_user_id
                    )

                    if msg.get("payload").get("status") == 'CLOSED':
                        self._producer.produce(dst_msg)

        # Пишем в лог, что джоб успешно завершен.
        self._logger.info(f"{datetime.utcnow()}: FINISH")
