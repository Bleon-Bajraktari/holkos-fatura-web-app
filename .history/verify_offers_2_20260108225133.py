
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
    print("Verifikimi i Ofertës me Subject...")
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
    offer.subject = "MONTIM XHAMI + PIKORET ALUMINI" # Test subject
    offer.description = "*Ne oferte perfshihet edhe furnizimi dhe montimi komplet*"
    
    # Add items
    offer.add_item("Lloji i xhamit: Guardian 8 + 8", "cope", 0, 0) # Info only
    offer.add_item("Me shin te plote poshte", "m2", 100, 190.00)
    offer.add_item("Me cunga + me kapak", "m2", 50, 200.00)
    
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
    except Exception as e:
        print(f"PDF Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
