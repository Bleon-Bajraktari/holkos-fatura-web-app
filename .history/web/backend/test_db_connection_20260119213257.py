from database import SessionLocal
import models
from datetime import date

try:
    db = SessionLocal()
    print("✓ Database connection successful")
    
    # Test query
    count = db.query(models.Invoice).count()
    print(f"✓ Total invoices: {count}")
    
    # Test getting invoices for 2026
    invoices_2026 = db.query(models.Invoice).filter(
        models.Invoice.date >= date(2026, 1, 1)
    ).all()
    print(f"✓ Invoices in 2026: {len(invoices_2026)}")
    
    # Test the problematic query with extract
    from sqlalchemy import extract
    test_query = db.query(models.Invoice).filter(
        extract('year', models.Invoice.date) == 2026
    ).all()
    print(f"✓ Extract query works: {len(test_query)} invoices")
    
    db.close()
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
