from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from datetime import datetime
from typing import Optional, Annotated


class MessageUsageCreditLogBase(BaseModel):
    busi_user_id: Annotated[str, BeforeValidator(str)] = Field(..., description="UUID of the user (reseller or business)")
    message_id: str = Field(..., description="ID of the message")
    credits_deducted: float = Field(..., description="Number of credits deducted (negative for additions)")
    balance_after: float = Field(..., description="Remaining balance after deduction")


class MessageUsageCreditLogCreate(MessageUsageCreditLogBase):
    timestamp: Optional[datetime] = None


class MessageUsageCreditLogResponse(MessageUsageCreditLogBase):
    usage_id: Annotated[str, BeforeValidator(str)]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageUsageCreditLogUpdate(BaseModel):
    credits_deducted: Optional[float] = Field(None)
    balance_after: Optional[float] = Field(None)
    source: Optional[str] = Field(None)
