"""
Quick check if endpoint works now
"""
import requests

try:
    response = requests.get("http://localhost:8000/invoices")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Got {len(data)} invoices")
        if data:
            print(f"First invoice: {data[0].get('invoice_number')}")
    else:
        print(f"✗ Error:")
        print(response.text[:500])
        
except Exception as e:
    print(f"✗ Exception: {e}")
