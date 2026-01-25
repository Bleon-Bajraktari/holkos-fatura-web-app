from backend.database import SessionLocal
from backend import models, schemas
from decimal import Decimal
from datetime import date

db = SessionLocal()
try:
    invoice_data = {
        "invoice_number": "FATURA NR.1",
        "date": date.today(),
        "payment_due_date": None,
        "client_id": 1,
        "items": [
            {
                "description": "Test",
                "quantity": Decimal("1"),
                "unit_price": Decimal("100"),
                "subtotal": Decimal("100"),
                "unit": "Copa"
            }
        ],
        "subtotal": Decimal("100"),
        "vat_percentage": Decimal("18"),
        "vat_amount": Decimal("18"),
        "total": Decimal("118"),
        "status": "draft"
    }
    
    invoice = schemas.InvoiceCreate(**invoice_data)
    db_invoice = models.Invoice(**invoice.dict(exclude={'items'}))
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    for item in invoice.items:
        db_item = models.InvoiceItem(**item.dict(), invoice_id=db_invoice.id)
        db.add(db_item)
    
    db.commit()
    print("Save successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
