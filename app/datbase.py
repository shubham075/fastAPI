import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_NAME")
USERNAME = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DRIVER = os.getenv("DB_DRIVER")

if not SERVER or not DATABASE or not DRIVER:
    missing = [name for name, value in (("DB_SERVER", SERVER), ("DB_NAME", DATABASE), ("DB_DRIVER", DRIVER)) if not value]
    raise RuntimeError(f"Missing database environment variables: {', '.join(missing)}")

conn_parts = [
    f"DRIVER={DRIVER}",
    f"SERVER={SERVER}",
    f"DATABASE={DATABASE}",
]

if PASSWORD:
    if not USERNAME:
        raise RuntimeError("DB_USER is required when DB_PASSWORD is set")
    conn_parts.extend([f"UID={USERNAME}", f"PWD={PASSWORD}"])
else:
    conn_parts.append("Trusted_Connection=yes")

params = urllib.parse.quote_plus(";".join(conn_parts))
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

# Engine setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# dependency to yield DB sessions for requests...
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

