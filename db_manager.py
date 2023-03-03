import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# get data from environment
# db_port = os.environ.get('POSTGRES_PORT') or 5432
# db_host = os.environ.get('POSTGRES_HOST') or "127.0.0.1"
# db_name = os.environ.get('POSTGRES_DB') or "Library"
# db_user = os.environ.get('POSTGRES_USER') or "postgres"
# db_pass = os.environ.get('POSTGRES_PASSWORD') or "postgres"
db_port = 5432
db_host = "127.0.0.1"
db_name = "Library"
db_user = "postgres"
db_pass = "qwerlodaza"

SQLALCHEMY_DATABASE_URL = \
    f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
DeclarativeBase = declarative_base()

# create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db():
    """
    create tables if they don't exist
    """
    DeclarativeBase.metadata.create_all(engine)


def get_db():
    """
    :return: db session
    """
    return SessionLocal()