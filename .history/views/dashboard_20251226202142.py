"""
Dashboard view
"""
import customtkinter as ctk
from models.database import Database
from models.invoice import Invoice
from models.client import Client
from datetime import datetime, timedelta

class DashboardView(ctk.CTkFrame):
    """Dashboard me statistika dhe fatura të fundit"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.db = Database()
        self.db.connect()
        
        self.create_widgets()
        self.load_statistics()
    
    def create_widgets(self):
        """Krijon widget-et e dashboard-it"""
        # Titulli
        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Frame për statistikat
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Statistikat
        self.stats_labels = {}
        stats = [
            ("Total Fatura", "total_invoices"),
            ("Fatura këtë muaj", "month_invoices"),
            ("Totali i ardhurave", "total_revenue"),
            ("TVSH total", "total_vat")
        ]
        
        for i, (label_text, key) in enumerate(stats):
            frame = ctk.CTkFrame(stats_frame)
            frame.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
            stats_frame.grid_columnconfigure(i%2, weight=1)
            
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=ctk.CTkFont(size=14)
            )
            label.pack(pady=5)
            
            value_label = ctk.CTkLabel(
                frame,
                text="0",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#FF6600"
            )
            value_label.pack(pady=5)
            
            self.stats_labels[key] = value_label
        
        # Faturat e fundit
        recent_label = ctk.CTkLabel(
            self,
            text="Faturat e fundit",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        recent_label.pack(pady=(10, 10))
        
        # Tabela e faturave të fundit (me scroll vetëm nëse nevojitet)
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.recent_table_frame = ctk.CTkFrame(table_container)
        self.recent_table_frame.pack(fill="both", expand=True)
        
        # Header
        headers = ["Numri", "Data", "Klienti", "Totali", "Statusi"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.recent_table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            self.recent_table_frame.grid_columnconfigure(i, weight=1)
    
    def load_statistics(self):
        """Ngarkon statistikat"""
        try:
            # Total fatura
            all_invoices = Invoice.get_all(self.db)
            total_invoices = len(all_invoices)
            
            # Fatura këtë muaj
            first_day = datetime.now().replace(day=1).date()
            month_invoices = [inv for inv in all_invoices if inv['date'] >= first_day]
            month_count = len(month_invoices)
            
            # Totali i ardhurave
            total_revenue = sum(float(inv['total']) for inv in all_invoices)
            
            # TVSH total
            total_vat = sum(float(inv['vat_amount']) for inv in all_invoices)
            
            # Përditëso etiketat
            self.stats_labels['total_invoices'].configure(text=str(total_invoices))
            self.stats_labels['month_invoices'].configure(text=str(month_count))
            self.stats_labels['total_revenue'].configure(text=f"{total_revenue:,.2f} €".replace(",", " "))
            self.stats_labels['total_vat'].configure(text=f"{total_vat:,.2f} €".replace(",", " "))
            
            # Faturat e fundit (5 të fundit)
            recent_invoices = all_invoices[:5]
            self.load_recent_invoices(recent_invoices)
            
        except Exception as e:
            print(f"Gabim në ngarkimin e statistikave: {e}")
    
    def load_recent_invoices(self, invoices):
        """Ngarkon faturaet e fundit në tabelë"""
        # Pastro tabelën (përveç header-it)
        for widget in self.recent_table_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.grid_info()['row'] > 0:
                widget.destroy()
        
        # Shto rreshtat
        for i, invoice in enumerate(invoices, start=1):
            row_data = [
                invoice['invoice_number'],
                invoice['date'].strftime("%d.%m.%Y") if invoice['date'] else "",
                invoice.get('client_name', ''),
                f"{float(invoice['total']):,.2f} €".replace(",", " "),
                invoice['status']
            ]
            
            for j, data in enumerate(row_data):
                label = ctk.CTkLabel(
                    self.recent_table_frame,
                    text=str(data),
                    font=ctk.CTkFont(size=11)
                )
                label.grid(row=i, column=j, padx=10, pady=5, sticky="ew")

