"""
Direct test of the problematic endpoint
"""
import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
import schemas

try:
    db = SessionLocal()
    
    # Get invoices
    invoices = db.query(models.Invoice).order_by(models.Invoice.date.desc()).limit(5).all()
    
    print(f"✓ Found {len(invoices)} invoices")
    
    # Try to serialize them
    for inv in invoices:
        try:
            # This is what Pydantic does
            invoice_dict = {
                'id': inv.id,
                'invoice_number': inv.invoice_number,
                'date': inv.date,
                'payment_due_date': inv.payment_due_date,
                'client_id': inv.client_id,
                'template_id': inv.template_id,
                'subtotal': inv.subtotal,
                'vat_percentage': inv.vat_percentage,
                'vat_amount': inv.vat_amount,
                'total': inv.total,
                'status': inv.status,
                'created_at': inv.created_at,
                'updated_at': inv.updated_at,
                'items': inv.items,
                'client': inv.client
            }
            print(f"  ✓ Invoice {inv.id} serialized OK")
        except Exception as e:
            print(f"  ✗ Invoice {inv.id} failed: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
