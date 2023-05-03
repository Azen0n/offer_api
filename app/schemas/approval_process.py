import uuid
from enum import Enum

from pydantic import BaseModel, Field

from .offer import Offer
from .product import Product
from .sale import Sale


class ApprovalProcessStatus(str, Enum):
    PENDING = 'Ожидание'
    APPROVED = 'Одобрен'
    CANCELLED = 'Отменён'
    REJECTED = 'Отклонён'


class ApprovalProcess(BaseModel):
    """Процесс согласования акционной продажи."""
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
    status: ApprovalProcessStatus = Field(..., description=f'Статус согласования')
    product: Product = Field(..., description='Товар')
    offers: list[Offer] = Field(..., description='Применяемые к товару акции')
    sale: Sale = Field(..., description='ID продажи')

    class Config:
        allow_population_by_field_name = True
