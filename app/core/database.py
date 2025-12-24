from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # evita conexiones muertas
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> str:
    # Prueba simple: SELECT 1
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        return str(result)
