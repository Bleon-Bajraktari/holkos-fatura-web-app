import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# Load existing config logic
# We can either import it or replicate for simplicity since it's a new environment
# Given the TiDB Cloud setup, we'll replicate or use environment variables

# Database configurations
# Cloud (TiDB)
CLOUD_DB_URL = "mysql+pymysql://23pY2336LXLw5MR.root:oFv0JzSZ1dk8olqt@gateway01.eu-central-1.prod.aws.tidbcloud.com:4000/test"

# Local
LOCAL_DB_URL = "mysql+pymysql://root:@localhost:3306/holkos_fatura1"

# Engine setup
engine = create_engine(
    CLOUD_DB_URL, 
    connect_args={"ssl": {"ssl": {}}},
    pool_pre_ping=True
)

# For cloud we might need SSL context if port is 4000
# engine_cloud = create_engine(CLOUD_DB_URL, connect_args={"ssl": {"ssl": {}}})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
