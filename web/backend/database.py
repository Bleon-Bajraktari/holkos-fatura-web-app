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
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    # Opsioni 1: DATABASE_URL i plotë (p.sh. nga TiDB Cloud Vercel integration)
    url = os.getenv("DATABASE_URL")
    if url:
        # Konverto mysql:// në mysql+pymysql:// për SQLAlchemy
        if url.startswith("mysql://") and "pymysql" not in url:
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        # PyMySQL nuk kupton sslaccept - heqe dhe përdor connect_args për SSL
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        qs.pop("sslaccept", None)  # heqe sslaccept
        qs.pop("ssl_mode", None)   # do përdorim connect_args
        new_query = urlencode(qs, doseq=True)
        url = urlunparse(parsed._replace(query=new_query))
        return url
    
    # Opsioni 2: Variabla të ndara (TIDB_HOST, TIDB_USER, etj.)
    host = os.getenv("TIDB_HOST") or os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("TIDB_PORT") or os.getenv("MYSQL_PORT", "4000" if host != "localhost" else "3306")
    user = os.getenv("TIDB_USER") or os.getenv("MYSQL_USER", "root")
    password = os.getenv("TIDB_PASSWORD") or os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("TIDB_DATABASE") or os.getenv("MYSQL_DATABASE", "test")
    
    # SSL: TiDB Cloud aktivizohet përmes connect_args, jo query params
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

DATABASE_URL = _get_database_url()

# TiDB Cloud Serverless kërkon SSL/TLS - ssl={} nuk aktivizon transport të sigurt
# Duhet ssl.SSLContext për TLS të vërtetë
_connect_args = {}
if "tidbcloud" in DATABASE_URL.lower():
    import ssl
    _connect_args = {"ssl": ssl.create_default_context()}

# Engine setup
engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args if _connect_args else {},
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
