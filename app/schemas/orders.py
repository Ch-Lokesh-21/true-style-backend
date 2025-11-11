# app/schemas/orders.py
from typing import Optional, Annotated
from datetime import datetime, date

from pydantic import BaseModel, Field, FutureDate, field_validator
from app.schemas.object_id import PyObjectId

Money = Annotated[float, Field(ge=0, description="Order total; non-negative")]
OTP = Annotated[int, Field(ge=0, le=999_999, description="Delivery OTP (e.g., 6 digits)")]

class OrdersBase(BaseModel):
    user_id: PyObjectId          
    address: dict       
    status_id: PyObjectId         
    total: Money
    delivery_otp: Optional[OTP] = None
    delivery_date: date
    model_config = {"extra": "ignore"}

class OrdersCreate(OrdersBase):
    pass

class OrdersUpdate(BaseModel):
    delivery_date: Optional[date]=None
    status_id: Optional[PyObjectId] = None
    model_config = {"extra": "ignore"}

class OrdersOut(OrdersBase):
    id: PyObjectId = Field(alias="_id")
    createdAt: datetime
    updatedAt: datetime
    @field_validator("delivery_date", mode="before")
    def convert_dt_to_date(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v
    model_config = {
        "populate_by_name": True,
        "from_attributes": False,
        "json_encoders": {PyObjectId: str},
        "extra": "ignore",
    }
