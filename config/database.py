from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback a sqlite si no hay DATABASE_URL (útil en desarrollo)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./dev.db"
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

print("DATABASE_URL used:", DATABASE_URL)

# create_engine con connect_args sólo para sqlite
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Si tus modelos están en otro módulo, impórtalos aquí antes de create_all
    # from models import User, Loan  # <- descomenta/ajusta según tu proyecto
    Base.metadata.create_all(bind=engine)