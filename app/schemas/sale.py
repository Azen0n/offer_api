from pydantic import BaseModel, Field


class Sale(BaseModel):
    """Продажа."""
    id: int = Field(..., alias='_id')
