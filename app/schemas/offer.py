from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field

from schemas.product import Product
from schemas.pyobjectid import PyObjectId


class OfferStatus(str, Enum):
    ACTIVE = 'Активная'
    INACTIVE = 'Не активная'
    ARCHIVED = 'Архивная'


class Offer(BaseModel):
    """Акция на товар."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    compatible_products: list[Product] = Field(..., description='Совместимые по параметрам товары')
    status: OfferStatus = Field(..., description=f'Статус акции')
    start_date: datetime = Field(..., description='Дата начала действия акции')
    end_date: datetime | None = Field(..., description='Дата окончания действия акции')
    application_limit: int = Field(..., ge=1, description='Количество возможных применений при продажах товаров')

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


class OfferId(BaseModel):
    """Id товара."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    
    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


class WriteOffer(BaseModel):
    """Схема создания и обновления товара без списка совместимых по параметрам товаров."""
    status: OfferStatus = Field(..., description=f'Статус акции')
    start_date: datetime = Field(..., description='Дата начала действия акции')
    end_date: datetime | None = Field(..., description='Дата окончания действия акции')
    application_limit: int = Field(..., ge=1, description='Количество возможных применений при продажах товаров')
