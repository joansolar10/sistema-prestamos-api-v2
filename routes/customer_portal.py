from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from dateutil.relativedelta import relativedelta
from config.database import get_db
from models.models import Loan, Customer
from schemas.schemas import LoanResponse, LoanWithSchedule, LoanRequestCreate
from utils.security import get_current_customer
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/customer-portal", tags=["Customer Portal"])

@router.get("/loans", response_model=List[LoanWithSchedule])
def get_my_loans(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    loans = db.query(Loan).options(
        joinedload(Loan.payment_schedule)
    ).filter(Loan.customer_id == current_customer.id).all()
    
    print(f"Loans found: {len(loans)}")  # DEBUG
    if loans:
        print(f"First loan schedules: {len(loans[0].payment_schedule)}")  # DEBUG
    
    return loans

@router.get("/loans/{loan_id}", response_model=LoanWithSchedule)
def get_my_loan_detail(
    loan_id: UUID,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    loan = db.query(Loan).filter(
        Loan.id == loan_id,
        Loan.customer_id == current_customer.id
    ).first()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    return loan

@router.post("/loan-request", response_model=LoanResponse)
def request_loan(
    loan_data: LoanRequestCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    maturity_date = loan_data.first_payment_date + relativedelta(months=loan_data.term_months - 1)
    
    new_loan = Loan(
        customer_id=current_customer.id,
        principal_amount=loan_data.principal_amount,
        interest_rate=loan_data.interest_rate,
        interest_type='fixed',
        term_months=loan_data.term_months,
        disbursement_date=loan_data.disbursement_date,
        first_payment_date=loan_data.first_payment_date,
        maturity_date=maturity_date,
        status='pending'
    )
    
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan