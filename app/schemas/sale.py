from pydantic import BaseModel, Field


class SaleId(BaseModel):
    """Продажа."""
    id: int = Field(...)
