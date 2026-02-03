import os
from sqlalchemy import create_engine, text
import models
from database import engine, Base

def _seed_auth_credentials(conn):
    """Seed app_login_username and app_login_password if missing."""
    from auth import hash_password
    username = os.getenv("APP_INITIAL_USERNAME", "admin")
    password = os.getenv("APP_INITIAL_PASSWORD", "holkos2025")
    pw_hash = hash_password(password)
    for key, val in [("app_login_username", username), ("app_login_password", pw_hash)]:
        existing = conn.execute(text("SELECT id FROM settings WHERE setting_key = :k"), {"k": key}).fetchone()
        if not existing:
            conn.execute(text("INSERT INTO settings (setting_key, setting_value) VALUES (:k, :v)"), {"k": key, "v": val})
            print(f"Seeded {key}.")

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
        
        # 3. Hiq indekset e vjeter qe kerkonin unike globale
        # Numrat e fatures jane unike per vit, jo globale (FATURA NR.1 2025 + FATURA NR.1 2026 OK)
        try:
            conn.execute(text("ALTER TABLE invoices DROP INDEX idx_unique_invoice_number"))
            print("Dropped idx_unique_invoice_number (allow per-year duplicates).")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE offers DROP INDEX idx_unique_offer_number"))
            print("Dropped idx_unique_offer_number.")
        except Exception:
            pass
            
        conn.commit()

    # 4. Seed auth credentials if missing
    with engine.connect() as conn:
        try:
            _seed_auth_credentials(conn)
            conn.commit()
        except Exception as ex:
            print("Auth seed skipped:", ex)
    
    print("Database schema update finished.")

if __name__ == "__main__":
    update_db()
