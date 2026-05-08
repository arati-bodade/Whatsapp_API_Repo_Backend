from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class ProfileSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8, max_length=255)


class ProfileResponseSchema(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    profile_image: Optional[str] = None


class ProfileUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=255)


class BusinessSchema(BaseModel):
    business_name: Optional[str] = Field(None, max_length=255)
    organization_type: Optional[str] = Field(None, max_length=100)
    business_description: Optional[str] = None
    erp_system: Optional[str] = Field(None, max_length=100)
    gstin: Optional[str] = Field(None, min_length=15, max_length=20)


class AddressSchema(BaseModel):
    full_address: Optional[str] = None
    pincode: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)


class BankSchema(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=255)


class WalletSchema(BaseModel):
    total_credits: float = Field(default=0.0, ge=0.0)
    available_credits: float = Field(default=0.0, ge=0.0)
    used_credits: float = Field(default=0.0, ge=0.0)


class ResellerCreateSchema(BaseModel):
    role: str = Field(default="reseller", max_length=50)
    status: str = Field(default="active", max_length=20)
    profile: ProfileSchema
    business: Optional[BusinessSchema] = None
    address: Optional[AddressSchema] = None
    bank: Optional[BankSchema] = None
    wallet: Optional[WalletSchema] = WalletSchema()


class ResellerUpdateSchema(BaseModel):
    role: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    profile: Optional[ProfileUpdateSchema] = None
    business: Optional[BusinessSchema] = None
    address: Optional[AddressSchema] = None
    bank: Optional[BankSchema] = None
    wallet: Optional[WalletSchema] = None


class ResellerResponseSchema(BaseModel):
    reseller_id: uuid.UUID
    role: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    profile: ProfileResponseSchema
    business: Optional[BusinessSchema] = None
    address: Optional[AddressSchema] = None
    bank: Optional[BankSchema] = None
    wallet: WalletSchema
    
    # [NEW] Plan fields
    plan_name: Optional[str] = None
    plan_expiry: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResellerLoginSchema(BaseModel):
    email: EmailStr
    password: str


class ResellerResponseWithTokenSchema(BaseModel):
    reseller: ResellerResponseSchema
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ResellerLogoutResponseSchema(BaseModel):
    message: str
    detail: str
