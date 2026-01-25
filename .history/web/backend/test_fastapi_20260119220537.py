"""
Test FastAPI endpoint directly to see the exact error
"""
import sys
sys.path.insert(0, 'c:\\xampp\\htdocs\\Holkos Fatura\\web\\backend')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("Testing GET /invoices endpoint...")

try:
    response = client.get("/invoices")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Got {len(data)} invoices")
        if data:
            print(f"First invoice: {data[0].get('invoice_number')}")
    else:
        print(f"✗ Error Response:")
        print(response.text)
        
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()
