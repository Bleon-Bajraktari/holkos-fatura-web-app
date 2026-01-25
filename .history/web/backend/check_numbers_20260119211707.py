from database import SessionLocal
import models
import re
from datetime import date

db = SessionLocal()
invoices = db.query(models.Invoice).all()

print(f"Total invoices in DB: {len(invoices)}")

# Check years
years = {}
for i in invoices:
    y = i.date.year if hasattr(i.date, 'year') else None
    if y:
        years[y] = years.get(y, 0) + 1

print("Invoices per year:", years)

for y in sorted(years.keys()):
    inv_y = [i for i in invoices if getattr(i.date, 'year', None) == y]
    nums = []
    for i in inv_y:
        m = re.findall(r'NR\.(\d+)', i.invoice_number.upper())
        if m:
            nums.append(int(m[0]))
    
    if nums:
        print(f"Year {y}: Count={len(inv_y)}, Max number={max(nums)}")
    else:
        print(f"Year {y}: Count={len(inv_y)}, No numbers found")

db.close()
