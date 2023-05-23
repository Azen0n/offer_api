from enum import Enum

from pydantic import BaseModel, Field


class ProductStatus(str, Enum):
    AVAILABLE = 'AVAILABLE'
    UNAVAILABLE = 'UNAVAILABLE'
    BOOKED = 'BOOKED'
    EXECUTION = 'EXECUTION'
    SOLD = 'SOLD'


class Product(BaseModel):
    """Товар."""
    id: int = Field(...)
    status: ProductStatus = Field(..., description=f'Статус товара')


class ProductId(BaseModel):
    """Товар."""
    id: int = Field(...)
