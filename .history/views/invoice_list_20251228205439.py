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
        super().__init__(parent, fg_color="#FFFFFF")
        
        self.db = Database()
        self.db.connect()
        
        # Sistemi i ngjyrave Premium
        self.primary_color = "#FF6600"
        self.hover_color = "#E55C00"
        self.bg_secondary = "#F8F9FA"
        self.border_color = "#E9ECEF"
        self.text_main = "#212529"
        self.text_dim = "#6C757D"
        
        self.create_widgets()
        self.after(50, self.load_invoices)

    def create_widgets(self):
        """Ndërtimi i strukturës kryesore"""
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
            command=self.load_invoices,
            cursor="hand2"
        )
        self.btn_refresh.pack(side="right")

        self.filter_bar = ctk.CTkFrame(self, fg_color=self.bg_secondary, corner_radius=12, border_width=1, border_color=self.border_color)
        self.filter_bar.pack(fill="x", padx=40, pady=10)
        
        search_frame = ctk.CTkFrame(self.filter_bar, fg_color="transparent")
        search_frame.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(search_frame, text="Kërko faturën", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.text_main).pack(anchor="w")
        self.search_entry = ctk.CTkEntry(search_frame, width=300, height=40, placeholder_text="Numri, emri i klientit...", corner_radius=8, border_width=1)
        self.search_entry.pack(pady=(5, 0))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        self.search_timer = None

        self.table_header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.table_header.pack(fill="x", padx=40, pady=(20, 0))
        
        header_cols = [
            ("NUMRI", 12), ("DATA", 12), ("KLIENTI", 30),
            ("TVSH", 10), ("TOTALI", 16), ("VEPRIMET", 20)
        ]
        
        for i, (text, weight) in enumerate(header_cols):
            self.table_header.grid_columnconfigure(i, weight=weight, uniform="col")
            lbl = ctk.CTkLabel(
                self.table_header, text=text, 
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=self.text_dim
            )
            px = 20 if i == 0 else 10
            lbl.grid(row=0, column=i, sticky="w", padx=px)

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=30, pady=(5, 30))

    def on_search_change(self, event):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.load_invoices)

    def load_invoices(self):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
        filters = {}
        search = self.search_entry.get().strip()
        if search: filters['search'] = search
        invoices = Invoice.get_all(self.db, filters)
        if not invoices:
            self.show_empty_state()
            return
        groups = {}
        for inv in invoices:
            cname = inv.get('client_name', 'Pa Emër').strip()
            if cname not in groups: groups[cname] = []
            groups[cname].append(inv)
        for name in sorted(groups.keys()):
            self.add_client_group(name, groups[name])

    def show_empty_state(self):
        container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        container.pack(pady=100)
        ctk.CTkLabel(container, text="📂", font=ctk.CTkFont(size=60)).pack()
        ctk.CTkLabel(container, text="Nuk u gjet asnjë faturë", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.text_main).pack(pady=10)

    def add_client_group(self, client_name, invoices):
        group_container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        group_container.pack(fill="x", pady=(0, 15))
        header_btn = ctk.CTkFrame(group_container, fg_color=self.bg_secondary, height=50, corner_radius=8, cursor="hand2")
        header_btn.pack(fill="x")
        header_btn.pack_propagate(False)
        total_sum = sum(float(inv['total']) for inv in invoices)
        count = len(invoices)
        label_text = f"  ▸  {client_name} ({count} fatura)"
        lbl_info = ctk.CTkLabel(header_btn, text=label_text, font=ctk.CTkFont(family="Inter", size=14, weight="bold"), text_color=self.text_main)
        lbl_info.pack(side="left", padx=15)
        lbl_total = ctk.CTkLabel(header_btn, text=f"Total: {total_sum:,.2f} €".replace(",", " "), font=ctk.CTkFont(family="Inter", size=14, weight="bold"), text_color=self.primary_color)
        lbl_total.pack(side="right", padx=20)
        content_frame = ctk.CTkFrame(group_container, fg_color="transparent")
        def toggle_click(event=None):
            if content_frame.winfo_manager():
                content_frame.pack_forget()
                lbl_info.configure(text=f"  ▸  {client_name} ({count} fatura)")
            else:
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
        outer_frame = ctk.CTkFrame(parent, fg_color="transparent", height=54, corner_radius=0)
        outer_frame.pack(fill="x")
        row_frame = ctk.CTkFrame(outer_frame, fg_color="#FFFFFF", height=52, corner_radius=0)
        row_frame.pack(fill="x", padx=1)
        row_frame.pack_propagate(False)
        def on_enter(e): row_frame.configure(fg_color="#FBFBFB")
        def on_leave(e): row_frame.configure(fg_color="#FFFFFF")
        row_frame.bind("<Enter>", on_enter)
        row_frame.bind("<Leave>", on_leave)
        ctk.CTkFrame(parent, height=1, fg_color=self.border_color).pack(fill="x")
        weights = [12, 12, 30, 10, 16, 20]
        for i, w in enumerate(weights):
            row_frame.grid_columnconfigure(i, weight=w, uniform="col")
        
        lbl_num = ctk.CTkLabel(row_frame, text=inv['invoice_number'], font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=self.primary_color)
        lbl_num.grid(row=0, column=0, sticky="w", padx=20)
        date_str = inv['date'].strftime("%d.%m.%Y") if inv['date'] else "-"
        ctk.CTkLabel(row_frame, text=date_str, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_main).grid(row=0, column=1, sticky="w", padx=10)
        c_name = inv.get('client_name', '').strip()
        ctk.CTkLabel(row_frame, text=c_name, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_dim).grid(row=0, column=2, sticky="w", padx=10)
        vat_val = f"{float(inv.get('vat_percentage', 0)):.0f}%"
        ctk.CTkLabel(row_frame, text=vat_val, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_dim).grid(row=0, column=3, sticky="w", padx=10)
        total_val = f"{float(inv.get('total', 0)):,.2f} €".replace(",", " ")
        ctk.CTkLabel(row_frame, text=total_val, font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=self.text_main).grid(row=0, column=4, sticky="w", padx=10)
        
        actions = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=15)
        
        inv_id = inv['id']
        pdf_path = inv.get('pdf_path')
        
        # Robust PDF path checking for USB/moves
        actual_path = pdf_path
        if pdf_path:
            if not os.path.exists(pdf_path):
                from config.settings import EXPORTS_DIR
                filename = os.path.basename(pdf_path)
                rel_path = os.path.join(EXPORTS_DIR, filename)
                if os.path.exists(rel_path):
                    actual_path = rel_path
                else:
                    actual_path = None

        btn_view = ctk.CTkButton(
            actions, text="👁", width=32, height=32, 
            fg_color="transparent", text_color="#555555", 
            hover_color="#EEEEEE", font=ctk.CTkFont(size=18),
            command=lambda i=inv_id, p=actual_path: self.handle_pdf_action(i, p),
            cursor="hand2"
        )
        btn_view.pack(side="left", padx=2)
        btn_edit = ctk.CTkButton(
            actions, text="✎", width=32, height=32, 
            fg_color="transparent", text_color="#0062CC", 
            hover_color="#E7F3FF", font=ctk.CTkFont(size=18),
            command=lambda i=inv_id: self.edit_invoice(i),
            cursor="hand2"
        )
        btn_edit.pack(side="left", padx=2)
        btn_del = ctk.CTkButton(
            actions, text="✕", width=32, height=32, 
            fg_color="transparent", text_color="#C82333", 
            hover_color="#F8D7DA", font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda i=inv_id: self.delete_invoice(i),
            cursor="hand2"
        )
        btn_del.pack(side="left", padx=2)
        
        if not (actual_path and os.path.exists(actual_path)):
            btn_gen = ctk.CTkButton(
                actions, text="Gjenero", width=65, height=28, 
                fg_color=self.primary_color, hover_color=self.hover_color, 
                corner_radius=6, cursor="hand2",
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                command=lambda i=inv_id: self.generate_pdf(i)
            )
            btn_gen.pack(side="left", padx=(5, 0))

    def handle_pdf_action(self, inv_id, path):
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("Gabim", f"Nuk mund të hapet: {e}")
        else:
            if messagebox.askyesno("PDF Mungon", "PDF nuk u gjet. Ta gjeneroj tani?"):
                self.generate_pdf(inv_id)

    def generate_pdf(self, inv_id):
        inv = Invoice.get_by_id(inv_id, self.db)
        if not inv: return
        try:
            gen = PDFGenerator()
            out = gen.generate(inv)
            inv.pdf_path = out
            inv.save()
            self.load_invoices()
            os.startfile(out)
        except Exception as e: messagebox.showerror("Gabim", f"Dështoi: {str(e)}")

    def edit_invoice(self, inv_id):
        main = self.winfo_toplevel()
        if hasattr(main, 'show_invoice_form'): main.show_invoice_form(inv_id)

    def delete_invoice(self, inv_id):
        if messagebox.askyesno("Konfirmim", "A jeni të sigurt?"):
            inv = Invoice.get_by_id(inv_id, self.db)
            if inv and inv.delete(): self.load_invoices()
