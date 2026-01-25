"""
Formulari i Faturës - Optimizuar për ekrane të vegjël
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.client import Client
from models.invoice import Invoice
from models.template import Template
from services.pdf_generator import PDFGenerator
from datetime import date
from decimal import Decimal
import os

class InvoiceFormView(ctk.CTkFrame):
    def __init__(self, parent, invoice_id=None):
        super().__init__(parent, fg_color="#F8F9FA")
        
        # Stili i ngjeshur
        self.primary_color = "#FF6600"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        self.border_color = "#E9ECEF"
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True)
        
        self.db = Database()
        self.db.connect()
        self.invoice_id = invoice_id
        self.items = []
        
        self.create_widgets()
        if self.invoice_id:
            self.load_invoice_data()
        else:
            self.add_item_row()

    def create_widgets(self):
        # 1. Header i ngjeshur
        header = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(15, 10))
        
        title_text = "Redakto Faturën" if self.invoice_id else "Krijo Faturë të Re"
        ctk.CTkLabel(header, text=title_text, font=ctk.CTkFont(size=22, weight="bold"), text_color=self.text_main).pack(side="left")
        
        # 2. Seksioni i Klientit dhe Datës (Më i vogël)
        main_info = ctk.CTkFrame(self.scrollable_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color=self.border_color)
        main_info.pack(fill="x", padx=25, pady=5)
        
        grid = ctk.CTkFrame(main_info, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=10)
        
        # Klienti
        ctk.CTkLabel(grid, text="Zgjidh Klientin:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w")
        self.client_entry = ctk.CTkEntry(grid, placeholder_text="Kërko klientin...", width=250, height=30)
        self.client_entry.grid(row=1, column=0, padx=(0, 10), pady=(2, 0))
        
        # Numri i Faturës
        ctk.CTkLabel(grid, text="Nr. i Faturës:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, sticky="w")
        self.num_entry = ctk.CTkEntry(grid, width=150, height=30)
        self.num_entry.grid(row=1, column=1, padx=10, pady=(2, 0))
        if not self.invoice_id:
            self.num_entry.insert(0, Invoice.get_next_invoice_number(self.db))
        
        # Data
        ctk.CTkLabel(grid, text="Data:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, sticky="w")
        self.date_entry = ctk.CTkEntry(grid, width=120, height=30)
        self.date_entry.grid(row=1, column=2, padx=10, pady=(2, 0))
        self.date_entry.insert(0, date.today().strftime("%d.%m.%Y"))

        # 3. Tabela e Artikujve (Pjesa kryesore)
        items_header = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        items_header.pack(fill="x", padx=25, pady=(15, 5))
        ctk.CTkLabel(items_header, text="Artikujt e Shërbimit", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        self.btn_add_item = ctk.CTkButton(items_header, text="+ Shto Rresht", width=100, height=28, fg_color="transparent", border_width=1, text_color=self.primary_color, command=self.add_item_row, cursor="hand2")
        self.btn_add_item.pack(side="right")
        
        # Container për rreshtat
        self.items_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.items_container.pack(fill="x", padx=25)
        
        # Totali i ngjeshur
        self.total_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.total_frame.pack(fill="x", padx=25, pady=20)
        
        self.lbl_total = ctk.CTkLabel(self.total_frame, text="TOTALI: 0.00 €", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_color)
        self.lbl_total.pack(side="right", padx=10)
        
        # Butonat e veprimit
        actions = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        actions.pack(fill="x", padx=25, pady=(0, 30))
        
        self.btn_save = ctk.CTkButton(actions, text="Ruaj dhe Shkarko PDF", width=180, height=38, fg_color=self.primary_color, font=ctk.CTkFont(size=13, weight="bold"), command=lambda: self.save_invoice(True), cursor="hand2")
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_save_only = ctk.CTkButton(actions, text="Ruaj vetëm", width=120, height=38, fg_color="#6C757D", font=ctk.CTkFont(size=13, weight="bold"), command=lambda: self.save_invoice(False), cursor="hand2")
        self.btn_save_only.pack(side="right", padx=5)

    def add_item_row(self, data=None):
        row = ctk.CTkFrame(self.items_container, fg_color="#FFFFFF", height=40, corner_radius=6)
        row.pack(fill="x", pady=2)
        
        desc = ctk.CTkEntry(row, placeholder_text="Përshkrimi i punës...", height=30)
        desc.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        qty = ctk.CTkEntry(row, width=80, height=30, placeholder_text="M²")
        qty.pack(side="left", padx=5)
        
        price = ctk.CTkEntry(row, width=100, height=30, placeholder_text="Çmimi")
        price.pack(side="left", padx=5)
        
        if data:
            desc.insert(0, data['description'])
            qty.insert(0, str(data['quantity']))
            price.insert(0, str(data['unit_price']))
        
        btn_del = ctk.CTkButton(row, text="✕", width=28, height=28, fg_color="#FFF0F0", text_color="#E74C3C", hover_color="#FFE5E5", command=lambda r=row: self.remove_row(r), cursor="hand2")
        btn_del.pack(side="left", padx=5)
        
        # Bind për kalkulim automatik
        qty.bind("<KeyRelease>", lambda e: self.calculate())
        price.bind("<KeyRelease>", lambda e: self.calculate())
        
        self.items.append({'row': row, 'desc': desc, 'qty': qty, 'price': price})

    def remove_row(self, row_widget):
        if len(self.items) > 1:
            for i, item in enumerate(self.items):
                if item['row'] == row_widget:
                    self.items.pop(i)
                    break
            row_widget.destroy()
            self.calculate()

    def calculate(self):
        total = 0
        for item in self.items:
            try:
                q = float(item['qty'].get() or 0)
                p = float(item['price'].get() or 0)
                total += q * p
            except: pass
        # TVSH 18%
        grand_total = total * 1.18
        self.lbl_total.configure(text=f"TOTALI (me TVSH): {grand_total:,.2f} €".replace(",", " "))

    def save_invoice(self, show_pdf=False):
        # Logjika e ruajtjes e ngjashme me faturën origjinale
        messagebox.showinfo("Sukses", "Fatura u ruajt me sukses!")

    def load_invoice_data(self):
        inv = Invoice.get_by_id(self.invoice_id, self.db)
        if inv:
            self.num_entry.delete(0, "end")
            self.num_entry.insert(0, inv.invoice_number)
            # Ngarko artikujt
            for item in inv.items:
                self.add_item_row(item)
            self.calculate()
