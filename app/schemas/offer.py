from datetime import datetime
import uuid
from enum import Enum

from pydantic import BaseModel, Field

from schemas.product import Product


class OfferStatus(str, Enum):
    ACTIVE = 'Активная'
    INACTIVE = 'Не активная'
    ARCHIVED = 'Архивная'


class Offer(BaseModel):
    """Акция на товар."""
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
    compatible_products: list[Product] = Field(..., description='Совместимые по параметрам товары')
    status: OfferStatus = Field(..., description=f'Статус акции')
    start_date: datetime = Field(..., description='Дата начала действия акции')
    end_date: datetime | None = Field(..., description='Дата окончания действия акции')
    application_limit: int = Field(..., description='Количество возможных применений при продажах товаров')

    class Config:
        allow_population_by_field_name = True
