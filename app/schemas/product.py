from pydantic import BaseModel, Field


class Product(BaseModel):
    """Товар."""
    id: int = Field(..., alias='_id')
