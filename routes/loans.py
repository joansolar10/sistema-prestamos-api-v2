from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from config.database import get_db
from models.models import Loan, Customer, PaymentSchedule, User
from schemas.schemas import LoanCreate, LoanResponse, LoanWithSchedule
from utils.security import get_current_user

router = APIRouter(prefix="/loans", tags=["Loans"])

def calculate_payment_schedule(loan: Loan):
    """Calcula el cronograma de pagos con método de capital fijo"""
    schedule = []
    remaining_balance = loan.principal_amount
    monthly_interest = loan.interest_rate / 100 / 12
    fixed_principal = loan.principal_amount / loan.term_months
    
    current_date = loan.first_payment_date
    
    for i in range(1, loan.term_months + 1):
        interest_amount = remaining_balance * monthly_interest
        total_payment = fixed_principal + interest_amount
        remaining_balance -= fixed_principal
        
        if remaining_balance < 0.01:
            remaining_balance = Decimal('0.00')
        
        schedule.append({
            'installment_number': i,
            'due_date': current_date,
            'principal_amount': round(fixed_principal, 2),
            'interest_amount': round(interest_amount, 2),
            'total_amount': round(total_payment, 2),
            'remaining_balance': round(remaining_balance, 2),
            'status': 'pending'
        })
        
        current_date = current_date + relativedelta(months=1)
    
    return schedule

@router.post("/", response_model=LoanWithSchedule, status_code=status.HTTP_201_CREATED)
def create_loan(
    loan: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == loan.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    maturity_date = loan.first_payment_date + relativedelta(months=loan.term_months - 1)
    
    new_loan = Loan(
        **loan.model_dump(),
        maturity_date=maturity_date,
        created_by=current_user.id,
        status='active'
    )
    
    schedule_data = calculate_payment_schedule(new_loan)
    
    total_interest = sum(item['interest_amount'] for item in schedule_data)
    new_loan.total_interest = total_interest
    new_loan.total_amount = new_loan.principal_amount + total_interest
    new_loan.outstanding_balance = new_loan.total_amount
    
    if customer.monthly_income and customer.monthly_income > 0:
        new_loan.dti_ratio = (new_loan.total_amount / loan.term_months) / customer.monthly_income * 100
    
    db.add(new_loan)
    db.flush()
    
    for item in schedule_data:
        payment = PaymentSchedule(
            loan_id=new_loan.id,
            installment_number=item['installment_number'],
            due_date=item['due_date'],
            principal_amount=item['principal_amount'],
            interest_amount=item['interest_amount'],
            total_amount=item['total_amount'],
            remaining_balance=item['remaining_balance'],
            outstanding_amount=item['total_amount'],
            status='pending'
        )
        db.add(payment)
    
    db.commit()
    db.refresh(new_loan)
    
    return new_loan

@router.get("/", response_model=List[LoanResponse])
def get_loans(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Loan)
    if status:
        query = query.filter(Loan.status == status)
    loans = query.offset(skip).limit(limit).all()
    return loans

@router.get("/{loan_id}", response_model=LoanWithSchedule)
def get_loan(
    loan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    return loan