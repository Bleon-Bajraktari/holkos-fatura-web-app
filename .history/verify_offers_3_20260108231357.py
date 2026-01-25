
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
    print("Verifikimi i Ofertës pa artikuj (Text Only)...")
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
    offer.subject = "OFERTË PËR PUNIME ALUMINI"
    offer.description = """
Përshkrimi i punimeve:

1. Furnizimi dhe montimi i dritareve, ngjyra Anthracite.
   Sasia totale: 100m2
   Cmimi total: 12,000 EUR

2. Dyer hyrese te sigurise se larte.
   Sasia: 2 cope

Kushtet e pageses:
- 50% paradhënie
- 50% pas përfundimit
    """
    
    # No items addded
    # offer.items is empty
    
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
