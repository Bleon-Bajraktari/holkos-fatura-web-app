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
        
        # Ngjyrat e projektit
        self.primary_color = "#FF6600"
        self.bg_secondary = ("#F0F0F0", "#2B2B2B")
        self.text_color = ("black", "white")
        
        self.create_widgets()
        self.after(10, self.load_statistics)
    
    def create_widgets(self):
        """Krijon widget-et e dashboard-it"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        
        title = ctk.CTkLabel(
            header_frame,
            text="Përmbledhja e Biznesit",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(side="left")
        
        date_label = ctk.CTkLabel(
            header_frame,
            text=datetime.now().strftime("%d %B, %Y"),
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        date_label.pack(side="right")
        
        # Frame për statistikat (Cards)
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=20, pady=20)
        
        self.stats_labels = {}
        stats_info = [
            ("Total Fatura", "total_invoices", "📄"),
            ("Fatura këtë muaj", "month_invoices", "📅"),
            ("Totali i ardhurave", "total_revenue", "💰"),
            ("TVSH total", "total_vat", "🏦")
        ]
        
        for i, (label_text, key, icon) in enumerate(stats_info):
            self.create_stat_card(i, label_text, key, icon)
        
        # Bottom Section
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Recent Invoices Section
        recent_section = ctk.CTkFrame(bottom_frame, fg_color=self.bg_secondary, corner_radius=20)
        recent_section.pack(fill="both", expand=True)
        
        recent_header = ctk.CTkFrame(recent_section, fg_color="transparent")
        recent_header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            recent_header,
            text="Faturat e Fundit",
            font=ctk.CTkFont(size=20, weight="bold")
        ) .pack(side="left")
        
        # Table
        table_container = ctk.CTkFrame(recent_section, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Header-i i tabelës
        self.recent_table_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        self.recent_table_frame.pack(fill="both", expand=True)
        
        headers = ["Numri", "Data", "Klienti", "Totali", "Statusi"]
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.recent_table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="gray"
            )
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            self.recent_table_frame.grid_columnconfigure(i, weight=1)
            
    def create_stat_card(self, index, label_text, key, icon):
        """Krijon një kartelë statistikore"""
        card = ctk.CTkFrame(self.stats_container, fg_color=self.bg_secondary, corner_radius=15, height=120)
        card.grid(row=0, column=index, padx=10, pady=10, sticky="ew")
        self.stats_container.grid_columnconfigure(index, weight=1)
        card.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24))
        icon_label.place(relx=0.1, rely=0.2)
        
        title_label = ctk.CTkLabel(card, text=label_text, font=ctk.CTkFont(size=13), text_color="gray")
        title_label.place(relx=0.1, rely=0.5)
        
        value_label = ctk.CTkLabel(card, text="...", font=ctk.CTkFont(size=22, weight="bold"))
        value_label.place(relx=0.1, rely=0.7)
        
        self.stats_labels[key] = value_label
    
    def load_statistics(self):
        """Ngarkon statistikat në mënyrë të optimizuar"""
        try:
            # Merr statistikat e llogaritura direkt nga SQL
            stats = Invoice.get_stats(self.db)
            
            # Përditëso etiketat
            self.stats_labels['total_invoices'].configure(text=str(stats.get('total_count', 0)))
            self.stats_labels['month_invoices'].configure(text=str(stats.get('month_count', 0)))
            
            revenue = float(stats.get('total_revenue', 0) or 0)
            vat = float(stats.get('total_vat', 0) or 0)
            
            self.stats_labels['total_revenue'].configure(text=f"{revenue:,.2f} €".replace(",", " "))
            self.stats_labels['total_vat'].configure(text=f"{vat:,.2f} €".replace(",", " "))
            
            # Faturat e fundit - i marrim veçmas (limit 8)
            recent_invoices = Invoice.get_all(self.db, limit=8)
            self.load_recent_invoices(recent_invoices)
            
        except Exception as e:
            print(f"Gabim në ngarkimin e statistikave: {e}")
    
    def load_recent_invoices(self, invoices):
        """Ngarkon faturaet e fundit në tabelë"""
        # Pastro tabelën (përveç header-it)
        for widget in self.recent_table_frame.winfo_children():
            if widget.grid_info()['row'] > 0:
                widget.destroy()
        
        # Shto rreshtat
        for i, inv in enumerate(invoices, start=1):
            row_data = [
                inv['invoice_number'],
                inv['date'].strftime("%d.%m.%Y") if inv['date'] else "",
                inv.get('client_name', ''),
                f"{float(inv['total']):,.2f} €".replace(",", " "),
                inv['status'].upper()
            ]
            
            for j, data in enumerate(row_data):
                color = None
                if j == 4: # Status
                    status_low = str(data).lower()
                    color = "#4CAF50" if status_low == "paid" else "#FFC107" if status_low == "sent" else "gray"
                
                lbl = ctk.CTkLabel(
                    self.recent_table_frame,
                    text=str(data),
                    font=ctk.CTkFont(size=12, weight="bold" if j==3 else "normal"),
                    text_color=color
                )
                lbl.grid(row=i, column=j, padx=10, pady=8, sticky="ew")
            
            # Vizë ndarëse
            line = ctk.CTkFrame(self.recent_table_frame, height=1, fg_color=("gray90", "gray30"))
            line.grid(row=i, column=0, columnspan=5, sticky="ew", pady=(25, 0))

