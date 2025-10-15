from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sistema de Préstamos API",
    description="API REST para gestión de préstamos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://sistema-prestamos.vercel.app"],
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
app.include_router(payments.router)
app.include_router(customer_portal.router)