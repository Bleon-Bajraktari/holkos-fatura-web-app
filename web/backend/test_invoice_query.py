import sys
sys.path.insert(0, 'c:\\xampp\\htdocs\\Holkos Fatura\\web\\backend')

from main import app
from database import SessionLocal
import models

try:
    # Test getting all invoices
    db = SessionLocal()
    invoices = db.query(models.Invoice).all()
    print(f"✓ Query successful: {len(invoices)} invoices")
    
    # Try to serialize first invoice
    if invoices:
        inv = invoices[0]
        print(f"\nFirst invoice:")
        print(f"  ID: {inv.id}")
        print(f"  Number: {inv.invoice_number}")
        print(f"  Date: {inv.date}")
        print(f"  Client ID: {inv.client_id}")
        
        # Try to access client
        try:
            client = inv.client
            print(f"  Client: {client.name if client else 'None'}")
        except Exception as e:
            print(f"  ✗ Client error: {e}")
        
        # Try to access items
        try:
            items = inv.items
            print(f"  Items: {len(items)}")
        except Exception as e:
            print(f"  ✗ Items error: {e}")
    
    db.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
