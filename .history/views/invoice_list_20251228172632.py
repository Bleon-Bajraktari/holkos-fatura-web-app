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
            text="Refresko",
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
        
        # Status Filter
        status_frame = ctk.CTkFrame(self.filter_bar, fg_color="transparent")
        status_frame.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(status_frame, text="Statusi", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.text_main).pack(anchor="w")
        self.status_var = ctk.StringVar(value="Të gjitha")
        self.status_combo = ctk.CTkComboBox(
            status_frame, 
            values=["Të gjitha", "DRAFT", "SENT", "PAID"],
            variable=self.status_var,
            width=160,
            height=40,
            corner_radius=8,
            command=lambda x: self.load_invoices()
        )
        self.status_combo.pack(pady=(5, 0))

        # 3. Table Header
        self.table_header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.table_header.pack(fill="x", padx=40, pady=(20, 0))
        
        # Përdorim grid weights identike me rreshtat
        header_cols = [
            ("NUMRI", 15),
            ("DATA", 15),
            ("KLIENTI", 30),
            ("TOTALI", 15),
            ("STATUSI", 10),
            ("VEPRIMET", 15)
        ]
        
        for i, (text, weight) in enumerate(header_cols):
            self.table_header.grid_columnconfigure(i, weight=weight)
            lbl = ctk.CTkLabel(
                self.table_header, 
                text=text, 
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.text_dim
            )
            lbl.grid(row=0, column=i, sticky="w", padx=10)

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
        
        status = self.status_var.get()
        if status != "Të gjitha":
            filters['status'] = status.lower()
            
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
        """Krijon një seksion të zgjerueshëm për klientin"""
        group_container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        group_container.pack(fill="x", pady=(0, 15))
        
        # Header i grupit
        header_btn = ctk.CTkFrame(group_container, fg_color=self.bg_secondary, height=50, corner_radius=8, cursor="hand2")
        header_btn.pack(fill="x")
        header_btn.pack_propagate(False)
        
        # Informacionet e grupit
        total_sum = sum(float(inv['total']) for inv in invoices)
        count = len(invoices)
        
        label_text = f"  ▾  {client_name} ({count} fatura)"
        lbl_info = ctk.CTkLabel(header_btn, text=label_text, font=ctk.CTkFont(size=14, weight="bold"), text_color=self.text_main)
        lbl_info.pack(side="left", padx=15)
        
        lbl_total = ctk.CTkLabel(header_btn, text=f"Total: {total_sum:,.2f} €".replace(",", " "), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.primary_color)
        lbl_total.pack(side="right", padx=20)
        
        # Content (Faturat)
        content_frame = ctk.CTkFrame(group_container, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=5)
        
        # Shto rreshtat e faturave
        for inv in invoices:
            self.add_invoice_row(content_frame, inv)
            
        # Logjika e Toggle (E hapur si default për dizajnin premium)
        self.is_expanded = True
        def toggle_click(event):
            nonlocal content_frame
            if content_frame.winfo_manager():
                content_frame.pack_forget()
                lbl_info.configure(text=f"  ▸  {client_name} ({count} fatura)")
            else:
                content_frame.pack(fill="x", padx=10, pady=5)
                lbl_info.configure(text=f"  ▾  {client_name} ({count} fatura)")
        
        header_btn.bind("<Button-1>", toggle_click)
        lbl_info.bind("<Button-1>", toggle_click)

    def add_invoice_row(self, parent, inv):
        """Dizenjimi i një rreshti të vetëm faturë"""
        row_frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", height=50, corner_radius=0)
        row_frame.pack(fill="x")
        row_frame.pack_propagate(False)
        
        # Vija ndarëse poshtë
        border = ctk.CTkFrame(parent, height=1, fg_color=self.border_color)
        border.pack(fill="x")
        
        # Grid weights (duhet të përputhen me Header)
        row_frame.grid_columnconfigure(0, weight=15) # Numri
        row_frame.grid_columnconfigure(1, weight=15) # Data
        row_frame.grid_columnconfigure(2, weight=30) # Klienti
        row_frame.grid_columnconfigure(3, weight=15) # Totali
        row_frame.grid_columnconfigure(4, weight=10) # Statusi
        row_frame.grid_columnconfigure(5, weight=15) # Veprimet
        
        # 1. Numri
        ctk.CTkLabel(row_frame, text=inv['invoice_number'], font=ctk.CTkFont(size=13, weight="bold"), text_color=self.primary_color).grid(row=0, column=0, sticky="w", padx=20)
        
        # 2. Data
        date_str = inv['date'].strftime("%d.%m.%Y") if inv['date'] else "-"
        ctk.CTkLabel(row_frame, text=date_str, font=ctk.CTkFont(size=13), text_color=self.text_main).grid(row=0, column=1, sticky="w", padx=10)
        
        # 3. Klienti
        ctk.CTkLabel(row_frame, text=inv.get('client_name', '').strip(), font=ctk.CTkFont(size=13), text_color=self.text_dim).grid(row=0, column=2, sticky="w", padx=10)
        
        # 4. Totali
        total_val = f"{float(inv.get('total', 0)):,.2f} €".replace(",", " ")
        ctk.CTkLabel(row_frame, text=total_val, font=ctk.CTkFont(size=13, weight="bold"), text_color=self.text_main).grid(row=0, column=3, sticky="w", padx=10)
        
        # 5. Statusi
        status = str(inv.get('status', '')).upper()
        s_color = "#28A745" if status == "PAID" else "#FFC107" if status == "SENT" else "#6C757D"
        
        status_badge = ctk.CTkFrame(row_frame, fg_color=s_color, corner_radius=4, height=22)
        status_badge.grid(row=0, column=4, sticky="w", padx=10)
        status_badge.pack_propagate(False)
        ctk.CTkLabel(status_badge, text=status, font=ctk.CTkFont(size=9, weight="bold"), text_color="white").pack(expand=True)
        
        # 6. Veprimet
        actions = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=20)
        
        inv_id = inv['id']
        pdf_path = inv.get('pdf_path')
        
        # Eye Icon para PDF (Quick View)
        btn_view = ctk.CTkButton(
            actions, text="👁", width=30, height=30, 
            fg_color="transparent", text_color=self.text_dim, 
            hover_color=self.bg_secondary, font=ctk.CTkFont(size=16),
            command=lambda: self.handle_pdf_action(inv_id, pdf_path)
        )
        btn_view.pack(side="left", padx=2)
        
        # Edit Icon
        btn_edit = ctk.CTkButton(
            actions, text="✎", width=30, height=30, 
            fg_color="transparent", text_color="#007BFF", 
            hover_color="#E7F1FF", font=ctk.CTkFont(size=16),
            command=lambda: self.edit_invoice(inv_id)
        )
        btn_edit.pack(side="left", padx=2)
        
        # Delete Icon
        btn_del = ctk.CTkButton(
            actions, text="✕", width=30, height=30, 
            fg_color="transparent", text_color="#DC3545", 
            hover_color="#F8D7DA", font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self.delete_invoice(inv_id)
        )
        btn_del.pack(side="left", padx=2)
        
        # Dinamika e Gjenero (Nëse mungon PDF)
        if not (pdf_path and os.path.exists(pdf_path)):
            btn_gen = ctk.CTkButton(
                actions, text="Gjenero", width=70, height=28, 
                fg_color=self.primary_color, hover_color=self.hover_color, 
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda: self.generate_pdf(inv_id)
            )
            btn_gen.pack(side="left", padx=5)

    def handle_pdf_action(self, inv_id, path):
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Gabim", f"Nuk mund të hapet PDF: {e}")
        else:
            self.generate_pdf(inv_id)

    def generate_pdf(self, inv_id):
        inv = Invoice.get_by_id(inv_id, self.db)
        if not inv: return
        
        try:
            gen = PDFGenerator()
            out = gen.generate(inv)
            inv.pdf_path = out
            inv.save()
            # Rifresko pamjen për të shkaktojë zhdukjen e butonit 'Gjenero'
            self.load_invoices()
            os.startfile(out)
        except Exception as e:
            messagebox.showerror("Gabim", f"Gjenerimi dështoi: {e}")

    def edit_invoice(self, inv_id):
        main = self.winfo_toplevel()
        if hasattr(main, 'show_invoice_form'):
            main.show_invoice_form(inv_id)

    def delete_invoice(self, inv_id):
        if messagebox.askyesno("Konfirmim", "A jeni të sigurt?"):
            inv = Invoice.get_by_id(inv_id, self.db)
            if inv and inv.delete():
                self.load_invoices()
