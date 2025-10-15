from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

# Auth Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Customer Schemas
class CustomerBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=20)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    monthly_income: Optional[Decimal] = Field(None, ge=0)
    employment_status: Optional[str] = Field(None, max_length=100)
    employer_name: Optional[str] = Field(None, max_length=255)
    credit_score: Optional[int] = Field(None, ge=0, le=1000)

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    monthly_income: Optional[Decimal] = Field(None, ge=0)
    employment_status: Optional[str] = Field(None, max_length=100)
    employer_name: Optional[str] = Field(None, max_length=255)
    credit_score: Optional[int] = Field(None, ge=0, le=1000)

class CustomerResponse(CustomerBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Loan Schemas
class LoanBase(BaseModel):
    customer_id: UUID
    principal_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0, le=100)
    interest_type: str = Field(..., pattern="^(fixed|variable|indexed)$")
    term_months: int = Field(..., gt=0)
    amortization_method: str = Field(default="fixed_capital", pattern="^(fixed_capital|french|german|american)$")
    late_interest_rate: Optional[Decimal] = Field(default=0.00, ge=0)
    late_fee_amount: Optional[Decimal] = Field(default=0.00, ge=0)
    disbursement_date: date
    first_payment_date: date
    notes: Optional[str] = None

class LoanCreate(LoanBase):
    pass

class PaymentScheduleItem(BaseModel):
    id: UUID
    installment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    remaining_balance: Decimal
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class LoanResponse(LoanBase):
    id: UUID
    loan_number: str
    maturity_date: date
    status: str
    total_amount: Optional[Decimal]
    total_interest: Optional[Decimal]
    paid_amount: Decimal
    outstanding_balance: Optional[Decimal]
    dti_ratio: Optional[Decimal]
    version: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LoanWithSchedule(LoanResponse):
    payment_schedule: list[PaymentScheduleItem] = []
    

# Payment Schemas
class PaymentCreate(BaseModel):
    loan_id: UUID
    schedule_id: Optional[UUID] = None
    amount: Decimal
    payment_date: datetime
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = 'pending'

class PaymentResponse(BaseModel):
    id: UUID
    status: str
    loan_id: UUID
    payment_date: date
    amount: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    late_fee_paid: Decimal
    late_interest_paid: Decimal
    payment_method: Optional[str]
    reference_number: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaymentScheduleResponse(BaseModel):
    id: UUID
    installment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    remaining_balance: Decimal
    status: str
    
    class Config:
        from_attributes = True

class LoanWithSchedule(BaseModel):
    id: UUID
    loan_number: str
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    status: str
    outstanding_balance: Decimal
    paid_amount: Decimal
    payment_schedule: List[PaymentScheduleResponse] = []
    
    class Config:
        from_attributes = True

class LoanRequestCreate(BaseModel):
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    disbursement_date: date
    interest_type: str = 'fixed'

class CustomerRegister(BaseModel):
    dni: str
    full_name: str
    email: str
    phone: Optional[str] = None
    password: str
    