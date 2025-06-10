from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from uuid import UUID


class OrderDTO(BaseModel):
    h_order_pk: UUID
    order_id: int
    order_dt: datetime
    cost: Decimal = Field(max_digits=19, decimal_places=5)
    payment: Decimal = Field(max_digits=19, decimal_places=5)
    hk_order_cost_hashdiff: UUID
    status: str
    hk_order_status_hashdiff: UUID


class ProductDTO(BaseModel):
    h_product_pk: UUID
    product_id: str
    product_name: str
    hk_product_names_hashdiff: UUID
    category_name: str


class RestaurantDTO(BaseModel):
    h_restaurant_pk: UUID
    restaurant_id: str
    restaurant_name: str
    hk_restaurant_names_hashdiff: UUID


class UserDTO(BaseModel):
    h_user_pk: UUID
    user_id: str
    user_name: str
    user_login: str


class CategoryDTO(BaseModel):
    h_category_pk: UUID
    category_name: str


class OutputMessageDTO(BaseModel):
    user_id: str
    product_id: str
    product_name: str
    order_cnt: int