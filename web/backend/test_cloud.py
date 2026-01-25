from sqlalchemy import create_engine, text
import pymysql

CLOUD_DB_URL = "mysql+pymysql://23pY2336LXLw5MR.root:oFv0JzSZ1dk8olqt@gateway01.eu-central-1.prod.aws.tidbcloud.com:4000/test"

try:
    engine = create_engine(CLOUD_DB_URL, connect_args={"ssl": {"ssl": {}}})
    with engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM invoices")).scalar()
        print(f"Connection successful! Total invoices in CLOUD: {res}")
        
        # Check last invoice in cloud
        last = conn.execute(text("SELECT id, invoice_number, date FROM invoices ORDER BY id DESC LIMIT 1")).fetchone()
        if last:
            print(f"Last invoice in cloud: ID={last[0]}, Num={last[1]}, Date={last[2]}")
except Exception as e:
    print(f"Connection failed: {e}")
