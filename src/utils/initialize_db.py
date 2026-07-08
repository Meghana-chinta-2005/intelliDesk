import logging
from sqlalchemy.orm import Session

from src.config.config import settings
from src.database import Base, engine, SessionLocal
# Import models to ensure they are registered with Base metadata
from src.models import db_models
from src.utils.auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_init")


def init_db():
    logger.info("Connecting to PostgreSQL and creating tables if they do not exist...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        return

    # Seed initial Admin User
    db: Session = SessionLocal()
    try:
        admin_user = db.query(db_models.User).filter(db_models.User.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not admin_user:
            logger.info("Seeding default admin user...")
            hashed_pw = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            admin_user = db_models.User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                hashed_password=hashed_pw,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Default admin user created. Username: {settings.DEFAULT_ADMIN_USERNAME}")
        else:
            logger.info("Admin user already exists in the database.")
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
