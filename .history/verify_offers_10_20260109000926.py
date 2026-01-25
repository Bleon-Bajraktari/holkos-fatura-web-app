
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
    print("Verifikimi i Ofertës me Simbole Speciale (m², m³)...")
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
    offer.subject = "Oferte me Simbole m² dhe m³"
    
    # Item 1: m2 symbol
    offer.add_item("Dritare PVC kualitet i lartë", "", 1, 1000, [{'value': '1000', 'unit': '€ m²'}], 'item')

    # Item 2: Complex m3
    offer.add_item("Betonim i shkalleve", "", 1, 450, [{'value': '5', 'unit': 'm³'}, {'value': '90', 'unit': '€/m³'}], 'item')

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
