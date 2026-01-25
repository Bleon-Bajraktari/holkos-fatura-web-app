import os
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.invoice import Invoice
from services.pdf_generator import PDFGenerator
from views.invoice_form import InvoiceFormView

class InvoiceListView(ctk.CTkFrame):
    """Lista e faturave me dizajni premium dhe performance të lartë"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="#FFFFFF") # Background i pastër bardhë
        
        self.db = Database()
        self.db.connect()
        
        # Sistemi i ngjyrave Premium
        self.primary_color = "#FF6600"
        self.hover_color = "#E55C00"
        self.bg_secondary = "#F8F9FA" # Shumë e lehtë
        self.border_color = "#E9ECEF"
        self.text_main = "#212529"
        self.text_dim = "#6C757D"
        
        self.create_widgets()
        # Ngarko faturat me një vonesë të vogël për animacion visual
        self.after(50, self.load_invoices)

    def create_widgets(self):
        """Ndërtimi i strukturës kryesore"""
        # 1. Top Section (Titulli dhe Butoni Refresh)
        self.top_section = ctk.CTkFrame(self, fg_color="transparent")
        self.top_section.pack(fill="x", padx=40, pady=(30, 20))
        
        title_container = ctk.CTkFrame(self.top_section, fg_color="transparent")
        title_container.pack(side="left")
        
        ctk.CTkLabel(
            title_container, 
            text="Menaxhimi i Faturave", 
            font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
            text_color=self.text_main
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_container, 
            text="Shikoni, kërkoni dhe menaxhoni të gjitha faturat e lëshuara", 
            font=ctk.CTkFont(family="Inter", size=14),
            text_color=self.text_dim
        ).pack(anchor="w")
        
        self.btn_refresh = ctk.CTkButton(
            self.top_section,
            text="Refresh",
            width=120,
            height=40,
            fg_color=self.primary_color,
            hover_color=self.hover_color,
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self.load_invoices
        )
        self.btn_refresh.pack(side="right")

        # 2. Filter Bar
        self.filter_bar = ctk.CTkFrame(self, fg_color=self.bg_secondary, corner_radius=12, border_width=1, border_color=self.border_color)
        self.filter_bar.pack(fill="x", padx=40, pady=10)
        
        # Search
        search_frame = ctk.CTkFrame(self.filter_bar, fg_color="transparent")
        search_frame.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(search_frame, text="Kërko faturën", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.text_main).pack(anchor="w")
        self.search_entry = ctk.CTkEntry(search_frame, width=300, height=40, placeholder_text="Numri, emri i klientit...", corner_radius=8, border_width=1)
        self.search_entry.pack(pady=(5, 0))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        self.search_timer = None

        # 3. Table Header
        self.table_header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.table_header.pack(fill="x", padx=40, pady=(20, 0))
        
        # Përdorim grid weights identike me rreshtat
        header_cols = [
            ("NUMRI", 12),
            ("DATA", 12),
            ("KLIENTI", 30),
            ("TVSH", 10),
            ("TOTALI", 16),
            ("VEPRIMET", 20)
        ]
        
        for i, (text, weight) in enumerate(header_cols):
            self.table_header.grid_columnconfigure(i, weight=weight, uniform="col")
            lbl = ctk.CTkLabel(
                self.table_header, 
                text=text, 
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=self.text_dim
            )
            # Match the row padding
            px = 20 if i == 0 else 10
            lbl.grid(row=0, column=i, sticky="w", padx=px)

        # 4. Scrollable Content
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=30, pady=(5, 30))

    def on_search_change(self, event):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.load_invoices)

    def load_invoices(self):
        """Ngarkon dhe shfaq faturat e grupuara"""
        # Pastrimi
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        filters = {}
        search = self.search_entry.get().strip()
        if search:
            filters['search'] = search
            
        invoices = Invoice.get_all(self.db, filters)
        
        if not invoices:
            self.show_empty_state()
            return
            
        # Grupimi
        groups = {}
        for inv in invoices:
            cname = inv.get('client_name', 'Pa Emër').strip()
            if cname not in groups:
                groups[cname] = []
            groups[cname].append(inv)
            
        # Shfaqja e grupeve
        for name in sorted(groups.keys()):
            self.add_client_group(name, groups[name])

    def show_empty_state(self):
        container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        container.pack(pady=100)
        
        ctk.CTkLabel(container, text="📂", font=ctk.CTkFont(size=60)).pack()
        ctk.CTkLabel(
            container, 
            text="Nuk u gjet asnjë faturë", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.text_main
        ).pack(pady=10)
        ctk.CTkLabel(
            container, 
            text="Provo të ndryshosh filtrat ose kërkimin tuaj.", 
            font=ctk.CTkFont(size=14),
            text_color=self.text_dim
        ).pack()

    def add_client_group(self, client_name, invoices):
        """Krijon një seksion të zgjerueshëm për klientin - Optimizuar për performance"""
        group_container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        group_container.pack(fill="x", pady=(0, 15))
        
        # Header i grupit
        header_btn = ctk.CTkFrame(group_container, fg_color=self.bg_secondary, height=50, corner_radius=8, cursor="hand2")
        header_btn.pack(fill="x")
        header_btn.pack_propagate(False)
        
        # Informacionet e grupit
        total_sum = sum(float(inv['total']) for inv in invoices)
        count = len(invoices)
        
        # Default: Mbyllur (▸)
        label_text = f"  ▸  {client_name} ({count} fatura)"
        lbl_info = ctk.CTkLabel(header_btn, text=label_text, font=ctk.CTkFont(family="Inter", size=14, weight="bold"), text_color=self.text_main)
        lbl_info.pack(side="left", padx=15)
        
        lbl_total = ctk.CTkLabel(header_btn, text=f"Total: {total_sum:,.2f} €".replace(",", " "), font=ctk.CTkFont(family="Inter", size=14, weight="bold"), text_color=self.primary_color)
        lbl_total.pack(side="right", padx=20)
        
        # Content Frame (I fshehur fillimisht)
        content_frame = ctk.CTkFrame(group_container, fg_color="transparent")
        
        # Variabël për të ndjekur nëse rreshtat janë gjeneruar (Lazy Loading)
        self.is_populated = False 

        def toggle_click(event=None):
            nonlocal content_frame
            
            if content_frame.winfo_manager():
                # Fsheh listën
                content_frame.pack_forget()
                lbl_info.configure(text=f"  ▸  {client_name} ({count} fatura)")
            else:
                # Shfaq listën (Lazy Loading)
                if not getattr(content_frame, 'is_populated', False):
                    for inv in invoices:
                        self.add_invoice_row(content_frame, inv)
                    content_frame.is_populated = True
                
                content_frame.pack(fill="x", padx=10, pady=5)
                lbl_info.configure(text=f"  ▾  {client_name} ({count} fatura)")
        
        header_btn.bind("<Button-1>", toggle_click)
        lbl_info.bind("<Button-1>", toggle_click)
        lbl_total.bind("<Button-1>", toggle_click)

    def add_invoice_row(self, parent, inv):
        """Dizenjimi i një rreshti të vetëm faturë me stil modern"""
        # Outer frame for hover and border
        outer_frame = ctk.CTkFrame(parent, fg_color="transparent", height=54, corner_radius=0)
        outer_frame.pack(fill="x")
        
        # Inner row content
        row_frame = ctk.CTkFrame(outer_frame, fg_color="#FFFFFF", height=52, corner_radius=0)
        row_frame.pack(fill="x", padx=1)
        row_frame.pack_propagate(False)
        
        # Hover effects
        def on_enter(e): row_frame.configure(fg_color="#FBFBFB")
        def on_leave(e): row_frame.configure(fg_color="#FFFFFF")
        
        row_frame.bind("<Enter>", on_enter)
        row_frame.bind("<Leave>", on_leave)
        
        # Vija ndarëse mes rreshtave
        ctk.CTkFrame(parent, height=1, fg_color=self.border_color).pack(fill="x")
        
        # Grid weights uniform me Header
        weights = [12, 12, 30, 10, 16, 20]
        for i, w in enumerate(weights):
            row_frame.grid_columnconfigure(i, weight=w, uniform="col")
        
        # 1. Numri
        lbl_num = ctk.CTkLabel(row_frame, text=inv['invoice_number'], font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=self.primary_color)
        lbl_num.grid(row=0, column=0, sticky="w", padx=20)
        
        # 2. Data
        date_str = inv['date'].strftime("%d.%m.%Y") if inv['date'] else "-"
        ctk.CTkLabel(row_frame, text=date_str, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_main).grid(row=0, column=1, sticky="w", padx=10)
        
        # 3. Klienti
        c_name = inv.get('client_name', '').strip()
        ctk.CTkLabel(row_frame, text=c_name, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_dim).grid(row=0, column=2, sticky="w", padx=10)
        
        # 4. TVSH
        vat_val = f"{float(inv.get('vat_percentage', 0)):.0f}%"
        ctk.CTkLabel(row_frame, text=vat_val, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_dim).grid(row=0, column=3, sticky="w", padx=10)
        
        # 5. Totali
        total_val = f"{float(inv.get('total', 0)):,.2f} €".replace(",", " ")
        ctk.CTkLabel(row_frame, text=total_val, font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=self.text_main).grid(row=0, column=4, sticky="w", padx=10)
        
        # 6. Veprimet
        actions = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=15)
        
        inv_id = inv['id']
        pdf_path = inv.get('pdf_path')
        
        # Eye (View PDF) - Gjithmonë prezent
        btn_view = ctk.CTkButton(
            actions, text="👁", width=32, height=32, 
            fg_color="transparent", text_color="#555555", 
            hover_color="#EEEEEE", font=ctk.CTkFont(size=18),
            command=lambda: self.handle_pdf_action(inv_id, pdf_path)
        )
        btn_view.pack(side="left", padx=2)
        
        # Pencil (Edit)
        btn_edit = ctk.CTkButton(
            actions, text="✎", width=32, height=32, 
            fg_color="transparent", text_color="#0062CC", 
            hover_color="#E7F3FF", font=ctk.CTkFont(size=18),
            command=lambda: self.edit_invoice(inv_id)
        )
        btn_edit.pack(side="left", padx=2)
        
        # Trash (Delete)
        btn_del = ctk.CTkButton(
            actions, text="✕", width=32, height=32, 
            fg_color="transparent", text_color="#C82333", 
            hover_color="#F8D7DA", font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda: self.delete_invoice(inv_id)
        )
        btn_del.pack(side="left", padx=2)
        
        # Butoni dinamik "Produkto PDF" nëse nuk ekziston
        if not (pdf_path and os.path.exists(pdf_path)):
            btn_gen = ctk.CTkButton(
                actions, text="Gjenero", width=65, height=28, 
                fg_color=self.primary_color, hover_color=self.hover_color, 
                corner_radius=6,
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                command=lambda: self.generate_pdf(inv_id)
            )
            btn_gen.pack(side="left", padx=(5, 0))

    def handle_pdf_action(self, inv_id, path):
        """Hap PDF nëse ekziston, përndryshe njofton ose e gjeneron"""
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Gabim", f"Nuk mund të hapet skedari: {e}")
        else:
            if messagebox.askyesno("PDF Mungon", "PDF për këtë faturë nuk është gjeneruar ende. A dëshironi ta gjeneroni tani?"):
                self.generate_pdf(inv_id)

    def generate_pdf(self, inv_id):
        inv = Invoice.get_by_id(inv_id, self.db)
        if not inv: return
        
        try:
            gen = PDFGenerator()
            out = gen.generate(inv)
            inv.pdf_path = out
            inv.save()
            # Rifreskoni që të shfaqet rruga e re dhe të zhduket butoni Gjenero
            self.load_invoices()
            os.startfile(out)
        except Exception as e:
            messagebox.showerror("Gabim", f"Gjenerimi dështoi: {str(e)}")

    def edit_invoice(self, inv_id):
        main = self.winfo_toplevel()
        if hasattr(main, 'show_invoice_form'):
            main.show_invoice_form(inv_id)

    def delete_invoice(self, inv_id):
        if messagebox.askyesno("Konfirmim", "A jeni të sigurt që dëshironi të fshini këtë faturë?"):
            inv = Invoice.get_by_id(inv_id, self.db)
            if inv and inv.delete():
                self.load_invoices()
