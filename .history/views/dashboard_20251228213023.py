"""
Dashboard - Versioni i Ngjeshur (Compact)
"""
import customtkinter as ctk
from models.database import Database
from models.invoice import Invoice

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F8F9FA")
        
        self.db = Database()
        self.db.connect()
        
        self.primary_color = "#FF6600"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True)
        
        self.create_widgets()

    def create_widgets(self):
        # Header i vogël
        header = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 15))
        ctk.CTkLabel(header, text="Përmbledhja e Biznesit", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.text_main).pack(side="left")

        # Kartat e Statistikat (Më të vogla)
        stats_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        stats_container.pack(fill="x", padx=30, pady=10)
        
        stats = Invoice.get_stats(self.db)
        
        self.add_stat_card(stats_container, "Faturat Total", str(stats['total_count']), "📝", 0)
        self.add_stat_card(stats_container, "Ardhura Total", f"{float(stats['total_revenue']):,.2f} €", "💰", 1)
        self.add_stat_card(stats_container, "TVSH Total", f"{float(stats['total_vat']):,.2f} €", "🧾", 2)
        
        stats_container.columnconfigure((0, 1, 2), weight=1)

        # Faturat e Fundit (Tabela e ngjeshur)
        recent_label = ctk.CTkLabel(self.scrollable_frame, text="Faturat e Fundit", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.text_main)
        recent_label.pack(anchor="w", padx=35, pady=(20, 5))
        
        self.recent_container = ctk.CTkFrame(self.scrollable_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E9ECEF")
        self.recent_container.pack(fill="x", padx=30, pady=5)
        
        self.load_recent_invoices()

    def add_stat_card(self, parent, title, value, icon, col):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E9ECEF", height=100)
        card.grid(row=0, column=col, padx=10, sticky="ew")
        card.pack_propagate(False)
        
        # Icon
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24)).pack(pady=(10, 0))
        # Title
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=self.text_secondary).pack()
        # Value
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.primary_color).pack(pady=(0, 10))

    def load_recent_invoices(self):
        invoices = Invoice.get_all(self.db, limit=5)
        for inv in invoices:
            row = ctk.CTkFrame(self.recent_container, fg_color="transparent", height=38)
            row.pack(fill="x", padx=10)
            ctk.CTkFrame(self.recent_container, height=1, fg_color="#F1F3F5").pack(fill="x")
            
            ctk.CTkLabel(row, text=inv['invoice_number'], font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=inv.get('client_name', '-'), font=ctk.CTkFont(size=12)).pack(side="left", padx=20)
            total = f"{float(inv['total']):,.2f} €"
            ctk.CTkLabel(row, text=total, font=ctk.CTkFont(size=12, weight="bold"), text_color=self.primary_color).pack(side="right", padx=10)
