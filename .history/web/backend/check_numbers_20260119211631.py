from database import SessionLocal
import models
import re
from datetime import date

db = SessionLocal()
invoices = db.query(models.Invoice).all()

print(f"Total invoices: {len(invoices)}")

# Check years
years = {}
for i in invoices:
    y = i.date.year if hasattr(i.date, 'year') else None
    if y:
        years[y] = years.get(y, 0) + 1

print("Invoices per year:", years)

# Check last entries for 2026
invoices_2026 = [i for i in invoices if getattr(i.date, 'year', None) == 2026]
print(f"Invoices in 2026: {len(invoices_2026)}")

if invoices_2026:
    invoices_2026.sort(key=lambda x: x.id, reverse=True)
    print("Last 5 by ID (2026):")
    for i in invoices_2026[:5]:
        print(f"  ID: {i.id}, Num: {i.invoice_number}, Date: {i.date}")

    # Try to find max number
    nums = []
    for i in invoices_2026:
        m = re.findall(r'NR\.(\d+)', i.invoice_number.upper())
        if m:
            nums.append(int(m[0]))
    
    if nums:
        print(f"Max number in 2026: {max(nums)}")
    else:
        print("No numbers found in 2026 invoices")

db.close()
