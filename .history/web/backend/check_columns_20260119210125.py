from database import engine
from sqlalchemy import text

with engine.connect() as con:
    for table in ['invoices', 'invoice_items', 'offers', 'offer_items']:
        print(f"\nTable: {table}")
        try:
            columns = con.execute(text(f"SHOW COLUMNS FROM {table}")).fetchall()
            for c in columns:
                print(f"  {c[0]}: {c[1]}")
        except Exception as e:
            print(f"  Error: {e}")
