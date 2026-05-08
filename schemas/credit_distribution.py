from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class CreditDistributionCreateSchema(BaseModel):
    from_reseller_id: uuid.UUID = Field(..., description="Reseller ID sharing credits")
    to_business_user_id: uuid.UUID = Field(..., description="Business user ID receiving credits")
    credits_shared: int = Field(..., gt=0, description="Number of credits to share")


class CreditDistributionResponseSchema(BaseModel):
    distribution_id: str
    from_reseller_id: uuid.UUID
    to_business_user_id: uuid.UUID
    credits_shared: int
    shared_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreditDistributionSummarySchema(BaseModel):
    """Schema for credit distribution summary with reseller and business details."""
    distribution_id: str
    from_reseller_id: uuid.UUID
    to_business_user_id: uuid.UUID
    credits_shared: int
    shared_at: datetime
    created_at: datetime
    
    # Additional details for better response
    from_reseller_name: Optional[str] = None
    from_reseller_username: Optional[str] = None
    to_business_name: Optional[str] = None
    to_business_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CreditDistributionListSchema(BaseModel):
    """Schema for list of credit distributions with pagination."""
    distributions: list[CreditDistributionSummarySchema]
    total: int
    page: int
    size: int
    pages: int


class CreditBalanceUpdateSchema(BaseModel):
    """Schema for updating credit balances after distribution."""
    reseller_available_credits: int
    business_credits_allocated: int
    business_credits_remaining: int
