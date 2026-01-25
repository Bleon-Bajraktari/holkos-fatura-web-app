from sqlalchemy import create_engine, inspect
import models

# Replicate connection logic from database.py
LOCAL_DB_URL = "mysql+pymysql://root:@localhost:3306/holkos_fatura1"
engine = create_engine(LOCAL_DB_URL)
inspector = inspect(engine)

def check_db():
    tables = inspector.get_table_names()
    print(f"Tables in DB: {tables}")
    
    needed_tables = ["companies", "clients", "invoices", "invoice_items", "offers", "offer_items"]
    for table in needed_tables:
        if table not in tables:
            print(f"!!! MISSING TABLE: {table}")
        else:
            columns = [c['name'] for c in inspector.get_columns(table)]
            print(f"Columns in {table}: {columns}")
            
            # Check for specific new columns
            if table == "invoices":
                for col in ["created_at", "status"]:
                    if col not in columns: print(f"!!! MISSING COLUMN in {table}: {col}")
            if table == "offers":
                for col in ["created_at"]:
                    if col not in columns: print(f"!!! MISSING COLUMN in {table}: {col}")

if __name__ == "__main__":
    check_db()
