from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/fastAPIwallet"
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dnd-currency-manager-db"

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
