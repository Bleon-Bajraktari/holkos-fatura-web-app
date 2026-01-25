"""
Test script to identify the exact 500 error
"""
import sys
import traceback
from fastapi.testclient import TestClient

sys.path.insert(0, 'c:\\xampp\\htdocs\\Holkos Fatura\\web\\backend')

try:
    from main import app
    client = TestClient(app)
    
    print("Testing GET /api/invoices...")
    response = client.get("/api/invoices")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
    else:
        data = response.json()
        print(f"Success! Got {len(data)} invoices")
        
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
