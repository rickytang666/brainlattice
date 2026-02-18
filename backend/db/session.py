from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import get_settings

settings = get_settings()

# use pooled connection for neon
engine = create_engine(
    settings.DATABASE_URL,
    # pooling settings for serverless
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """dependency for fastapi endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
