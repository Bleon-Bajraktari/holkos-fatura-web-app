import os
import customtkinter as ctk
from datetime import datetime, date
from tkinter import messagebox
from models.database import Database
from models.invoice import Invoice
from services.pdf_generator import PDFGenerator
from views.invoice_form import InvoiceFormView

class InvoiceListView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#FFFFFF")
        
        self.db = Database()
        self.db.connect()
        
        self.primary_color = "#FF6600"
        self.hover_color = "#E55C00"
        self.bg_secondary = "#F8F9FA"
        self.border_color = "#E9ECEF"
        self.text_main = "#212529"
        self.text_dim = "#6C757D"
        
        self.search_timer = None # Rregulluar: Tani brenda __init__
        
        self.create_widgets()
        self.after(50, self.load_invoices)

    def create_widgets(self):
        # 1. Top Section
        self.top_section = ctk.CTkFrame(self, fg_color="transparent")
        self.top_section.pack(fill="x", padx=30, pady=(20, 15))
        
        title_container = ctk.CTkFrame(self.top_section, fg_color="transparent")
        title_container.pack(side="left")
        
        ctk.CTkLabel(
            title_container, 
            text="Menaxhimi i Faturave", 
            font=ctk.CTkFont(family="Inter", size=26, weight="bold"),
            text_color=self.text_main
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_container, 
            text="Shikoni, kërkoni dhe menaxhoni faturat", 
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=self.text_dim
        ).pack(anchor="w")
        
        self.btn_refresh = ctk.CTkButton(
            self.top_section, text="Refresh", width=100, height=32,
            fg_color=self.primary_color, hover_color=self.hover_color,
            font=ctk.CTkFont(size=12, weight="bold"), command=self.load_invoices, cursor="hand2"
        )
        self.btn_refresh.pack(side="right")

        self.filter_bar = ctk.CTkFrame(self, fg_color=self.bg_secondary, corner_radius=10, border_width=1, border_color=self.border_color)
        self.filter_bar.pack(fill="x", padx=30, pady=5)
        
        search_frame = ctk.CTkFrame(self.filter_bar, fg_color="transparent")
        search_frame.pack(side="left", padx=15, pady=10)
        
        self.search_entry = ctk.CTkEntry(search_frame, width=250, height=35, placeholder_text="Kërko...", corner_radius=8)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        # Filtri i Viteve (Dinamike nga DB)
        self.current_year = str(date.today().year)
        self.year_var = ctk.StringVar(value=self.current_year)
        available_years = Invoice.get_available_years(self.db)

        ctk.CTkLabel(search_frame, text="Viti:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 5))
        self.year_filter = ctk.CTkOptionMenu(
            search_frame, values=available_years, variable=self.year_var,
            width=80, height=35, corner_radius=8,
            fg_color="#FFFFFF", text_color=self.text_main, button_color="#E9ECEF", button_hover_color="#DEE2E6",
            command=lambda x: self.load_invoices()
        )
        self.year_filter.pack(side="left")
        
        # Filtri i Muajve
        self.months = ["Të gjithë", "Janar", "Shkurt", "Mars", "Prill", "Maj", "Qershor", 
                      "Korrik", "Gusht", "Shtator", "Tetor", "Nëntor", "Dhjetor"]
        self.month_var = ctk.StringVar(value="Të gjithë")
        
        ctk.CTkLabel(search_frame, text="Muaji:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(15, 5))
        self.month_filter = ctk.CTkOptionMenu(
            search_frame, values=self.months, variable=self.month_var,
            width=110, height=35, corner_radius=8,
            fg_color="#FFFFFF", text_color=self.text_main, button_color="#E9ECEF", button_hover_color="#DEE2E6",
            command=lambda x: self.load_invoices()
        )
        self.month_filter.pack(side="left")

        self.table_header = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self.table_header.pack(fill="x", padx=30, pady=(15, 0))
        
        header_cols = [("NUMRI", 12), ("DATA", 12), ("KLIENTI", 30), ("TVSH", 10), ("TOTALI", 16), ("VEPRIMET", 20)]
        for i, (text, weight) in enumerate(header_cols):
            self.table_header.grid_columnconfigure(i, weight=weight, uniform="col")
            lbl = ctk.CTkLabel(self.table_header, text=text, font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_dim)
            lbl.grid(row=0, column=i, sticky="w", padx=10)

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(5, 20))

    def on_search_change(self, event):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.load_invoices)

    def load_invoices(self):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        filters = {}
        search = self.search_entry.get().strip()
        if search:
            filters['search'] = search
        
        # Shto filtrin e vitit dhe muajit
        selected_year = self.year_var.get()
        selected_month_name = self.month_var.get()
        
        if selected_year and selected_year.isdigit():
            year_int = int(selected_year)
            
            if selected_month_name == "Të gjithë":
                filters['date_from'] = f"{selected_year}-01-01"
                filters['date_to'] = f"{selected_year}-12-31"
            else:
                try:
                    month_idx = self.months.index(selected_month_name) # Janar=1, etj.
                    # Llogarit ditën e fundit të muajit
                    if month_idx == 12: # Dhjetor
                        last_day = 31
                    else:
                        # Muaji tjetër dita 1 minus 1 ditë
                        next_month = date(year_int, month_idx + 1, 1) if month_idx < 12 else date(year_int + 1, 1, 1)
                        import calendar
                        last_day = calendar.monthrange(year_int, month_idx)[1]
                    
                    filters['date_from'] = f"{selected_year}-{month_idx:02d}-01"
                    filters['date_to'] = f"{selected_year}-{month_idx:02d}-{last_day:02d}"
                except:
                    # Fallback në gjithë vitin nëse ka error
                    filters['date_from'] = f"{selected_year}-01-01"
                    filters['date_to'] = f"{selected_year}-12-31"
            
        invoices = Invoice.get_all(self.db, filters)
        if not invoices:
            self.show_empty_state()
            return
            
        groups = {}
        for inv in invoices:
            cname = inv.get('client_name', 'Pa Emër').strip()
            if cname not in groups:
                groups[cname] = []
            groups[cname].append(inv)
            
        for name in sorted(groups.keys()):
            self.add_client_group(name, groups[name])

    def show_empty_state(self):
        container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        container.pack(pady=50)
        ctk.CTkLabel(container, text="📂", font=ctk.CTkFont(size=40)).pack()
        ctk.CTkLabel(container, text="Nuk u gjet asnjë faturë", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

    def add_client_group(self, client_name, invoices):
        group_container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        group_container.pack(fill="x", pady=(0, 10))
        
        header_btn = ctk.CTkFrame(group_container, fg_color=self.bg_secondary, height=45, corner_radius=8, cursor="hand2")
        header_btn.pack(fill="x")
        header_btn.pack_propagate(False)
        
        total_sum = sum(float(inv['total']) for inv in invoices)
        label_text = f"  ▸  {client_name} ({len(invoices)})"
        lbl_info = ctk.CTkLabel(header_btn, text=label_text, font=ctk.CTkFont(size=13, weight="bold"))
        lbl_info.pack(side="left", padx=10)
        
        lbl_total = ctk.CTkLabel(header_btn, text=f"Total: {total_sum:,.2f} €", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.primary_color)
        lbl_total.pack(side="right", padx=15)
        
        content_frame = ctk.CTkFrame(group_container, fg_color="transparent")
        
        def toggle_click(event=None):
            if content_frame.winfo_manager():
                content_frame.pack_forget()
                lbl_info.configure(text=f"  ▸  {client_name} ({len(invoices)})")
            else:
                if not getattr(content_frame, 'is_populated', False):
                    for inv in invoices:
                        self.add_invoice_row(content_frame, inv)
                    content_frame.is_populated = True
                content_frame.pack(fill="x", padx=5, pady=2)
                lbl_info.configure(text=f"  ▾  {client_name} ({len(invoices)})")
                
        header_btn.bind("<Button-1>", toggle_click)
        lbl_info.bind("<Button-1>", toggle_click)
        lbl_total.bind("<Button-1>", toggle_click)

    def add_invoice_row(self, parent, inv):
        row_frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", height=45, corner_radius=0)
        row_frame.pack(fill="x")
        row_frame.pack_propagate(False)
        
        ctk.CTkFrame(parent, height=1, fg_color=self.border_color).pack(fill="x")
        
        weights = [12, 12, 30, 10, 16, 20]
        for i, w in enumerate(weights):
            row_frame.grid_columnconfigure(i, weight=w, uniform="col")
            
        ctk.CTkLabel(row_frame, text=inv['invoice_number'], font=ctk.CTkFont(size=12, weight="bold"), text_color=self.primary_color).grid(row=0, column=0, sticky="w", padx=15)
        date_str = inv['date'].strftime("%d.%m.%Y") if inv['date'] else "-"
        ctk.CTkLabel(row_frame, text=date_str, font=ctk.CTkFont(size=12)).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(row_frame, text=inv.get('client_name', '').strip(), font=ctk.CTkFont(size=12), text_color=self.text_dim).grid(row=0, column=2, sticky="w", padx=5)
        
        vat_val = f"{float(inv.get('vat_percentage', 0)):.1f} %"
        ctk.CTkLabel(row_frame, text=vat_val, font=ctk.CTkFont(size=11), text_color=self.text_dim).grid(row=0, column=3, sticky="w", padx=5)
        
        total_val = f"{float(inv.get('total', 0)):,.2f} €"
        ctk.CTkLabel(row_frame, text=total_val, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=4, sticky="w", padx=5)
        
        actions = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=10)
        
        pdf_path = inv.get('pdf_path')
        actual_path = pdf_path
        if pdf_path and not os.path.exists(pdf_path):
            from config.settings import EXPORTS_DIR
            filename = os.path.basename(pdf_path)
            rel_path = os.path.join(EXPORTS_DIR, filename)
            if os.path.exists(rel_path):
                actual_path = rel_path
            else:
                actual_path = None

        btn_view = ctk.CTkButton(actions, text="👁", width=28, height=28, fg_color="transparent", text_color="#555555", hover_color="#EEEEEE", command=lambda i=inv['id'], p=actual_path: self.handle_pdf_action(i, p), cursor="hand2")
        btn_view.pack(side="left", padx=1)
        
        btn_edit = ctk.CTkButton(actions, text="✎", width=28, height=28, fg_color="transparent", text_color="#0062CC", hover_color="#E7F3FF", command=lambda i=inv['id']: self.edit_invoice(i), cursor="hand2")
        btn_edit.pack(side="left", padx=1)
        
        btn_del = ctk.CTkButton(actions, text="✕", width=28, height=28, fg_color="transparent", text_color="#C82333", hover_color="#F8D7DA", command=lambda i=inv['id']: self.delete_invoice(i), cursor="hand2")
        btn_del.pack(side="left", padx=1)
        
        if not (actual_path and os.path.exists(actual_path)):
            btn_gen = ctk.CTkButton(actions, text="Gjenero", width=55, height=24, fg_color=self.primary_color, font=ctk.CTkFont(size=10, weight="bold"), command=lambda i=inv['id']: self.generate_pdf(i), cursor="hand2")
            btn_gen.pack(side="left", padx=(2, 0))

    def handle_pdf_action(self, inv_id, path):
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Gabim", f"Hapja dështoi: {e}")
        else:
            if messagebox.askyesno("PDF", "Ta gjeneroj PDF-në?"):
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
        except Exception as e:
            messagebox.showerror("Gabim", f"Dështoi: {str(e)}")

    def edit_invoice(self, inv_id):
        main = self.winfo_toplevel()
        if hasattr(main, 'show_invoice_form'):
            main.show_invoice_form(inv_id)

    def delete_invoice(self, inv_id):
        if messagebox.askyesno("Konfirmim", "A jeni të sigurt?"):
            inv = Invoice.get_by_id(inv_id, self.db)
            if inv and inv.delete():
                self.load_invoices()
