from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
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

# Importar routers
from routes import auth, customers, loans, payments, customer_portal

# ✅ NO agregues prefix aquí porque ya lo tienen en sus archivos
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(loans.router)
app.include_router(payments.router)
app.include_router(customer_portal.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)