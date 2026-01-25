from database import SessionLocal
import models
from datetime import date
from sqlalchemy import text

db = SessionLocal()
try:
    print("Test 1: Minimal save")
    client = db.query(models.Client).first()
    db_invoice = models.Invoice(
        invoice_number="MIN-001",
        date=date.today(),
        client_id=client.id if client else 1
    )
    db.add(db_invoice)
    db.commit()
    print("Minimal save success!")
    
    print("Test 2: Adding status")
    db_invoice.status = "draft"
    db.commit()
    print("Status update success!")
    
    print("Test 3: Adding decimals")
    from decimal import Decimal
    db_invoice.subtotal = Decimal("100.00")
    db_invoice.vat_amount = Decimal("18.00")
    db_invoice.total = Decimal("118.00")
    db.commit()
    print("Decimals update success!")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
