"""
Lista e faturave
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.invoice import Invoice
from services.pdf_generator import PDFGenerator
from views.invoice_form import InvoiceFormView

class InvoiceListView(ctk.CTkFrame):
    """Lista e faturave me filtra dhe veprime"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.db = Database()
        self.db.connect()
        
        # Ngjyrat e projektit
        self.primary_color = "#FF6600"
        self.hover_color = "#FF8533"
        self.bg_secondary = ("#F0F0F0", "#2B2B2B")
        
        self.create_widgets()
        self.after(10, self.load_invoices)  # Load invoices after a short delay for smoother UI
    
    def create_widgets(self):
        """Krijon widget-et"""
        # Header Area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Lista e Faturave",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left")
        
        # Frame për filtra
        filters_frame = ctk.CTkFrame(self, fg_color=self.bg_secondary, corner_radius=15)
        filters_frame.pack(fill="x", padx=30, pady=10)
        
        # Kërkimi
        search_container = ctk.CTkFrame(filters_frame, fg_color="transparent")
        search_container.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(search_container, text="Kërko:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_container, width=250, placeholder_text="Numri ose Klienti...", height=35)
        self.search_entry.pack(side="left")
        self.search_timer = None
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # Statusi
        status_container = ctk.CTkFrame(filters_frame, fg_color="transparent")
        status_container.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(status_container, text="Statusi:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 10))
        self.status_var = ctk.StringVar(value="Të gjitha")
        status_combo = ctk.CTkComboBox(
            status_container,
            values=["Të gjitha", "draft", "sent", "paid"],
            variable=self.status_var,
            width=150,
            height=35,
            command=lambda x: self.load_invoices()
        )
        status_combo.pack(side="left")
        
        # Butoni për refresh
        self.btn_refresh = ctk.CTkButton(
            filters_frame,
            text="Refresh",
            command=self.load_invoices,
            width=100,
            height=35,
            fg_color=self.primary_color,
            hover_color=self.hover_color,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_refresh.pack(side="right", padx=20, pady=15)
        
        # Table Header (Static)
        table_header = ctk.CTkFrame(self, fg_color="transparent")
        table_header.pack(fill="x", padx=40, pady=(10, 0))
        
        cols = [
            ("Numri", 0.15),
            ("Data", 0.15),
            ("Klienti", 0.25),
            ("Totali", 0.15),
            ("Statusi", 0.10),
            ("Veprimet", 0.20)
        ]
        
        for text, weight in cols:
            lbl = ctk.CTkLabel(
                table_header, 
                text=text, 
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="gray"
            )
            lbl.place(relx=sum(c[1] for c in cols[:cols.index((text, weight))]), rely=0.5, anchor="w")
        
        # Container for scrollable list
        self.scrollable_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_container.pack(fill="both", expand=True, padx=30, pady=(5, 20))
        
        self.client_groups = []
    
    def on_search_change(self, event):
        """Debounced search"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.load_invoices)
    
    def load_invoices(self):
        """Ngarkon faturat e grupuara sipas klientit"""
        # Pastro kontajnerin
        for widget in self.scrollable_container.winfo_children():
            widget.destroy()
        
        self.client_groups = []
        
        # Filtra
        filters = {}
        search_term = self.search_entry.get()
        if search_term:
            filters['search'] = search_term
        
        status = self.status_var.get()
        if status != "Të gjitha":
            filters['status'] = status
        
        # Merr faturat
        invoices = Invoice.get_all(self.db, filters)
        
        if not invoices:
            no_data = ctk.CTkLabel(
                self.scrollable_container,
                text="Nuk u gjet asnjë faturë.",
                font=ctk.CTkFont(size=16, slant="italic"),
                text_color="gray"
            )
            no_data.pack(pady=40)
            return
            
        # Grupo sipas klientit
        grouped_invoices = {}
        for invoice in invoices:
            client_name = invoice.get('client_name', 'Pa klient')
            if client_name not in grouped_invoices:
                grouped_invoices[client_name] = []
            grouped_invoices[client_name].append(invoice)
        
        # Krijimi i grupeve
        for client_name in sorted(grouped_invoices.keys()):
            client_invoices = grouped_invoices[client_name]
            self.add_client_group(client_name, client_invoices)
            
    def add_client_group(self, client_name, invoices):
        """Shton një grup klientësh në listë"""
        group_frame = ctk.CTkFrame(self.scrollable_container, fg_color="transparent")
        group_frame.pack(fill="x", pady=5)
        
        # Totali i klientit
        client_total = sum(float(inv['total']) for inv in invoices)
        count = len(invoices)
        
        # Header i grupit
        header = ctk.CTkFrame(group_frame, fg_color=self.bg_secondary, height=45, corner_radius=10)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Info i grupit
        info_label = ctk.CTkLabel(
            header,
            text=f"  ▶  {client_name} ({count} fatura)",
            font=ctk.CTkFont(size=14, weight="bold"),
            cursor="hand2"
        )
        info_label.pack(side="left", padx=10)
        
        total_label = ctk.CTkLabel(
            header,
            text=f"Total: {client_total:,.2f} €  ".replace(",", " "),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.primary_color
        )
        total_label.pack(side="right", padx=10)
        
        # Content i grupit (faturat) - initially hidden
        content_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
        
        def toggle():
            if content_frame.winfo_manager():
                content_frame.pack_forget()
                info_label.configure(text=f"  ▶  {client_name} ({count} fatura)")
            else:
                content_frame.pack(fill="x", padx=15, pady=5)
                info_label.configure(text=f"  ▼  {client_name} ({count} fatura)")
                
                # Popullo content nëse është i zbrazët (lazy loading)
                if not content_frame.winfo_children():
                    for inv in invoices:
                        self.add_invoice_item(content_frame, inv)
        
        header.bind("<Button-1>", lambda e: toggle())
        info_label.bind("<Button-1>", lambda e: toggle())
        header.configure(cursor="hand2")
        
    def add_invoice_item(self, parent, invoice):
        """Shton një rresht fatura brenda grupit"""
        item_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        item_frame.pack(fill="x", pady=2)
        
        # Ndarja e kolonave (relx duhet të përputhet me header-in statik)
        cols = [
            (invoice['invoice_number'], 0.15),
            (invoice['date'].strftime("%d.%m.%Y") if invoice['date'] else "", 0.15),
            (invoice.get('client_name', ''), 0.25),
            (f"{float(invoice.get('total', 0)):,.2f} €".replace(",", " "), 0.15),
            (invoice.get('status', '').upper(), 0.10)
        ]
        
        for text, weight in cols:
            color = "gray" if "data" in str(text).lower() else None
            if weight == 0.10: # Statusi
                status = str(text).lower()
                status_color = "#4CAF50" if status == "paid" else "#FFC107" if status == "sent" else "gray"
                lbl = ctk.CTkLabel(item_frame, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color)
            else:
                lbl = ctk.CTkLabel(item_frame, text=text, font=ctk.CTkFont(size=12))
            
            lbl.place(relx=sum(c[1] for c in cols[:cols.index((text, weight))]), rely=0.5, anchor="w")
        
        # Veprimet
        actions = ctk.CTkFrame(item_frame, fg_color="transparent")
        actions.place(relx=0.80, rely=0.5, anchor="w")
        
        inv_id = invoice.get('id')
        pdf_path = invoice.get('pdf_path')
        
        # Butonat e veprimeve
        # View (Eye) -> Open PDF
        btn_view = ctk.CTkButton(
            actions, 
            text="👁", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            text_color="gray20", 
            hover_color="gray90", 
            font=ctk.CTkFont(size=14), 
            command=lambda: self.handle_pdf(inv_id, pdf_path)
        )
        btn_view.pack(side="left", padx=2)
        
        # Edit
        btn_edit = ctk.CTkButton(
            actions, 
            text="✎", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            text_color="blue", 
            hover_color="lightblue", 
            font=ctk.CTkFont(size=14), 
            command=lambda: self.edit_invoice(inv_id)
        )
        btn_edit.pack(side="left", padx=2)
        
        # PDF Status Button (Visual Indicator + Action)
        pdf_exists = pdf_path and os.path.exists(pdf_path)
        btn_pdf_text = "PDF" if pdf_exists else "Gjenero"
        btn_pdf_color = "#4CAF50" if pdf_exists else self.primary_color
        
        btn_pdf = ctk.CTkButton(
            actions, 
            text=btn_pdf_text, 
            width=60, 
            height=30, 
            fg_color=btn_pdf_color, 
            hover_color=self.hover_color, 
            font=ctk.CTkFont(size=11, weight="bold"), 
            command=lambda: self.handle_pdf(inv_id, pdf_path)
        )
        btn_pdf.pack(side="left", padx=2)
        
        # Delete
        btn_del = ctk.CTkButton(
            actions, 
            text="×", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            text_color="red", 
            hover_color="#FFCDD2", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            command=lambda: self.delete_invoice(inv_id)
        )
        btn_del.pack(side="left", padx=2)
        
        # Vijë ndarëse
        line = ctk.CTkFrame(parent, height=1, fg_color=self.bg_secondary)
        line.pack(fill="x", padx=10, pady=0)

    def view_invoice(self, invoice_id):
        """Hap dritaren e detajeve të faturave"""
        pass # Funksioni kryhet tani nga handle_pdf
        
    def edit_invoice(self, invoice_id):
        """Redakton faturave"""
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Redakto Faturën")
        edit_window.geometry("1100x800")
        edit_window.after(100, lambda: edit_window.focus())
        
        form = InvoiceFormView(edit_window, invoice_id=invoice_id)
        form.pack(fill="both", expand=True)
        # Refresh list after closing (simple implementation, usually needs a callback)
    
    def handle_pdf(self, invoice_id, current_path):
        """Menaxhon hapjen ose gjenerimin e PDF"""
        import os # Ensure os is imported here as well
        if current_path and os.path.exists(current_path):
             self.open_pdf(current_path)
        else:
             self.generate_pdf(invoice_id)

    def open_pdf(self, path):
        """Hap PDF ekzistuese"""
        import os # Ensure os is imported here as well
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Gabim", f"Nuk mund të hapet PDF: {e}")

    def generate_pdf(self, invoice_id):
        """Gjeneron PDF për faturave dhe e ruan path-in"""
        invoice = Invoice.get_by_id(invoice_id, self.db)
        if not invoice:
            messagebox.showerror("Gabim", "Fatura nuk u gjet!")
            return
        
        try:
            # Gjenero PDF
            generator = PDFGenerator()
            output_path = generator.generate(invoice)
            
            # Update database with path
            invoice.pdf_path = output_path
            invoice.save()
            
            messagebox.showinfo("Sukses", f"PDF u gjenerua me sukses!")
            
            # Hap automatikisht
            self.open_pdf(output_path)
            
            # Rifresko listen për të update statusin e butonit (opsionale, por mirë për UX)
            # self.load_invoices() # Mund të jetë e rëndë të bëhet reload komplet
            
        except Exception as e:
            messagebox.showerror("Gabim", f"Gabim në gjenerimin e PDF: {str(e)}")
    
    def delete_invoice(self, invoice_id):
        """Fshin faturave"""
        if not messagebox.askyesno("Konfirmim", "A jeni të sigurt që dëshironi të fshini këtë faturë?\nKy veprim nuk mund të kthehet."):
            return
        
        invoice = Invoice.get_by_id(invoice_id, self.db)
        if invoice and invoice.delete():
            messagebox.showinfo("Sukses", "Fatura u fshi me sukses!")
            self.load_invoices()
        else:
            messagebox.showerror("Gabim", "Gabim në fshirjen e faturës!")

