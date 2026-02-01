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
        try:
            rows = conn.execute(text("SHOW COLUMNS FROM invoices")).fetchall()
        except Exception:
            rows = []
        columns = [row[0] for row in rows] if rows else []
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
        
        if "save_timestamp" not in columns:
            print("Adding 'save_timestamp' to invoices...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN save_timestamp DATETIME NULL"))
        
        # Invoice Items table
        try:
            rows = conn.execute(text("SHOW COLUMNS FROM invoice_items")).fetchall()
        except Exception:
            rows = []
        columns = [row[0] for row in rows] if rows else []
        if "unit" not in columns:
            print("Adding 'unit' to invoice_items...")
            conn.execute(text("ALTER TABLE invoice_items ADD COLUMN unit VARCHAR(50)"))
        elif columns:
            conn.execute(text("ALTER TABLE invoice_items MODIFY COLUMN unit VARCHAR(50)"))

        # Offers and OfferItems - Standard check (skip if table missing)
        try:
            rows = conn.execute(text("SHOW COLUMNS FROM offer_items")).fetchall()
            columns = [row[0] for row in rows]
            if "unit" not in columns:
                print("Adding 'unit' to offer_items...")
                conn.execute(text("ALTER TABLE offer_items ADD COLUMN unit VARCHAR(50)"))
            else:
                conn.execute(text("ALTER TABLE offer_items MODIFY COLUMN unit VARCHAR(50)"))
            if "order_index" not in columns:
                print("Adding 'order_index' to offer_items...")
                conn.execute(text("ALTER TABLE offer_items ADD COLUMN order_index INT DEFAULT 0"))
        except Exception as ex:
            print("offer_items check skipped:", ex)

        # Offer table check
        try:
            rows = conn.execute(text("SHOW COLUMNS FROM offers")).fetchall()
            columns = [row[0] for row in rows]
            if "save_timestamp" not in columns:
                print("Adding 'save_timestamp' to offers...")
                conn.execute(text("ALTER TABLE offers ADD COLUMN save_timestamp DATETIME NULL"))
        except Exception as ex:
            print("offers check skipped:", ex)

        # Offers and OfferItems should have been created by create_all if они missing.
        
        # 3. Add Unique Constraints
        try:
            conn.execute(text("CREATE UNIQUE INDEX idx_unique_invoice_number ON invoices (invoice_number)"))
            print("Added unique index to invoice_number.")
        except:
            pass # Index probably already exists
            
        try:
            conn.execute(text("CREATE UNIQUE INDEX idx_unique_offer_number ON offers (offer_number)"))
            print("Added unique index to offer_number.")
        except:
            pass
            
        conn.commit()
    
    print("Database schema update finished.")

if __name__ == "__main__":
    update_db()
