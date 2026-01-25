"""
Minimal test to see exact error from database query
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

print("Testing database connection and query...")

try:
    db = SessionLocal()
    print("✓ Connection established")
    
    # Try the exact query that the endpoint uses
    invoices = db.query(models.Invoice).order_by(models.Invoice.date.desc()).all()
    print(f"✓ Query successful: {len(invoices)} invoices found")
    
    # Try to serialize first invoice
    if invoices:
        inv = invoices[0]
        print(f"\nFirst invoice details:")
        print(f"  ID: {inv.id}")
        print(f"  Number: {inv.invoice_number}")
        print(f"  Date: {inv.date}")
        print(f"  Client ID: {inv.client_id}")
        
        # Check if client relationship works
        try:
            client = inv.client
            if client:
                print(f"  Client: {client.name}")
            else:
                print(f"  ✗ Client is None (client_id={inv.client_id} not found)")
        except Exception as e:
            print(f"  ✗ Error accessing client: {e}")
        
        # Check items
        try:
            items = inv.items
            print(f"  Items: {len(items)}")
        except Exception as e:
            print(f"  ✗ Error accessing items: {e}")
    
    db.close()
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
