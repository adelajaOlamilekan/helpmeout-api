""" Database setup and connection """
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_PORT,
    DB_HOST,
    DB_NAME,
    DB_TYPE,
)

# Setup Database URL and Create Engine
if DB_TYPE == "mysql":
    DB_URL = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DB_URL)
else:
    DB_URL = f"sqlite:///./{DB_NAME}.db"
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

# Create all Tables
Base = declarative_base()

# Setup SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Connect db session
def get_db() -> SessionLocal:
    """
    Connects to the database and returns the session

    Yields:
        SessionLocal: The database session
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
