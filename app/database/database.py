from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()


SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# SQLALCHEMY_DATABASE_URL = ("postgresql://" + os.getenv("POSTGRES_USER") + ":"
#                            + os.getenv("POSTGRES_PASSWORD") + "@db:5432/"
#                            + os.getenv("POSTGRES_DB"))
# local DB
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/fastAPIwallet"

# docker db
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"


# supabase db
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:qK6jusID5tarUzg9@db.apdtlbxlcjdkimvoqqse.supabase.co:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
