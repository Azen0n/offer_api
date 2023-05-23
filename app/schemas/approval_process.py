from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field

from .offer import OfferId
from .product import Product, ProductId
from .pyobjectid import PyObjectId
from .sale import SaleId


class ApprovalProcessStatus(str, Enum):
    PENDING = 'Ожидание'
    APPROVED = 'Одобрен'
    CANCELLED = 'Отменён'
    REJECTED = 'Отклонён'


class ApprovalProcess(BaseModel):
    """Процесс согласования акционной продажи."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    status: ApprovalProcessStatus = Field(..., description=f'Статус согласования')
    product: ProductId = Field(..., description='Товар')
    offers: list[OfferId] = Field(..., description='Применяемые к товару акции')
    sale: SaleId = Field(..., description='ID продажи')

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


class CreateApprovalProcess(BaseModel):
    """Схема создания процесса согласования акционной продажи."""
    status: ApprovalProcessStatus = Field(..., description=f'Статус согласования')
    product: ProductId = Field(..., description='Товар')
    offers: list[OfferId] = Field(..., description='Применяемые к товару акции')
    sale: SaleId = Field(..., description='ID продажи')

    class Config:
        json_encoders = {ObjectId: str}
