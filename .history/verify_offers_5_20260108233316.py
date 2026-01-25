
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
    print("Verifikimi i Ofertës Split Layout (Left Text / Right Items)...")
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
    offer.subject = "Oferte per Zyre"
    offer.description = """
Përshkrimi teknik i punimeve:

Ne ofrojmë zgjidhje të plota për dritaret dhe dyert e zyrës suaj.
Profili i përdorur është ALUMIL S560 me ndërprerje termike.
Xhami është 4 stinësh, 6mm + 16mm + 4mm.

Ngjyra: E zezë mat (RAL 9005).
Garancia: 10 vite për profilin, 5 vite për mekanizmat.

Koha e realizimit: 3 javë nga data e konfirmimit.

Këtu mund të shkruani tekst sa të doni dhe ai do të rri në anën e majtë të fletës, ndërsa kalkulimet do të rrinë në të djathtë.
"""
    # Add items (Right side modules)
    offer.add_item("Dritare 120x140", "cope", 5, 250.00)
    offer.add_item("Dera ballkoni 220x90", "cope", 2, 400.00)
    offer.add_item("Grila të jashtme", "m2", 10, 80.00)
    
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
