import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.config import settings

logger = logging.getLogger(__name__)

# Connection engine
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # checks connection health before utilizing it
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.critical(f"Failed to create SQLAlchemy engine with URL: {settings.DATABASE_URL}. Error: {e}")
    raise

Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session scope management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
