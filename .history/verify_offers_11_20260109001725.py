
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
    print("Verifikimi i Ofertës me Rreshta Kompaktë (1000€ m²)...")
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
    offer.subject = "Oferte me Rreshta Kompaktë"
    
    # Scenario 1: Description + Price/Unit Suffix
    # Using two modules: [1000, "€"] and ["", "m²"]
    mods = [
        {'value': '1000', 'unit': '€'},
        {'value': '', 'unit': 'm²'}
    ]
    offer.add_item("Lloji i montimit: Me shin te plote poshte", "", 1, 1000, mods, 'item')

    # Scenario 2: Calculation
    mods2 = [
        {'value': '10', 'unit': 'm²'},
        {'value': '15', 'unit': '€'}
    ]
    offer.add_item("Dera e jashtme - llogaritja", "", 1, 150, mods2, 'item')

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
