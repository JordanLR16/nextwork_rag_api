from pydantic import BaseModel, Field


class PantryItemIn(BaseModel):
    name: str = Field(min_length=1)
    quantity: float | None = None
    unit: str | None = None
