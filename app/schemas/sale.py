import uuid

from pydantic import BaseModel, Field


class Sale(BaseModel):
    """Продажа."""
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
