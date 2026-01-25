"""
Dashboard view - v1.1.3 (Rregullim Final i statistikave)
"""
import customtkinter as ctk
from models.database import Database
from models.invoice import Invoice
from models.client import Client
from datetime import datetime, timedelta

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F8F9FA")
        
        self.primary_color = "#FF6600"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        self.border_color = "#E9ECEF"
        
        self.db = Database()
        self.db.connect()
        
        self.create_widgets()
        self.after(10, self.load_statistics)
    
    def create_widgets(self):
        # 1. Header
        header_container = ctk.CTkFrame(self, fg_color="transparent")
        header_container.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(
            header_container, 
            text="Përmbledhja e Biznesit", 
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            text_color=self.text_main
        ).pack(side="left")
        
        date_card = ctk.CTkFrame(header_container, fg_color="#FFFFFF", corner_radius=8, border_width=1, border_color=self.border_color)
        date_card.pack(side="right")
        ctk.CTkLabel(date_card, text=datetime.now().strftime("%d %B, %Y"), font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=self.text_main).pack(padx=15, pady=6)

        # 2. Statistics Cards Grid - Rritet lartësia totale
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=20, pady=5)
        
        self.stats_labels = {}
        stats_info = [
            ("Totali i Faturave", "total_invoices", "📄", "#3498DB"),
            ("Faturat këtë Muaj", "month_invoices", "📅", "#9B59B6"),
            ("Ardhura Totale", "total_revenue", "💰", "#2ECC71"),
            ("TVSH e Grumbulluar", "total_vat", "🏦", "#E67E22")
        ]
        
        for i, (label, key, icon, color) in enumerate(stats_info):
            self.create_stat_card(i, label, key, icon, color)
            
        # 3. Recent Activity Section
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=30, pady=(10, 25))
        
        recent_card = ctk.CTkFrame(main_content, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color=self.border_color)
        recent_card.pack(fill="both", expand=True)
        
        card_header = ctk.CTkFrame(recent_card, fg_color="transparent", height=45)
        card_header.pack(fill="x", padx=20, pady=(10, 5))
        card_header.pack_propagate(False)
        ctk.CTkLabel(card_header, text="Faturat e Fundit", font=ctk.CTkFont(family="Inter", size=15, weight="bold"), text_color=self.text_main).pack(side="left")
        
        table_main = ctk.CTkFrame(recent_card, fg_color="transparent")
        table_main.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        
        table_header = ctk.CTkFrame(table_main, fg_color="#F8F9FA", height=35, corner_radius=6)
        table_header.pack(fill="x", pady=(0, 8))
        table_header.pack_propagate(False)
        
        self.col_weights = [1.5, 1.5, 4, 3] 
        for i, weight in enumerate(self.col_weights):
            table_header.grid_columnconfigure(i, weight=int(weight*10), uniform="col")
            
        header_text = ["NUMRI", "DATA", "KLIENTI", "TOTALI"]
        for i, txt in enumerate(header_text):
            ctk.CTkLabel(table_header, text=txt, font=ctk.CTkFont(family="Inter", size=10, weight="bold"), text_color=self.text_secondary, anchor="w").grid(row=0, column=i, padx=12, sticky="w")

        self.rows_container = ctk.CTkScrollableFrame(table_main, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True)

    def create_stat_card(self, index, label_text, key, icon, color):
        """Krijon një kartelë - Me hapësirë të garantuar"""
        # Rrisim lartësinë në 140px për të pasur pafund hapësirë
        card = ctk.CTkFrame(self.stats_container, fg_color="#FFFFFF", height=140, corner_radius=12, border_width=1, border_color=self.border_color)
        card.grid(row=0, column=index, padx=8, pady=5, sticky="ew")
        self.stats_container.grid_columnconfigure(index, weight=1)
        card.pack_propagate(False)
        
        # Padding i brendshëm më i madh
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)
        
        light_colors = {"#3498DB": "#EBF5FB", "#9B59B6": "#F5EEF8", "#2ECC71": "#EAFAF1", "#E67E22": "#FEF5E7"}
        bg_color = light_colors.get(color, "#F1F1F1")
        
        icon_box = ctk.CTkFrame(inner, fg_color=bg_color, width=36, height=36, corner_radius=8)
        icon_box.pack(anchor="w", pady=(0, 12))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=ctk.CTkFont(size=18), text_color=color).pack(expand=True)
        
        # Label me padding të poshtëm të detyruar
        lbl = ctk.CTkLabel(inner, text=label_text, font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=self.text_secondary, anchor="w")
        lbl.pack(fill="x", pady=(0, 4))
        
        # Vallbl me font fiks që nuk lëviz
        val_lbl = ctk.CTkLabel(inner, text="...", font=ctk.CTkFont(family="Inter", size=24, weight="bold"), text_color=self.text_main, anchor="w")
        val_lbl.pack(fill="x")
        self.stats_labels[key] = val_lbl

    def load_statistics(self):
        try:
            stats = Invoice.get_stats(self.db)
            self.stats_labels['total_invoices'].configure(text=str(stats.get('total_count', 0)))
            self.stats_labels['month_invoices'].configure(text=str(stats.get('month_count', 0)))
            revenue = float(stats.get('total_revenue', 0) or 0)
            vat = float(stats.get('total_vat', 0) or 0)
            self.stats_labels['total_revenue'].configure(text=f"{revenue:,.2f} €".replace(",", " "))
            self.stats_labels['total_vat'].configure(text=f"{vat:,.2f} €".replace(",", " "))
            
            recent_invoices = Invoice.get_all(self.db, limit=10)
            self.render_recent_rows(recent_invoices)
        except Exception as e: print(f"Gabim në Dashboard: {e}")

    def render_recent_rows(self, invoices):
        for widget in self.rows_container.winfo_children(): widget.destroy()
        for i, inv in enumerate(invoices):
            row = ctk.CTkFrame(self.rows_container, fg_color="transparent", height=40)
            row.pack(fill="x", pady=0)
            row.pack_propagate(False)
            for j, weight in enumerate(self.col_weights):
                row.grid_columnconfigure(j, weight=int(weight*10), uniform="col")
            inv_nr = inv['invoice_number']
            date_str = inv['date'].strftime("%d.%m.%Y") if inv['date'] else "-"
            total_str = f"{float(inv['total']):,.2f} €".replace(",", " ")
            ctk.CTkLabel(row, text=inv_nr, font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=self.text_main).grid(row=0, column=0, padx=12, sticky="w")
            ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(family="Inter", size=11), text_color=self.text_secondary).grid(row=0, column=1, padx=12, sticky="w")
            ctk.CTkLabel(row, text=inv.get('client_name', '-'), font=ctk.CTkFont(family="Inter", size=11), text_color=self.text_main).grid(row=0, column=2, padx=12, sticky="w")
            ctk.CTkLabel(row, text=total_str, font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=self.primary_color).grid(row=0, column=3, padx=12, sticky="w")
            if i < len(invoices) - 1: ctk.CTkFrame(self.rows_container, height=1, fg_color=self.border_color).pack(fill="x", padx=10)
