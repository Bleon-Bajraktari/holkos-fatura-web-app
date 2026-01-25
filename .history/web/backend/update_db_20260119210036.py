from sqlalchemy import create_engine, text
import models
from database import engine, Base

def update_db():
    print("Starting database schema update...")
    
    # 1. Create missing tables
    Base.metadata.create_all(bind=engine)
    print("Tables check/creation complete.")
    
    # 2. Add missing columns to existing tables
    with engine.connect() as conn:
        # Invoices table
        rows = conn.execute(text("SHOW COLUMNS FROM invoices")).fetchall()
        columns = [row[0] for row in rows] # row[0] is 'Field' in SHOW COLUMNS
        if "created_at" not in columns:
            print("Adding 'created_at' to invoices...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
        if "status" not in columns:
            print("Adding 'status' to invoices...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN status VARCHAR(20) DEFAULT 'draft'"))
        else:
            # Change existing status to VARCHAR(20) to avoid ENUM issues
            print("Ensuring 'status' is VARCHAR(20)...")
            conn.execute(text("ALTER TABLE invoices MODIFY COLUMN status VARCHAR(20) DEFAULT 'draft'"))
        
        # Invoice Items table
        rows = conn.execute(text("SHOW COLUMNS FROM invoice_items")).fetchall()
        columns = [row[0] for row in rows]
        if "unit" not in columns:
            # Although 'unit' is not in models.InvoiceItem yet (it was only in frontend?), 
            # let's check if we need it. Our model doesn't have it.
            pass

        # Offers and OfferItems should have been created by create_all if они missing.
        
        conn.commit()
    
    print("Database schema update finished.")

if __name__ == "__main__":
    update_db()
