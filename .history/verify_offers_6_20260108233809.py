
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
    print("Verifikimi i Ofertës Aligned Rows (Desc | Calc)...")
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
    offer.subject = "Oferte Finale Aligned"
    
    # Needs explicit description logic adjustment
    # In this new flow, offer.items holds the description text for the row.
    
    # Row 1: Intro + some item
    offer.add_item("""
Furnizimi dhe montimi i dritareve PVC.
Profili 5 dhomësh, xham i dyfishtë.
Ngjyra e bardhë.
""", "cope", 10, 150.00)

    # Row 2: Just text (Qty=0)
    offer.add_item("""
Garancia për produktet është 10 vite.
Servisimi falas për vitin e parë.
""", "", 0, 0)

    # Row 3: Complex Item
    offer.add_item("""
Dera e hyrjes kryesore.
Modeli 'Avantgarde', me panel dekorativ.
Përfshin dorezë inoksi dhe bravë sigurie.
""", "cope", 1, 850.00)
    
    offer.description = "" # Not used anymore
    
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
