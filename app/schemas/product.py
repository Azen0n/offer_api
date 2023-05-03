import uuid

from pydantic import BaseModel, Field


class Product(BaseModel):
    """Товар."""
    id: str = Field(default_factory=uuid.uuid4, alias='_id')
