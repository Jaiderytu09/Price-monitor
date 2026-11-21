from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    url: HttpUrl
    target_price: float = Field(..., gt=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    target_price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class PriceHistoryResponse(BaseModel):
    id: int
    price: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: int
    name: str
    url: str
    target_price: float
    current_price: float | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)