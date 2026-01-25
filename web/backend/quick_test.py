"""
Simple test to check what's wrong with /api/invoices endpoint
"""
from database import SessionLocal
import models

try:
    db = SessionLocal()
    
    # Get one invoice
    invoice = db.query(models.Invoice).first()
    
    if invoice:
        print(f"✓ Got invoice ID: {invoice.id}")
        print(f"  Number: {invoice.invoice_number}")
        print(f"  Date: {invoice.date}")
        print(f"  Client ID: {invoice.client_id}")
        
        # Try to access client
        if invoice.client:
            print(f"  Client Name: {invoice.client.name}")
        else:
            print(f"  ✗ No client found for client_id={invoice.client_id}")
        
        # Try to access items
        print(f"  Items count: {len(invoice.items)}")
        
    else:
        print("No invoices found")
    
    db.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
