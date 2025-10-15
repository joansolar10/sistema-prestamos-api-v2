from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from config.database import get_db
from models.models import Payment, Loan, PaymentSchedule, User, Customer
from schemas.schemas import PaymentCreate, PaymentResponse
from utils.security import get_current_user, get_current_customer
from decimal import Decimal

router = APIRouter(prefix="/payments", tags=["Payments"])

# -----------------------------------------------------------
# NUEVA RUTA PARA REGISTRAR PAGO POR ADMINISTRADOR
# POST /payments/admin
# -----------------------------------------------------------
@router.post("/admin", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_admin(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Usa get_current_user (Admin/User)
):
    """
    Permite a un usuario administrador registrar un pago para cualquier préstamo.
    La lógica de aprobación y aplicación de pago es idéntica a la ruta de cliente,
    pero la autenticación se realiza con el token del administrador (User).
    """
    loan = db.query(Loan).filter(Loan.id == payment.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # Validación: Solo un administrador debería poder registrar pagos de esta manera.
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Se requiere rol de administrador.")
    
    # -----------------------------------------------------------
    # 1. PREPARACIÓN DE DATOS DEL PAGO
    # -----------------------------------------------------------
    new_payment_data = {
        "loan_id": payment.loan_id,
        "payment_date": payment.payment_date,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "created_by": current_user.id, # Creado por el usuario administrador
        "status": 'approved' # CAMBIO CLAVE: Asumimos la aprobación inmediata
    }

    if payment.schedule_id:
        # --- ESCENARIO 1: PAGO DE CUOTA ESPECÍFICA ---
        schedule = db.query(PaymentSchedule).filter(
            PaymentSchedule.id == payment.schedule_id
        ).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")
        
        if schedule.status == 'paid':
            raise HTTPException(status_code=400, detail="Esta cuota ya está pagada")
        
        # Validación del monto
        expected_amount = Decimal(str(schedule.total_amount)) - Decimal(str(schedule.paid_amount or 0))
        if abs(Decimal(str(payment.amount)) - expected_amount) > Decimal('0.01'):
            raise HTTPException(
                status_code=400, 
                detail=f"El monto debe ser S/ {expected_amount:.2f}"
            )
        
        # 1a. Actualizar datos del nuevo pago
        new_payment_data["schedule_id"] = payment.schedule_id
        new_payment_data["principal_paid"] = schedule.principal_amount
        new_payment_data["interest_paid"] = schedule.interest_amount
        
        # 1b. *** LÓGICA DE ACTUALIZACIÓN DE CUOTA (Cronograma) ***
        schedule.paid_amount = schedule.total_amount
        schedule.paid_principal = schedule.principal_amount
        schedule.paid_interest = schedule.interest_amount
        schedule.status = 'paid' # Marca la cuota como PAGADA

    else:
        # --- ESCENARIO 2: PAGO LIBRE / ADELANTO ---
        
        # 2a. *** LÓGICA DE APLICACIÓN DE PAGO EN ORDEN ***
        remaining_amount = Decimal(str(payment.amount))
        schedules = db.query(PaymentSchedule).filter(
            PaymentSchedule.loan_id == payment.loan_id,
            PaymentSchedule.status.in_(['pending', 'partial'])
        ).order_by(PaymentSchedule.installment_number).all()
        
        # Aplicar el pago a las cuotas en orden (tomado de approve_payment)
        for schedule in schedules:
            if remaining_amount <= 0:
                break
            
            outstanding = Decimal(str(schedule.total_amount)) - Decimal(str(schedule.paid_amount or 0))
            payment_to_apply = min(remaining_amount, outstanding)
            
            schedule.paid_amount = Decimal(str(schedule.paid_amount or 0)) + payment_to_apply
            
            # Recalcular el status de la cuota
            if schedule.paid_amount >= Decimal(str(schedule.total_amount)) - Decimal('0.01'):
                schedule.status = 'paid'
            elif schedule.paid_amount > Decimal('0.00'):
                schedule.status = 'partial'
            
            remaining_amount -= payment_to_apply
        
        # En pagos libres, principal/interest_paid se puede calcular
        # más detalladamente, pero por simplicidad de este fix,
        # lo dejamos en None si no se especifica cuota.
        
    # -----------------------------------------------------------
    # 2. REGISTRAR PAGO Y ACTUALIZAR SALDO DEL PRÉSTAMO
    # -----------------------------------------------------------
    new_payment = Payment(**new_payment_data)
    db.add(new_payment)

    # *** ACTUALIZACIÓN DEL PRÉSTAMO (Loan) ***
    loan.paid_amount = Decimal(str(loan.paid_amount or 0)) + Decimal(str(payment.amount))
    loan.outstanding_balance = Decimal(str(loan.total_amount)) - Decimal(str(loan.paid_amount))
    
    # Commit para guardar: new_payment, el/los schedules actualizados, y loan actualizado.
    db.commit() 
    db.refresh(new_payment)
    return new_payment


# -----------------------------------------------------------
# RUTA ORIGINAL DE PAGO DE CLIENTE (Mantenida)
# -----------------------------------------------------------
@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    loan = db.query(Loan).filter(Loan.id == payment.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # -----------------------------------------------------------
    # 1. PREPARACIÓN DE DATOS DEL PAGO
    # -----------------------------------------------------------
    new_payment_data = {
        "loan_id": payment.loan_id,
        "payment_date": payment.payment_date,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "created_by": current_customer.created_by,
        "status": 'approved' # CAMBIO CLAVE: Asumimos la aprobación inmediata
    }

    if payment.schedule_id:
        # --- ESCENARIO 1: PAGO DE CUOTA ESPECÍFICA ---
        schedule = db.query(PaymentSchedule).filter(
            PaymentSchedule.id == payment.schedule_id
        ).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")
        
        if schedule.status == 'paid':
            raise HTTPException(status_code=400, detail="Esta cuota ya está pagada")
        
        # Validación del monto
        expected_amount = Decimal(str(schedule.total_amount)) - Decimal(str(schedule.paid_amount or 0))
        if abs(Decimal(str(payment.amount)) - expected_amount) > Decimal('0.01'):
            raise HTTPException(
                status_code=400, 
                detail=f"El monto debe ser S/ {expected_amount:.2f}"
            )
        
        # 1a. Actualizar datos del nuevo pago
        new_payment_data["schedule_id"] = payment.schedule_id
        new_payment_data["principal_paid"] = schedule.principal_amount
        new_payment_data["interest_paid"] = schedule.interest_amount
        
        # 1b. *** LÓGICA DE ACTUALIZACIÓN DE CUOTA (Cronograma) ***
        schedule.paid_amount = schedule.total_amount
        schedule.paid_principal = schedule.principal_amount
        schedule.paid_interest = schedule.interest_amount
        schedule.status = 'paid' # Marca la cuota como PAGADA

    else:
        # --- ESCENARIO 2: PAGO LIBRE / ADELANTO ---
        
        # 2a. *** LÓGICA DE APLICACIÓN DE PAGO EN ORDEN ***
        remaining_amount = Decimal(str(payment.amount))
        schedules = db.query(PaymentSchedule).filter(
            PaymentSchedule.loan_id == payment.loan_id,
            PaymentSchedule.status.in_(['pending', 'partial'])
        ).order_by(PaymentSchedule.installment_number).all()
        
        # Aplicar el pago a las cuotas en orden (tomado de approve_payment)
        for schedule in schedules:
            if remaining_amount <= 0:
                break
            
            outstanding = Decimal(str(schedule.total_amount)) - Decimal(str(schedule.paid_amount or 0))
            payment_to_apply = min(remaining_amount, outstanding)
            
            schedule.paid_amount = Decimal(str(schedule.paid_amount or 0)) + payment_to_apply
            
            # Recalcular el status de la cuota
            if schedule.paid_amount >= Decimal(str(schedule.total_amount)) - Decimal('0.01'):
                schedule.status = 'paid'
            elif schedule.paid_amount > Decimal('0.00'):
                schedule.status = 'partial'
            
            remaining_amount -= payment_to_apply
        
        # En pagos libres, principal/interest_paid se puede calcular
        # más detalladamente, pero por simplicidad de este fix,
        # lo dejamos en None si no se especifica cuota.
        
    # -----------------------------------------------------------
    # 2. REGISTRAR PAGO Y ACTUALIZAR SALDO DEL PRÉSTAMO
    # -----------------------------------------------------------
    new_payment = Payment(**new_payment_data)
    db.add(new_payment)

    # *** ACTUALIZACIÓN DEL PRÉSTAMO (Loan) ***
    loan.paid_amount = Decimal(str(loan.paid_amount or 0)) + Decimal(str(payment.amount))
    loan.outstanding_balance = Decimal(str(loan.total_amount)) - Decimal(str(loan.paid_amount))
    
    # Commit para guardar: new_payment, el/los schedules actualizados, y loan actualizado.
    db.commit() 
    db.refresh(new_payment)
    return new_payment

# EL RESTO DE LAS FUNCIONES QUEDAN IGUALES
@router.put("/{payment_id}/approve", response_model=PaymentResponse)
def approve_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    if payment.status != 'pending':
        raise HTTPException(status_code=400, detail="El pago ya fue procesado")
    
    loan = db.query(Loan).filter(Loan.id == payment.loan_id).first()
    
    if payment.schedule_id:
        schedule = db.query(PaymentSchedule).filter(
            PaymentSchedule.id == payment.schedule_id
        ).first()
        
        if schedule:
            schedule.paid_amount = schedule.total_amount
            schedule.paid_principal = schedule.principal_amount
            schedule.paid_interest = schedule.interest_amount
            schedule.status = 'paid'
    else:
        remaining_amount = Decimal(str(payment.amount))
        schedules = db.query(PaymentSchedule).filter(
            PaymentSchedule.loan_id == payment.loan_id,
            PaymentSchedule.status.in_(['pending', 'partial'])
        ).order_by(PaymentSchedule.installment_number).all()
        
        for schedule in schedules:
            if remaining_amount <= 0:
                break
            
            outstanding = Decimal(str(schedule.total_amount)) - Decimal(str(schedule.paid_amount or 0))
            payment_to_apply = min(remaining_amount, outstanding)
            
            schedule.paid_amount = Decimal(str(schedule.paid_amount or 0)) + payment_to_apply
            if schedule.paid_amount >= Decimal(str(schedule.total_amount)) - Decimal('0.01'):
                schedule.status = 'paid'
            else:
                schedule.status = 'partial'
            
            remaining_amount -= payment_to_apply
    
    loan.paid_amount = Decimal(str(loan.paid_amount or 0)) + Decimal(str(payment.amount))
    loan.outstanding_balance = Decimal(str(loan.total_amount)) - Decimal(str(loan.paid_amount))
    
    payment.status = 'approved'
    
    db.commit()
    db.refresh(payment)
    return payment

@router.put("/{payment_id}/reject", response_model=PaymentResponse)
def reject_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    if payment.status != 'pending':
        raise HTTPException(status_code=400, detail="El pago ya fue procesado")
    
    payment.status = 'rejected'
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/loan/{loan_id}")
def get_payments_by_loan(
    loan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = db.query(Payment).filter(Payment.loan_id == loan_id).all()
    return payments

@router.get("/pending")
def get_pending_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = db.query(Payment).filter(Payment.status == 'pending').all()
    return payments