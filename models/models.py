from sqlalchemy import Column, String, Integer, Numeric, Boolean, Date, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from config.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dni = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    address = Column(Text)
    monthly_income = Column(Numeric(12, 2))
    employment_status = Column(String(100))
    employer_name = Column(String(255))
    credit_score = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    loans = relationship("Loan", back_populates="customer")

class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    loan_number = Column(String(50), unique=True)
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    interest_type = Column(String(20), nullable=False)
    term_months = Column(Integer, nullable=False)
    amortization_method = Column(String(50), default='fixed_capital')
    late_interest_rate = Column(Numeric(5, 2), default=0.00)
    late_fee_amount = Column(Numeric(10, 2), default=0.00)
    disbursement_date = Column(Date, nullable=False)
    first_payment_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    status = Column(String(50), default='pending')
    total_amount = Column(Numeric(12, 2))
    total_interest = Column(Numeric(12, 2))
    paid_amount = Column(Numeric(12, 2), default=0.00)
    outstanding_balance = Column(Numeric(12, 2))
    dti_ratio = Column(Numeric(5, 2))
    version = Column(Integer, default=1)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="loans")
    payment_schedule = relationship("PaymentSchedule", back_populates="loan", lazy="joined")
    payments = relationship("Payment", back_populates="loan")

class PaymentSchedule(Base):
    __tablename__ = "payment_schedule"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_amount = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    remaining_balance = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0.00)
    paid_principal = Column(Numeric(12, 2), default=0.00)
    paid_interest = Column(Numeric(12, 2), default=0.00)
    outstanding_amount = Column(Numeric(12, 2))
    status = Column(String(50), default='pending')
    paid_date = Column(Date)
    days_overdue = Column(Integer, default=0)
    late_fee = Column(Numeric(10, 2), default=0.00)
    late_interest = Column(Numeric(10, 2), default=0.00)
    schedule_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    loan = relationship("Loan", back_populates="payment_schedule")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"), nullable=False)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("payment_schedule.id"))
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    principal_paid = Column(Numeric(12, 2), default=0.00)
    interest_paid = Column(Numeric(12, 2), default=0.00)
    late_fee_paid = Column(Numeric(12, 2), default=0.00)
    late_interest_paid = Column(Numeric(12, 2), default=0.00)
    payment_method = Column(String(50))
    reference_number = Column(String(100))
    notes = Column(Text)
    status = Column(String(50), default='pending')
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    loan = relationship("Loan", back_populates="payments")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"))
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("payment_schedule.id"))
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50))
    status = Column(String(50), default='pending')
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)