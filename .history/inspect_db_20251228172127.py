from models.database import Database
import json
from decimal import Decimal
from datetime import date, datetime

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super(CustomEncoder, self).default(obj)

def inspect():
    db = Database()
    db.connect()
    
    invoices = db.execute_query("SELECT i.*, c.name as client_name FROM invoices i LEFT JOIN clients c ON i.client_id = c.id")
    clients = db.execute_query("SELECT * FROM clients")
    
    with open('inspect_db.log', 'w', encoding='utf-8') as f:
        f.write("--- INVOICES ---\n")
        f.write(json.dumps(invoices, indent=4, cls=CustomEncoder, ensure_ascii=False))
        f.write("\n\n--- CLIENTS ---\n")
        f.write(json.dumps(clients, indent=4, cls=CustomEncoder, ensure_ascii=False))

if __name__ == "__main__":
    inspect()
