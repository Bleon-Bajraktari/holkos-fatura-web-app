"""
Aplikacioni kryesor - Holkos Fatura
"""
import customtkinter as ctk
from views.main_window import MainWindow
from models.database import Database
from models.company import Company
from models.template import Template
import sys

def check_database():
    """Kontrollon lidhjen me databazën dhe krijon tabelat nëse nevojitet"""
    db = Database()
    if not db.connect():
        print("Gabim: Nuk mund të lidhet me databazën MySQL!")
        print("Ju lutem:")
        print("1. Startoni MySQL në xampp")
        print("2. Krijoni databazën: CREATE DATABASE holkos_fatura;")
        print("3. Ekzekutoni skemën: mysql -u root holkos_fatura < sql/schema.sql")
        print("4. Kontrolloni konfigurimin në config/database.py")
        return False
    
    # Kontrollo nëse ka kompani
    company = Company(db)
    if not company.load():
        # Krijo kompani default
        company.name = "HOLKOS"
        company.address = "Kashice - Istog"
        company.phone = "044 224 031"
        company.email = "holkosmetal@yahoo.com"
        company.unique_number = "811226530"
        company.fiscal_number = "600610093"
        company.account_nib = "1706017400348068"
        company.save()
    
    # Kontrollo nëse ka shabllon default
    template = Template.get_default(db)
    if not template:
        template = Template(db)
        template.name = "Shablloni Default"
        template.description = "Shablloni bazë i faturave bazuar në dizajnin e HOLKOS"
        template.template_file = "default"
        template.is_active = True
        template.is_default = True
        template.save()
    
    db.disconnect()
    return True

import os

def main():
    """Funksioni kryesor"""
    try:
        # Kontrollo databazën
        if not check_database():
            print("\nShtypni nje buton per te vazhduar...")
            os.system("pause")
            sys.exit(1)
        
        # Krijo dhe shfaq dritaren kryesore
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"\n\nERROR KRITIK I PROGRAMIT:")
        print("="*30)
        import traceback
        traceback.print_exc()
        print("="*30)
        print("\nShtypni nje buton per te mbyllur kete dritare...")
        os.system("pause")

if __name__ == "__main__":
    main()

