"""
Dashboard view
"""
import customtkinter as ctk
from models.database import Database
from models.invoice import Invoice
from models.client import Client
from datetime import datetime, timedelta

class DashboardView(ctk.CTkFrame):
    """Dashboard Premium me statistika globale dhe aktivitete të fundit"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F8F9FA")
        
        # Ngjyrat e projektit
        self.primary_color = "#FF6600"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        self.border_color = "#E9ECEF"
        
        self.db = Database()
        self.db.connect()
        
        self.create_widgets()
        self.after(10, self.load_statistics)
    
    def create_widgets(self):
        """Krijon ndërfaqen premium të dashboard-it"""
        # 1. Top Header Section
        header_container = ctk.CTkFrame(self, fg_color="transparent")
        header_container.pack(fill="x", padx=40, pady=(40, 20))
        
        # Welcome side
        welcome_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        welcome_frame.pack(side="left")
        
        ctk.CTkLabel(
            welcome_frame, 
            text="Mirë se vini përsëri!", 
            font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
            text_color=self.text_main,
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            welcome_frame, 
            text="Ja se si po ecën biznesi juaj sot.", 
            font=ctk.CTkFont(family="Inter", size=14),
            text_color=self.text_secondary,
            anchor="w"
        ).pack(anchor="w")
        
        # Date side
        date_card = ctk.CTkFrame(header_container, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color=self.border_color)
        date_card.pack(side="right", padx=(20, 0))
        
        ctk.CTkLabel(
            date_card, 
            text=datetime.now().strftime("%d %B, %Y"), 
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=self.text_main
        ).pack(padx=20, pady=10)

        # 2. Statistics Cards Grid
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=30, pady=10)
        
        self.stats_labels = {}
        # Icons: 📄, 📅, 💰, 🏦
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
        main_content.pack(fill="both", expand=True, padx=40, pady=(30, 40))
        
        # Recent Invoices Card
        recent_card = ctk.CTkFrame(main_content, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color=self.border_color)
        recent_card.pack(fill="both", expand=True)
        
        # Card Header
        card_header = ctk.CTkFrame(recent_card, fg_color="transparent", height=60)
        card_header.pack(fill="x", padx=25, pady=(15, 5))
        card_header.pack_propagate(False)
        
        ctk.CTkLabel(
            card_header, 
            text="Faturat e Fundit", 
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=self.text_main
        ).pack(side="left")
        
        # Table UI
        table_main = ctk.CTkFrame(recent_card, fg_color="transparent")
        table_main.pack(fill="both", expand=True, padx=25, pady=(5, 20))
        
        # Table Header Row
        table_header = ctk.CTkFrame(table_main, fg_color="#F8F9FA", height=45, corner_radius=8)
        table_header.pack(fill="x", pady=(0, 10))
        table_header.pack_propagate(False)
        
        # Alignment Weights
        self.col_weights = [1.5, 1.5, 3, 2, 1.5] # Nr, Data, Klienti, Totali, Status
        for i, weight in enumerate(self.col_weights):
            table_header.grid_columnconfigure(i, weight=int(weight*10), uniform="col")
            
        header_text = ["NUMRI", "DATA", "KLIENTI", "TOTALI", "STATUSI"]
        for i, txt in enumerate(header_text):
            ctk.CTkLabel(
                table_header, 
                text=txt, 
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=self.text_secondary,
                anchor="w"
            ).grid(row=0, column=i, padx=15, sticky="w")

        # Scrollable rows
        self.rows_container = ctk.CTkScrollableFrame(table_main, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True)

    def create_stat_card(self, index, label_text, key, icon, color):
        """Krijon një kartelë statistikore premium"""
        card = ctk.CTkFrame(self.stats_container, fg_color="#FFFFFF", height=130, corner_radius=15, border_width=1, border_color=self.border_color)
        card.grid(row=0, column=index, padx=10, pady=10, sticky="ew")
        self.stats_container.grid_columnconfigure(index, weight=1)
        card.pack_propagate(False)
        
        # Icon Container (Përdorim ngjyra fikse pasi Tkinter nuk suporton HEX alpha)
        light_colors = {
            "#3498DB": "#EBF5FB", # Light Blue
            "#9B59B6": "#F5EEF8", # Light Purple
            "#2ECC71": "#EAFAF1", # Light Green
            "#E67E22": "#FEF5E7"  # Light Orange
        }
        bg_color = light_colors.get(color, "#F1F1F1")
        
        icon_box = ctk.CTkFrame(card, fg_color=bg_color, width=45, height=45, corner_radius=10)
        icon_box.place(x=20, y=20)
        icon_box.pack_propagate(False)
        
        ctk.CTkLabel(icon_box, text=icon, font=ctk.CTkFont(size=20), text_color=color).pack(expand=True)
        
        # Text Data
        ctk.CTkLabel(
            card, 
            text=label_text, 
            font=ctk.CTkFont(family="Inter", size=13), 
            text_color=self.text_secondary
        ).place(x=20, y=75)
        
        val_lbl = ctk.CTkLabel(
            card, 
            text="...", 
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"), 
            text_color=self.text_main
        )
        val_lbl.place(x=20, y=95)
        self.stats_labels[key] = val_lbl

    def load_statistics(self):
        """Ngarkon të dhënat reale"""
        try:
            stats = Invoice.get_stats(self.db)
            
            # Përditëso shifrat
            self.stats_labels['total_invoices'].configure(text=str(stats.get('total_count', 0)))
            self.stats_labels['month_invoices'].configure(text=str(stats.get('month_count', 0)))
            
            revenue = float(stats.get('total_revenue', 0) or 0)
            vat = float(stats.get('total_vat', 0) or 0)
            
            self.stats_labels['total_revenue'].configure(text=f"{revenue:,.2f} €".replace(",", " "))
            self.stats_labels['total_vat'].configure(text=f"{vat:,.2f} €".replace(",", " "))
            
            # Faturat e fundit (limit 10)
            recent_invoices = Invoice.get_all(self.db, limit=10)
            self.render_recent_rows(recent_invoices)
            
        except Exception as e:
            print(f"Gabim në Dashboard: {e}")

    def render_recent_rows(self, invoices):
        """Renderon rreshtat e tabelës së faturave të fundit"""
        for widget in self.rows_container.winfo_children():
            widget.destroy()
            
        for i, inv in enumerate(invoices):
            row = ctk.CTkFrame(self.rows_container, fg_color="transparent", height=50)
            row.pack(fill="x", pady=0)
            row.pack_propagate(False)
            
            # Alinjimi
            for j, weight in enumerate(self.col_weights):
                row.grid_columnconfigure(j, weight=int(weight*10), uniform="col")
                
            # Hover 효과
            def on_enter(e, r=row): r.configure(fg_color="#F8F9FA")
            def on_leave(e, r=row): r.configure(fg_color="transparent")
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            
            inv_nr = inv['invoice_number']
            date_str = inv['date'].strftime("%d.%m.%Y") if inv['date'] else "-"
            client = inv.get('client_name', '-')
            total_str = f"{float(inv['total']):,.2f} €".replace(",", " ")
            status = str(inv['status']).upper()
            
            # Labels
            ctk.CTkLabel(row, text=inv_nr, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), text_color=self.text_main).grid(row=0, column=0, padx=15, sticky="w")
            ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(family="Inter", size=12), text_color=self.text_secondary).grid(row=0, column=1, padx=15, sticky="w")
            ctk.CTkLabel(row, text=client, font=ctk.CTkFont(family="Inter", size=12), text_color=self.text_main).grid(row=0, column=2, padx=15, sticky="w")
            ctk.CTkLabel(row, text=total_str, font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=self.primary_color).grid(row=0, column=3, padx=15, sticky="w")
            
            # Status Badge
            status_colors = {
                "PAID": ("#2ECC71", "#EAFAF1"), # Text, BG
                "SENT": ("#FF6600", "#FFF4ED"), 
                "DRAFT": ("#95A5A6", "#F2F4F4")
            }
            
            text_color, bg_color = status_colors.get(status, ("#95A5A6", "#F2F4F4"))
            badge = ctk.CTkFrame(row, fg_color=bg_color, height=24, corner_radius=6)
            badge.grid(row=0, column=4, padx=15, sticky="w")
            
            ctk.CTkLabel(badge, text=status, font=ctk.CTkFont(family="Inter", size=10, weight="bold"), text_color=text_color).pack(padx=8)
            
            # Ndarësi (Subtle line)
            if i < len(invoices) - 1:
                line = ctk.CTkFrame(self.rows_container, height=1, fg_color=self.border_color)
                line.pack(fill="x", padx=10)

