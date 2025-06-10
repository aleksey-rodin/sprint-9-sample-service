from pydantic import BaseModel, Field
from uuid import UUID


class ProductCounters(BaseModel):
    user_id: UUID
    product_id: UUID
    product_name: str
    order_cnt: int
