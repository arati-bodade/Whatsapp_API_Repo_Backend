from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
from datetime import datetime
from uuid import UUID

class BusinessUserStats(BaseModel):
    user_id: Union[str, UUID] = Field(..., description="UUID of the business user")
    business_name: str = Field(..., description="Name of the business")
    credits_allocated: int = Field(..., ge=0, description="Total credits allocated to business")
    credits_used: int = Field(..., ge=0, description="Credits used by business")
    credits_remaining: int = Field(..., ge=0, description="Remaining credits for business")
    messages_sent: int = Field(..., ge=0, description="Total messages sent by business")

class Transaction(BaseModel):
    id: str
    type: str = Field(..., description="Type of transaction: 'distribution' or 'purchase'")
    description: str
    amount: int
    date: datetime
    status: str = "completed"

class ResellerAnalytics(BaseModel):
    total_credits_purchased: int = Field(..., ge=0, description="Total credits purchased by reseller")
    total_credits_distributed: int = Field(..., ge=0, description="Total credits distributed to businesses")
    total_credits_used: int = Field(..., ge=0, description="Total credits used by all businesses")
    remaining_credits: int = Field(..., ge=0, description="Remaining credits with reseller")

class ResellerDashboardResponse(BaseModel):
    reseller_id: Union[str, UUID] = Field(..., description="UUID of the reseller")
    
    # Flat structure as requested
    total_credits: int = Field(..., ge=0, description="Total credits purchased")
    used_credits: int = Field(..., ge=0, description="Total credits used by businesses")
    remaining_credits: int = Field(..., ge=0, description="Remaining credits available to distribute")
    wallet_balance: int = Field(..., ge=0, description="Current available credits in wallet")
    messages_sent: int = Field(..., ge=0, description="Total messages sent by all businesses")
    
    # Lists
    business_users: List[BusinessUserStats] = Field(default_factory=list)
    recent_transactions: List[Transaction] = Field(default_factory=list)
    
    # New Sections
    plan_details: dict = Field(default_factory=dict, description="Plan information (Mock)")
    account_info: dict = Field(default_factory=dict, description="Account details (Real)")
    traffic_source: List[dict] = Field(default_factory=list, description="Traffic/User distribution by country (Real)")
    graph_data: List[dict] = Field(default_factory=list, description="Aggregate message performance by month (Real)")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ResellerAnalyticsCreate(BaseModel):
    reseller_id: Union[str, UUID]
    total_credits_purchased: int
    total_credits_distributed: int
    total_credits_used: int
    remaining_credits: int

class ResellerAnalyticsUpdate(BaseModel):
    total_credits_purchased: Optional[int] = None
    total_credits_distributed: Optional[int] = None
    total_credits_used: Optional[int] = None
    remaining_credits: Optional[int] = None
