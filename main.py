from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Lista Explícita de Orígenes Permitidos (CORS) ---
# Hemos incluido todas las posibles URLs de Vercel y locales.
ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "https://sistema-prestamos-frontend-v2.vercel.app", 
    "https://sistema-prestamos-frontend-v2.git.main.joans-projects-28cd9c24.vercel.app", 
    "https://sistema-prestamos-api-v2.onrender.com",
]

app = FastAPI(
    title="Sistema de Préstamos API",
    description="API REST para gestión de préstamos",
    version="1.0.0"
)

# APLICACIÓN DE MIDDLEWARE CORS
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
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(loans.router)
app.include_router(payments.router, prefix="/api")
app.include_router(customer_portal.router)