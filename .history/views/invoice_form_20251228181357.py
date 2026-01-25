import os
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
from models.database import Database
from models.invoice import Invoice
from models.client import Client
from models.template import Template
from services.pdf_generator import PDFGenerator
from decimal import Decimal

class InvoiceFormView(ctk.CTkFrame):
    """Formulari për krijimin dhe redaktimin e faturave"""
    
    def __init__(self, parent, invoice_id=None):
        super().__init__(parent, fg_color="#F8F9FA")
        
        # Ngjyrat Premium
        self.primary_color = "#FF6600"
        self.bg_card = "#FFFFFF"
        self.border_color = "#E9ECEF"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        
        # Container me scroll
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True)
        
        self.db = Database()
        self.db.connect()
        
        self.invoice_id = invoice_id
        self.invoice = None
        self.items = []  # Lista e artikujve në formular
        
        if invoice_id:
            self.invoice = Invoice.get_by_id(invoice_id, self.db)
            if not self.invoice:
                messagebox.showerror("Gabim", "Fatura nuk u gjet!")
                return
        
        self.all_client_names = self.get_client_names()
        self.create_widgets()
        
        if self.invoice:
            self.load_invoice_data()
    
    def create_widgets(self):
        """Krijon dritaren e faturimit me dizajnin e ri premium"""
        # 1. Header (Titulli)
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 20))
        
        title_text = "Redakto Faturën" if self.invoice_id else "Krijo Faturë të Re"
        ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
            text_color=self.text_main
        ).pack(side="left")
        
        # 2. Informacione Bazë (Card style)
        self.info_card = ctk.CTkFrame(self.scrollable_frame, fg_color=self.bg_card, corner_radius=15, border_width=1, border_color=self.border_color)
        self.info_card.pack(fill="x", padx=40, pady=10)
        
        info_grid = ctk.CTkFrame(self.info_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=25, pady=20)
        
        # Rreshti i parë: Klienti
        self._add_form_field(info_grid, "Klienti:", 0, 0, is_search=True)
        
        # Container i Sugjerimeve (I fshehur fillimisht rreshtit 1)
        self.suggestions_container = ctk.CTkFrame(info_grid, fg_color="transparent")
        
        # Rreshti i dytë: Pjesa e mbetur (Data, Nr, Afati)
        fields_row = ctk.CTkFrame(info_grid, fg_color="transparent")
        fields_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        self._add_row_field(fields_row, "Data e Faturës:", "date_entry", 0, date.today().strftime("%d.%m.%Y"))
        self._add_row_field(fields_row, "Numri i Faturës:", "invoice_number_entry", 1)
        if not self.invoice_id:
            self.invoice_number_entry.insert(0, Invoice.get_next_invoice_number(self.db))
        self._add_row_field(fields_row, "Afati i Pagesës:", "payment_due_entry", 2)
        
        fields_row.columnconfigure((0,1,2), weight=1)
        info_grid.columnconfigure(1, weight=1)

        # 3. Artikujt (Card style)
        self.items_card = ctk.CTkFrame(self.scrollable_frame, fg_color=self.bg_card, corner_radius=15, border_width=1, border_color=self.border_color)
        self.items_card.pack(fill="both", expand=True, padx=40, pady=20)
        
        items_header = ctk.CTkFrame(self.items_card, fg_color="transparent", height=60)
        items_header.pack(fill="x", padx=25, pady=(15, 5))
        items_header.pack_propagate(False)
        
        ctk.CTkLabel(items_header, text="Artikujt e Faturës", font=ctk.CTkFont(family="Inter", size=18, weight="bold")).pack(side="left")
        
        btn_add = ctk.CTkButton(
            items_header, 
            text="+ Shto Artikull", 
            command=self.add_item_row,
            fg_color="#F1F3F5",
            text_color=self.text_main,
            hover_color="#E9ECEF",
            width=130,
            height=35,
            font=ctk.CTkFont(family="Inter", weight="bold")
        )
        btn_add.pack(side="right")
        
        # Table Header Row
        self.table_main = ctk.CTkFrame(self.items_card, fg_color="transparent")
        self.table_main.pack(fill="both", expand=True, padx=25, pady=(5, 20))
        
        self.table_header = ctk.CTkFrame(self.table_main, fg_color="#F8F9FA", height=45, corner_radius=8)
        self.table_header.pack(fill="x", pady=(0, 10))
        self.table_header.pack_propagate(False)
        
        # Alignment Weights
        self.item_col_weights = [4, 1.5, 1.5, 2, 0.5] # Përshkrimi, Sasia, Çmimi, Nëntotali, X
        for i, weight in enumerate(self.item_col_weights):
            self.table_header.grid_columnconfigure(i, weight=int(weight*10), uniform="icol")
            
        h_text = ["PËRSHKRIMI I ARTIKULLIT", "SASIA (M²)", "ÇMIMI", "NËNTOTALI", ""]
        for i, txt in enumerate(h_text):
            ctk.CTkLabel(
                self.table_header, 
                text=txt, 
                font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                text_color=self.text_secondary,
                anchor="w"
            ).grid(row=0, column=i, padx=15, sticky="w")

        self.items_table_frame = ctk.CTkFrame(self.table_main, fg_color="transparent")
        self.items_table_frame.pack(fill="both", expand=True)
        
        # 4. Summary & Totals (Card style)
        summary_outer = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        summary_outer.pack(fill="x", padx=40, pady=(0, 40))
        
        # Right aligned totals card
        self.totals_card = ctk.CTkFrame(summary_outer, fg_color=self.bg_card, corner_radius=15, border_width=1, border_color=self.border_color, width=400)
        self.totals_card.pack(side="right")
        
        totals_inner = ctk.CTkFrame(self.totals_card, fg_color="transparent")
        totals_inner.pack(padx=25, pady=20)
        
        # Subtotal
        self._add_summary_row(totals_inner, "Nëntotali:", "subtotal_label", 0)
        
        # VAT Input
        vat_row = ctk.CTkFrame(totals_inner, fg_color="transparent")
        vat_row.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        ctk.CTkLabel(vat_row, text="TVSH (%):", font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_secondary).pack(side="left")
        self.vat_percentage_entry = ctk.CTkEntry(vat_row, width=80, height=30, fg_color=self.bg_card, border_color=self.border_color)
        self.vat_percentage_entry.insert(0, "18,00")
        self.vat_percentage_entry.pack(side="right")
        self.vat_percentage_entry.bind("<KeyRelease>", lambda e: self.calculate_totals())
        
        # VAT Amount
        self._add_summary_row(totals_inner, "Shuma TVSH:", "vat_amount_label", 2)
        
        # Grand Total
        ctk.CTkFrame(totals_inner, height=1, fg_color=self.border_color).grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")
        
        ctk.CTkLabel(totals_inner, text="TOTALI PËR PAGESË:", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=self.text_main).grid(row=4, column=0, sticky="w")
        self.total_label = ctk.CTkLabel(totals_inner, text="0,00 €", font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=self.primary_color)
        self.total_label.grid(row=4, column=1, sticky="e", padx=(40, 0))
        
        # Butonat kryesorë (Left aligned)
        btn_main_container = ctk.CTkFrame(summary_outer, fg_color="transparent")
        btn_main_container.pack(side="left", fill="y", anchor="s")
        
        self.btn_save_pdf = ctk.CTkButton(
            summary_outer,
            text="Ruaj & Shfaq PDF",
            command=lambda: self.process_save(show_pdf=True),
            fg_color=self.primary_color,
            hover_color="#E65C00",
            font=ctk.CTkFont(family="Inter", weight="bold"),
            width=180,
            height=45,
            corner_radius=10
        )
        self.btn_save_pdf.pack(side="left", padx=(0, 15), pady=(100, 0))
        
        self.btn_save_only = ctk.CTkButton(
            summary_outer,
            text="Ruaj Vetëm",
            command=lambda: self.process_save(show_pdf=False),
            fg_color="transparent",
            border_width=1,
            border_color=self.border_color,
            text_color=self.text_main,
            hover_color="#FFFFFF",
            width=140,
            height=45,
            corner_radius=10
        )
        self.btn_save_only.pack(side="left", pady=(100, 0))
        
        # Shto një artikull default
        if not self.invoice_id:
            self.add_item_row()
    
    def _add_form_field(self, parent, label, row, col, is_search=False):
        """Shton një fushë në grid-in e informacionit"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=col, sticky="ew", padx=10)
        
        ctk.CTkLabel(container, text=label, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), text_color=self.text_main).pack(anchor="w")
        
        if is_search:
            self.client_var = ctk.StringVar()
            self.client_entry = ctk.CTkEntry(
                container, 
                textvariable=self.client_var,
                placeholder_text="Kërko klientin...",
                height=40,
                fg_color=self.bg_card,
                border_color=self.border_color,
                corner_radius=8
            )
            self.client_entry.pack(fill="x", pady=(5, 0))
            self.client_entry.bind("<KeyRelease>", self.on_client_search)
            self.client_entry.bind("<Button-1>", self.on_client_click)
            self.client_entry.bind("<FocusOut>", lambda e: self.after(200, self.hide_suggestions))
            
            # Klient i ri button
            btn_new = ctk.CTkButton(
                parent, text="Klient i ri", command=self.open_new_client, 
                width=100, height=35, fg_color="transparent", border_width=1, 
                text_color=self.primary_color, border_color=self.primary_color, hover_color="#FFF4ED"
            )
            btn_new.grid(row=row, column=2, padx=10, sticky="s", pady=(0, 2))

    def _add_row_field(self, parent, label, attr_name, col, default=""):
        """Shton një fushë në rreshtin e dytë të të dhënave"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=0, column=col, padx=10, sticky="ew")
        
        ctk.CTkLabel(container, text=label, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), text_color=self.text_main).pack(anchor="w")
        entry = ctk.CTkEntry(container, height=38, fg_color=self.bg_card, border_color=self.border_color, corner_radius=8)
        if default: entry.insert(0, default)
        entry.pack(fill="x", pady=(5, 0))
        setattr(self, attr_name, entry)

    def _add_summary_row(self, parent, label, attr_name, row):
        """Shton një rresht në përmbledhjen e çmimeve"""
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(family="Inter", size=13), text_color=self.text_secondary).grid(row=row, column=0, sticky="w", pady=5)
        lbl = ctk.CTkLabel(parent, text="0,00 €", font=ctk.CTkFont(family="Inter", size=14, weight="bold"), text_color=self.text_main)
        lbl.grid(row=row, column=1, sticky="e", padx=(40, 0))
        setattr(self, attr_name, lbl)
    
    def get_client_names(self):
        """Merr listën e emrave të klientëve"""
        clients = Client.get_all(self.db)
        return [f"{c['name']} ({c['unique_number']})" for c in clients]
    
    def refresh_clients(self):
        """Përditëson listën e klientëve"""
        self.all_client_names = self.get_client_names()
    
    def on_client_click(self, event):
        """Shfaq të gjithë klientët kur klikohet fusha"""
        self.show_suggestions(self.all_client_names)
    
    def on_client_search(self, event):
        """Kërkimi live dhe shfaqja e sugjerimeve"""
        search_term = self.client_var.get().lower()
        
        # Filtro emrat
        matches = [name for name in self.all_client_names if search_term in name.lower()]
        
        if matches:
            self.show_suggestions(matches)
        elif not search_term:
            self.show_suggestions(self.all_client_names)
        else:
            self.hide_suggestions()

    def show_suggestions(self, matches):
        """Shfaq listën e sugjerimeve direkt nën fushën e klientit"""
        # Pastrimi
        for widget in self.suggestions_container.winfo_children():
            widget.destroy()

        # Vendose në grid në rreshtin 1 të info_frame
        self.suggestions_container.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))
        
        # Scrollable area e thjeshtë
        results_frame = ctk.CTkScrollableFrame(
            self.suggestions_container, 
            height=120, 
            fg_color="#FFFFFF", 
            border_width=1, 
            border_color="#E0E0E0",
            corner_radius=8
        )
        results_frame.pack(fill="x")
        
        # Shto sugjerimet
        for name in matches:
            parts = name.split(" (")
            main_name = parts[0]
            unique_no = parts[1].replace(")", "") if len(parts) > 1 else ""
            
            # Container për secilin rresht
            item_frame = ctk.CTkFrame(results_frame, fg_color="transparent", height=40, cursor="hand2")
            item_frame.pack(fill="x", pady=1, padx=2)
            item_frame.pack_propagate(False)
            
            # Hover effect
            def on_enter(e, f=item_frame): f.configure(fg_color="#F5F7FB")
            def on_leave(e, f=item_frame): f.configure(fg_color="transparent")
            
            item_frame.bind("<Enter>", on_enter)
            item_frame.bind("<Leave>", on_leave)
            
            # Detajet
            lbl_text = f"👤 {main_name}"
            if unique_no: lbl_text += f" ({unique_no})"
            
            lbl = ctk.CTkLabel(
                item_frame, 
                text=lbl_text, 
                font=ctk.CTkFont(family="Inter", size=13), 
                text_color="#2C3E50"
            )
            lbl.pack(side="left", padx=15)
            
            # Veprimi i përzgjedhjes
            def on_click(e, n=name): self.select_client(n)
            item_frame.bind("<Button-1>", on_click)
            lbl.bind("<Button-1>", on_click)

    def hide_suggestions(self):
        """Fsheh listën e sugjerimeve"""
        if hasattr(self, 'suggestions_container'):
            self.suggestions_container.grid_forget()

    def select_client(self, name):
        """Zgjedh klientin dhe mbyll sugjerimet"""
        self.client_var.set(name)
        self.hide_suggestions()
        # Fokus automatik te fusha tjetër
        self.date_entry.focus_set()
    
    def open_new_client(self):
        """Hap dritaren për klient të ri"""
        from views.client_manager import ClientManagerView
        # Hap dritare të re për klient të ri
        client_window = ctk.CTkToplevel(self)
        client_window.title("Klient i ri")
        client_window.geometry("800x600")
        
        client_view = ClientManagerView(client_window)
        client_view.pack(fill="both", expand=True)
        
        # Përditëso listën e klientëve pas mbylljes së dritares
        client_window.protocol("WM_DELETE_WINDOW", lambda: (client_window.destroy(), self.refresh_clients()))
    
    def add_item_row(self):
        """Shton një rresht të ri artikulli me alinjim perfekt"""
        row_id = len(self.items) + 1
        
        row_frame = ctk.CTkFrame(self.items_table_frame, fg_color="transparent", height=50)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        # Alinjimi me header-in
        for i, weight in enumerate(self.item_col_weights):
            row_frame.grid_columnconfigure(i, weight=int(weight*10), uniform="icol")
            
        # Përshkrimi
        desc_entry = ctk.CTkEntry(row_frame, height=35, fg_color=self.bg_card, border_color="#E0E0E0", corner_radius=6, placeholder_text="Emri i produktit/shërbimit...")
        desc_entry.grid(row=0, column=0, padx=10, sticky="ew")
        
        # Sasia
        qty_entry = ctk.CTkEntry(row_frame, height=35, fg_color=self.bg_card, border_color="#E0E0E0", corner_radius=6, justify="center")
        qty_entry.insert(0, "1")
        qty_entry.grid(row=0, column=1, padx=10, sticky="ew")
        qty_entry.bind("<KeyRelease>", lambda e, r=row_id: self.update_item_subtotal(r))
        
        # Çmimi
        price_entry = ctk.CTkEntry(row_frame, height=35, fg_color=self.bg_card, border_color="#E0E0E0", corner_radius=6, justify="center")
        price_entry.insert(0, "0")
        price_entry.grid(row=0, column=2, padx=10, sticky="ew")
        price_entry.bind("<KeyRelease>", lambda e, r=row_id: self.update_item_subtotal(r))
        
        # Nëntotali
        subtotal_label = ctk.CTkLabel(row_frame, text="0,00 €", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=self.text_main, anchor="w")
        subtotal_label.grid(row=0, column=3, padx=15, sticky="w")
        
        # Butoni fshirje
        btn_del = ctk.CTkButton(
            row_frame, text="✕", width=30, height=30, fg_color="#FFF0F0", text_color="#E74C3C",
            hover_color="#FFE5E5", corner_radius=6, command=lambda r=row_id: self.remove_item_row(r)
        )
        btn_del.grid(row=0, column=4, padx=5)
        
        # Ruaj referencat
        self.items.append({
            'row': row_id,
            'container': row_frame,
            'desc_entry': desc_entry,
            'qty_entry': qty_entry,
            'price_entry': price_entry,
            'subtotal_label': subtotal_label,
            'btn_delete': btn_del
        })
        
        desc_entry.focus_set()
    
    def remove_item_row(self, row_id):
        """Heq një rresht artikulli me pastrim të plotë"""
        item = next((i for i in self.items if i['row'] == row_id), None)
        if item:
            item['container'].destroy()
            self.items.remove(item)
            self.calculate_totals()
    
    def update_item_subtotal(self, row):
        """Përditëson nëntotalin e një artikulli"""
        item = next((i for i in self.items if i['row'] == row), None)
        if item:
            try:
                qty = float(item['qty_entry'].get().replace(",", "."))
                price = float(item['price_entry'].get().replace(",", "."))
                subtotal = qty * price
                item['subtotal_label'].configure(text=f"{subtotal:,.2f}".replace(",", " ").replace(".", ","))
            except:
                item['subtotal_label'].configure(text="0,00")
            
            self.calculate_totals()
    
    def calculate_totals(self):
        """Llogarit totalet me simbolin e euros"""
        subtotal = 0
        for item in self.items:
            try:
                qty = float(item['qty_entry'].get().replace(",", "."))
                price = float(item['price_entry'].get().replace(",", "."))
                subtotal += qty * price
            except:
                pass
        
        self.subtotal_label.configure(text=f"{subtotal:,.2f} €".replace(",", " "))
        
        # TVSH
        try:
            vat_p_str = self.vat_percentage_entry.get().replace(",", ".")
            vat_percentage = float(vat_p_str) if vat_p_str else 0
            vat_amount = subtotal * (vat_percentage / 100)
            total = subtotal + vat_amount
            
            self.vat_amount_label.configure(text=f"{vat_amount:,.2f} €".replace(",", " "))
            self.total_label.configure(text=f"{total:,.2f} €".replace(",", " "))
        except:
            self.vat_amount_label.configure(text="0,00 €")
            self.total_label.configure(text=f"{subtotal:,.2f} €".replace(",", " "))
    
    def load_invoice_data(self):
        """Ngarkon të dhënat e faturave për redaktim"""
        if not self.invoice:
            return
        
        # Klienti
        client = Client.get_by_id(self.invoice.client_id, self.db)
        if client:
            client_text = f"{client.name} ({client.unique_number})"
            self.client_var.set(client_text)
        
        # Data
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, self.invoice.date.strftime("%d.%m.%Y") if self.invoice.date else "")
        
        # Numri i faturave
        self.invoice_number_entry.delete(0, "end")
        self.invoice_number_entry.insert(0, self.invoice.invoice_number)
        
        # Afati i pagesës
        self.payment_due_entry.delete(0, "end")
        if self.invoice.payment_due_date:
            self.payment_due_entry.insert(0, self.invoice.payment_due_date.strftime("%d.%m.%Y"))
        
        # TVSH %
        self.vat_percentage_entry.delete(0, "end")
        self.vat_percentage_entry.insert(0, f"{float(self.invoice.vat_percentage):.2f}".replace(".", ","))
        
        # Artikujt
        for item in self.invoice.items:
            self.add_item_row()
            last_item = self.items[-1]
            last_item['desc_entry'].insert(0, item['description'])
            last_item['qty_entry'].delete(0, "end")
            last_item['qty_entry'].insert(0, f"{float(item['quantity']):,.2f}".replace(",", " ").replace(".", ","))
            last_item['price_entry'].delete(0, "end")
            last_item['price_entry'].insert(0, f"{float(item['unit_price']):,.2f}".replace(",", " ").replace(".", ","))
            self.update_item_subtotal(last_item['row'])
        
        self.calculate_totals()
    
    def get_invoice_data(self):
        """Merr të dhënat nga formularit"""
        # Klienti
        client_text = self.client_var.get()
        if not client_text:
            return None
        
        # Gjej ID-në e klientit
        client_name = client_text.split(" (")[0]
        clients = Client.get_all(self.db)
        client_id = None
        for c in clients:
            if c['name'] == client_name:
                client_id = c['id']
                break
        
        if not client_id:
            messagebox.showerror("Gabim", "Ju lutem zgjidhni një klient!")
            return None
        
        # Data
        try:
            invoice_date = datetime.strptime(self.date_entry.get(), "%d.%m.%Y").date()
        except:
            messagebox.showerror("Gabim", "Data nuk është në format të saktë (dd.mm.yyyy)")
            return None
        
        # Numri i faturave
        invoice_number = self.invoice_number_entry.get()
        if not invoice_number:
            messagebox.showerror("Gabim", "Ju lutem shkruani numrin e faturave!")
            return None
        
        # Afati i pagesës
        payment_due_date = None
        if self.payment_due_entry.get():
            try:
                payment_due_date = datetime.strptime(self.payment_due_entry.get(), "%d.%m.%Y").date()
            except:
                messagebox.showerror("Gabim", "Afati i pagesës nuk është në format të saktë")
                return None
        
        # Artikujt
        items = []
        for item in self.items:
            desc = item['desc_entry'].get()
            if not desc:
                continue
            
            try:
                qty = float(item['qty_entry'].get().replace(",", "."))
                price = float(item['price_entry'].get().replace(",", "."))
                if qty > 0 and price > 0:
                    items.append({
                        'description': desc,
                        'quantity': qty,
                        'unit_price': price
                    })
            except:
                continue
        
        if not items:
            messagebox.showerror("Gabim", "Ju lutem shtoni të paktën një artikull!")
            return None
        
        # TVSH %
        try:
            vat_percentage = float(self.vat_percentage_entry.get().replace(",", "."))
        except:
            vat_percentage = 18.0
        
        # Krijoni objektin Invoice
        invoice = Invoice(self.db)
        if self.invoice_id:
            invoice.id = self.invoice_id
        
        invoice.invoice_number = invoice_number
        invoice.date = invoice_date
        invoice.payment_due_date = payment_due_date
        invoice.client_id = client_id
        invoice.vat_percentage = Decimal(str(vat_percentage))
        
        # Shto artikujt
        for item_data in items:
            invoice.add_item(
                item_data['description'],
                item_data['quantity'],
                item_data['unit_price']
            )
        
        return invoice
    
    def process_save(self, show_pdf=False):
        """Procesi i unifikuar i ruajtjes dhe gjenerimit të PDF"""
        invoice = self.get_invoice_data()
        if not invoice:
            return
        
        # Vendos statusin default si 'sent' pasi tani procesi është i shpejtë
        invoice.status = 'sent'
        
        if invoice.save():
            self.invoice_id = invoice.id
            try:
                # 1. Gjenero PDF
                generator = PDFGenerator()
                output_path = generator.generate(invoice)
                
                # 2. Ruaj rrugën e PDF në databazë
                invoice.pdf_path = output_path
                invoice.save() 
                
                # 3. Hap PDF nëse kërkohet
                if show_pdf:
                    os.startfile(output_path)
                    messagebox.showinfo("Sukses", "Fatura u ruajt dhe PDF u shfaq!")
                else:
                    messagebox.showinfo("Sukses", "Fatura u ruajt dhe PDF u krijua me sukses!")
                
                # Opcionale: Kthehu te lista ose pastro formularin
            except Exception as e:
                messagebox.showerror("Gabim", f"Fatura u ruajt, por gabim në PDF: {str(e)}")
        else:
            messagebox.showerror("Gabim", "Gabim në ruajtjen e faturës!")
