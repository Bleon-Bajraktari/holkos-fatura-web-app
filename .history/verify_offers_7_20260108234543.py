
import sys
import os
from decimal import Decimal
from datetime import date

sys.path.append(os.getcwd())

from models.database import Database
from models.offer import Offer
from models.client import Client
from services.pdf_generator import PDFGenerator

def verify():
    print("Verifikimi i Ofertës me Module Custom...")
    db = Database()
    db.connect()
    
    # Get client
    clients = Client.get_all(db)
    if not clients:
        print("No clients found.")
        return
    client_id = clients[0]['id']
    
    # Create Offer
    offer = Offer(db)
    offer.offer_number = Offer.get_next_offer_number(db)
    offer.date = date.today()
    offer.client_id = client_id
    offer.subject = "Oferte me Module Custom"
    
    # Item 1: Multiple modules (Qty, Price, Discount)
    custom_mods_1 = [
        {'value': '10', 'unit': 'm2'},
        {'value': '25.00', 'unit': '€/m2'},
        {'value': '0.90', 'unit': 'Koef.'}
    ]
    offer.add_item("Dritare PVC me Koeficient", "", 1, 225.00, custom_mods_1)

    # Item 2: Just one module (Total)
    custom_mods_2 = [
        {'value': '500.00', 'unit': '€ Total'}
    ]
    offer.add_item("Montimi i dyerve (Çmim Fix)", "", 1, 500.00, custom_mods_2)

    # Item 3: Empty modules, just text
    offer.add_item("Garancia 5 vite pa kosto shtese.", "", 0, 0, [])

    # Save
    if offer.save():
        print(f"Offer saved: {offer.offer_number}")
    else:
        print("Failed to save offer")
        return

    # Generate PDF
    try:
        gen = PDFGenerator()
        path = gen.generate_offer(offer)
        print(f"PDF Generated: {path}")
        os.startfile(path)
    except Exception as e:
        print(f"PDF Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
