from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from config.database import get_db
from models.models import User, Customer
from schemas.schemas import Token
from utils.security import verify_password, create_access_token
from schemas.schemas import CustomerRegister
from utils.security import verify_password, create_access_token, get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"Login attempt with email: {form_data.username}")  # DEBUG
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        print(f"User not found: {form_data.username}")  # DEBUG
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User found: {user.email}, checking password...")  # DEBUG
    
    if not verify_password(form_data.password, user.password_hash):
        print("Password verification failed")  # DEBUG
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    access_token = create_access_token(data={"sub": user.email, "role": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

print("router:", 'router' in dir())
print("router value:", router)

@router.post("/customer/login", response_model=Token)
def customer_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"Customer login attempt with email: {form_data.username}")  # DEBUG
    
    customer = db.query(Customer).filter(Customer.email == form_data.username).first()
    
    if not customer:
        print(f"Customer not found: {form_data.username}")  # DEBUG
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"Customer found: {customer.email}")  # DEBUG
    print(f"Has password_hash: {customer.password_hash is not None}")  # DEBUG
    
    if not customer.password_hash:
        print("Customer has no password_hash")  # DEBUG
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("Verifying password...")  # DEBUG
    
    if not verify_password(form_data.password, customer.password_hash):
        print("Password verification failed")  # DEBUG
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("Password verified successfully")  # DEBUG
    
    if not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente inactivo"
        )
    
    access_token = create_access_token(data={"sub": customer.email, "role": "customer", "customer_id": str(customer.id)})
    print("Token created successfully")  # DEBUG
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
def register_customer(customer_data: CustomerRegister, db: Session = Depends(get_db)):
    # Buscar por DNI primero
    existing_dni = db.query(Customer).filter(Customer.dni == customer_data.dni).first()
    existing_email = db.query(Customer).filter(Customer.email == customer_data.email).first()
    
    # Si existe por DNI y no tiene contraseña, actualizar
    if existing_dni and not existing_dni.password_hash:
        existing_dni.password_hash = get_password_hash(customer_data.password)
        existing_dni.email = customer_data.email
        existing_dni.phone = customer_data.phone or existing_dni.phone
        db.commit()
        db.refresh(existing_dni)
        access_token = create_access_token(data={"sub": existing_dni.email, "role": "customer", "customer_id": str(existing_dni.id)})
        return {"access_token": access_token, "token_type": "bearer"}
    
    # Si existe con contraseña
    if existing_dni and existing_dni.password_hash:
        raise HTTPException(status_code=400, detail="DNI ya registrado. Inicia sesión en su lugar.")
    
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Crear nuevo
    new_customer = Customer(
        dni=customer_data.dni,
        full_name=customer_data.full_name,
        email=customer_data.email,
        phone=customer_data.phone,
        password_hash=get_password_hash(customer_data.password),
        is_active=True
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    access_token = create_access_token(data={"sub": new_customer.email, "role": "customer", "customer_id": str(new_customer.id)})
    return {"access_token": access_token, "token_type": "bearer"}