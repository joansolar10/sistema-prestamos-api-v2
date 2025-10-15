from sqlalchemy.orm import Session
from config.database import SessionLocal
from models.models import Customer
from utils.security import get_password_hash

db = SessionLocal()

# Buscar cliente por DNI o email
customer = db.query(Customer).filter(Customer.dni == "12345678").first()

if customer:
    customer.email = "juan@example.com"  # Asegúrate que tenga email
    customer.password_hash = get_password_hash("123456")
    db.commit()
    print(f"✅ Cliente actualizado: {customer.full_name} - {customer.email}")
else:
    print("❌ Cliente no encontrado")

db.close()