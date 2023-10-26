from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# local DB
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/fastAPIwallet"
# docker db
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"
# render db
# SQLALCHEMY_DATABASE_URL = "postgresql://ivan:PmEwjE0BjPvhoKV4gNs5n2fow3Z0tC6Z@dpg-cktb1po168ec73cc37dg-a.oregon-postgres.render.com/db_n2jp"
# supabase db
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:qK6jusID5tarUzg9@db.apdtlbxlcjdkimvoqqse.supabase.co:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
