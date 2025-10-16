from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

# --- Lista Explícita de Orígenes Permitidos (CORS) ---
ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "https://sistema-prestamos-frontend-v2.vercel.app", 
    "https://sistema-prestamos-frontend-v2.git.main.joans-projects-28cd9c24.vercel.app", 
    "https://sistema-prestamos-api-v2.onrender.com",
    "https://prestamos-api-6a81.onrender.com",
]

app = FastAPI(
    title="Sistema de Préstamos API",
    description="API REST para gestión de préstamos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API Sistema de Préstamos", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

from routes import auth, customers, loans, payments, customer_portal

# CORRECCIÓN: Eliminar el prefix="/api" de payments
# porque el router ya tiene prefix="/payments" en payments.py
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(loans.router)
app.include_router(payments.router)  # ← AQUÍ ESTÁ EL CAMBIO
app.include_router(customer_portal.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)