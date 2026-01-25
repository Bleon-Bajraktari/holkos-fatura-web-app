"""
Check if local database exists and has data
"""
from database import SessionLocal, LOCAL_DB_URL
import models

print(f"Trying to connect to: {LOCAL_DB_URL}")

try:
    db = SessionLocal()
    print("✓ Database connection successful")
    
    # Check tables
    invoice_count = db.query(models.Invoice).count()
    client_count = db.query(models.Client).count()
    
    print(f"✓ Invoices: {invoice_count}")
    print(f"✓ Clients: {client_count}")
    
    if invoice_count > 0:
        inv = db.query(models.Invoice).first()
        print(f"✓ Sample invoice: {inv.invoice_number}")
    
    db.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
