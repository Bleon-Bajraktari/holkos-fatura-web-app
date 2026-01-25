
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
    print("Verifikimi i Ofertës me Blloqe (Header, Text, Item)...")
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
    offer.subject = "Oferte me Strukture Blloqesh"
    
    # Block 1: Header
    offer.add_item("PUNIMET E PËRFSHIRA", "", 0, 0, None, 'header')

    # Block 2: Info Text
    offer.add_item("- Lloji i gjamit: Guardian 8 + 8", "", 0, 0, None, 'text')

    # Block 3: Item with Custom Price display
    offer.add_item("Lloji i montimit: Me shin te plote poshte", "", 1, 190, [{'value': '190', 'unit': '€ m2'}], 'item')

    # Block 4: Another Item
    offer.add_item("Montimi i xhamit 8 + 8, ballkona francez", "", 1, 140, [{'value': '140', 'unit': '€ m2'}], 'item')

    # Block 5: Closing Text
    offer.add_item("*Ne oferte perfshihet edhe furnizimi dhe montimi komplet*", "", 0, 0, None, 'text')
    
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
