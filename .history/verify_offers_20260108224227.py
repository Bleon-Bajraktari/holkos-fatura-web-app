
import sys
import os
from decimal import Decimal
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from models.database import Database
from models.offer import Offer
from models.client import Client
from services.pdf_generator import PDFGenerator

def verify_offers():
    print("Fillimi i verifikimit te Ofertave...")
    
    db = Database()
    db.connect()
    
    # 1. Merr ose krijo nje klient testues
    clients = Client.get_all(db)
    if not clients:
        print("Creating test client...")
        client = Client(db)
        client.name = "Test Client"
        client.unique_number = "123456789"
        client.save()
        client_id = client.id
    else:
        client_id = clients[0]['id']
        print(f"Using client ID: {client_id}")

    # 2. Krijo Ofertën
    print("Creating Offer object...")
    offer = Offer(db)
    offer.offer_number = Offer.get_next_offer_number(db)
    offer.date = date.today()
    offer.client_id = client_id
    offer.description = "Kjo eshte nje oferte testuese.\nMe disa rreshta pershkrimi.\n\nTe dhenat jane fleksibile."
    
    # Shto artikuj
    offer.add_item("Fasada Ventiluese", "m2", 100, 45.50)
    offer.add_item("Skele", "m2", 200, 2.50)
    offer.add_item("Transport", "rruge", 1, 50.00)
    
    # 3. Ruaj ne DB
    print("Saving to database...")
    if offer.save():
        print(f"Offer saved with ID: {offer.id}")
    else:
        print("Failed to save offer!")
        return

    # 4. Gjenero PDF
    print("Generating PDF...")
    try:
        generator = PDFGenerator()
        output_path = generator.generate_offer(offer)
        print(f"PDF generated at: {output_path}")
        
        if os.path.exists(output_path):
            print("SUCCESS: PDF file exists!")
            # Update offer path
            offer.pdf_path = output_path
            offer.save()
        else:
            print("FAILURE: PDF file returned path but file not found?")
            
    except Exception as e:
        print(f"FAILURE: PDF Generation failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_offers()
