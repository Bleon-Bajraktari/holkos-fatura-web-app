import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# Ngarko konfigurimin nga environment variables
# Për Vercel + TiDB Cloud: përdor TIDB_HOST, TIDB_PORT, etj. ose DATABASE_URL
# Për zhvillim lokal: përdor .env ose variabla default

def _get_database_url():
    """Merr URL-in e databazës nga environment variables."""
    # Opsioni 1: DATABASE_URL i plotë (p.sh. nga TiDB Cloud Vercel integration)
    url = os.getenv("DATABASE_URL")
    if url:
        # Konverto mysql:// në mysql+pymysql:// për SQLAlchemy
        if url.startswith("mysql://") and "pymysql" not in url:
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        return url
    
    # Opsioni 2: Variabla të ndara (TIDB_HOST, TIDB_USER, etj.)
    host = os.getenv("TIDB_HOST") or os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("TIDB_PORT") or os.getenv("MYSQL_PORT", "4000" if host != "localhost" else "3306")
    user = os.getenv("TIDB_USER") or os.getenv("MYSQL_USER", "root")
    password = os.getenv("TIDB_PASSWORD") or os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("TIDB_DATABASE") or os.getenv("MYSQL_DATABASE", "test")
    
    # TiDB Cloud kërkon SSL
    ssl_param = "?ssl_mode=REQUIRED" if "tidbcloud" in host.lower() else ""
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}{ssl_param}"

DATABASE_URL = _get_database_url()

# Engine setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,  # TiDB Starter fiket pas 5 min - reconnect për shmangje gabimesh
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
