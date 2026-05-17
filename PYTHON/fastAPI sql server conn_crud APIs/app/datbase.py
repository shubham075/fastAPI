import urllib.parse
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("DB_SERVER", "localhost")
DATABASE = os.getenv("DB_NAME", "my_database")
USERNAME = os.getenv("DB_USER", "sa")
PASSWORD = os.getenv("DB_PASSWORD", "password")
DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

# proper formatted connection string for sql server...
params = urllib.parse.quote_plus(
    f"DRIVER = {DRIVER};"
    f"SERVER = {SERVER};"
    f"DATABASE = {DATABASE};"
    f"UID = {USERNAME};"
    f"PWD = {PASSWORD};"
    f"Trusted_Connection = yes;"
)

DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

# Engine setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#dependency to yeild DB sessions for requests...
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

