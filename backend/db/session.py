from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import get_settings

settings = get_settings()

engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True
}

# pooled connection for neon (serverless-friendly) or local postgres
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """fastapi dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
