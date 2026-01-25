
import smtplib
import ssl
from models.database import Database
from models.company import Company
import sys

def test_connection():
    print("--- FILLIMI I TESTIT TE EMAILIT ---")
    
    # 1. Merr të dhënat nga databaza
    db = Database()
    if not db.connect():
        print("Gabim: Nuk mund të lidhet me databazën.")
        return

    company = Company(db)
    if not company.load():
        print("Gabim: Nuk u gjet kompania.")
        return
        
    print(f"Serveri: {company.smtp_server}")
    print(f"Porti: {company.smtp_port}")
    print(f"User: {company.smtp_user}")
    
    context = ssl.create_default_context()
    
    # TESTI 1: SSL (Port 465)
    print("\n[TEST 1] Duke provuar SSL në portin 465...")
    try:
        server = smtplib.SMTP_SSL(company.smtp_server, 465, context=context, timeout=20)
        server.set_debuglevel(1) # Shfaq detaje teknike
        print("Lidhja u vendos (Connected)!")
        
        print("Duke provuar login...")
        server.login(company.smtp_user, company.smtp_password)
        print("Login SUKSES!")
        server.quit()
        print("Testi 1 kaloi me sukses.")
        return
    except Exception as e:
        print(f"Dështoi Testi 1: {e}")

    # TESTI 2: TLS (Port 587)
    print("\n[TEST 2] Duke provuar TLS në portin 587...")
    try:
        server = smtplib.SMTP(company.smtp_server, 587, timeout=20)
        server.set_debuglevel(1)
        print("Lidhja u vendos. Duke dërguar EHLO...")
        server.ehlo()
        print("Duke aktivizuar STARTTLS...")
        server.starttls(context=context)
        print("STARTTLS aktiv!")
        server.ehlo()
        
        print("Duke provuar login...")
        server.login(company.smtp_user, company.smtp_password)
        print("Login SUKSES!")
        server.quit()
        print("Testi 2 kaloi me sukses.")
    except Exception as e:
        print(f"Dështoi Testi 2: {e}")

    print("\n--- FUND I TESTIT ---")
    print("Nëse të dyja dështuan me 'Connection unexpectedly closed', kontrolloni Antivirusin.")

if __name__ == "__main__":
    test_connection()
