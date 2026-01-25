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
        super().__init__(parent, fg_color="transparent")
        
        # Container me scroll vetëm për përmbajtjen
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
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
        """Krijon widget-et e formularit"""
        # Titulli
        title_text = "Redakto Fatura" if self.invoice_id else "Fatura e re"
        title = ctk.CTkLabel(
            self.scrollable_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Frame për informacione bazë
        info_frame = ctk.CTkFrame(self.scrollable_frame)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        # Klienti (Searchable Entry)
        ctk.CTkLabel(info_frame, text="Klienti:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.client_var = ctk.StringVar()
        
        self.client_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.client_var,
            placeholder_text="Shkruaj emrin për të kërkuar klientin...",
            width=300,
            height=35
        )
        self.client_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.client_entry.bind("<KeyRelease>", self.on_client_search)
        self.client_entry.bind("<Button-1>", self.on_client_click)
        self.client_entry.bind("<FocusOut>", lambda e: self.after(200, self.hide_suggestions))
        
        # Sugjerimet (Hidden initialy)
        self.suggestions_frame = None 
        
        btn_new_client = ctk.CTkButton(
            info_frame,
            text="Klient i ri",
            command=self.open_new_client,
            width=120,
            height=35
        )
        btn_new_client.grid(row=0, column=2, padx=10, pady=10)
        
        info_frame.grid_columnconfigure(1, weight=1)
        
        # 2b. Container i Sugjerimeve (Integrim në layout i fshehur fillimisht)
        self.suggestions_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        
        # Data (Zhvendoset në row 2)
        ctk.CTkLabel(info_frame, text="Data:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.date_entry = ctk.CTkEntry(info_frame, width=200)
        self.date_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        self.date_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        # Numri i faturave (row 3)
        ctk.CTkLabel(info_frame, text="Fatura Nr.:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.invoice_number_entry = ctk.CTkEntry(info_frame, width=200)
        if not self.invoice_id:
            self.invoice_number_entry.insert(0, Invoice.get_next_invoice_number(self.db))
        self.invoice_number_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        # Afati i pagesës (row 4)
        ctk.CTkLabel(info_frame, text="Afati pageses:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.payment_due_entry = ctk.CTkEntry(info_frame, width=200)
        self.payment_due_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        
        # Frame për artikujt
        items_frame = ctk.CTkFrame(self.scrollable_frame)
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Titulli i artikujve
        items_title = ctk.CTkLabel(
            items_frame,
            text="Artikujt",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        items_title.pack(pady=10)
        
        # Butoni për shtim artikulli
        btn_add_item = ctk.CTkButton(
            items_frame,
            text="+ Shto Artikull",
            command=self.add_item_row,
            width=150
        )
        btn_add_item.pack(pady=10)
        
        # Frame për tabelën e artikujve
        self.items_table_frame = ctk.CTkFrame(items_frame)
        self.items_table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header i tabelës
        headers = ["Përshkrimi", "Sasia (m²)", "Çmimi", "Nëntotali", ""]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.items_table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.items_table_frame.grid_columnconfigure(i, weight=1 if i < 3 else 0)
        
        # Frame për totalet
        totals_frame = ctk.CTkFrame(self.scrollable_frame)
        totals_frame.pack(fill="x", padx=20, pady=10)
        
        # Total pa TVSH
        ctk.CTkLabel(totals_frame, text="Total pa TVSH:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.subtotal_label = ctk.CTkLabel(totals_frame, text="0,00", font=ctk.CTkFont(size=14))
        self.subtotal_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # TVSH %
        ctk.CTkLabel(totals_frame, text="TVSH %:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.vat_percentage_entry = ctk.CTkEntry(totals_frame, width=100)
        self.vat_percentage_entry.insert(0, "18,00")
        self.vat_percentage_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.vat_percentage_entry.bind("<KeyRelease>", lambda e: self.calculate_totals())
        
        # Shuma TVSH
        ctk.CTkLabel(totals_frame, text="Shuma TVSH:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.vat_amount_label = ctk.CTkLabel(totals_frame, text="0,00", font=ctk.CTkFont(size=14))
        self.vat_amount_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Total për pagesë
        ctk.CTkLabel(totals_frame, text="Total për pagesë:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.total_label = ctk.CTkLabel(totals_frame, text="0,00", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FF6600")
        self.total_label.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        # Butonat
        buttons_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        btn_save = ctk.CTkButton(
            buttons_frame,
            text="Ruaj",
            command=lambda: self.process_save(show_pdf=False),
            width=180,
            height=45,
            fg_color="#3498DB",
            hover_color="#2980B9",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn_save.pack(side="left", padx=10)
        
        btn_save_and_pdf = ctk.CTkButton(
            buttons_frame,
            text="Ruaj dhe shfaq PDF",
            command=lambda: self.process_save(show_pdf=True),
            width=220,
            height=45,
            fg_color="#28a745",
            hover_color="#218838",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn_save_and_pdf.pack(side="left", padx=10)
        
        # Shto një artikull default
        if not self.invoice_id:
            self.add_item_row()
    
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
        """Shton një rresht të ri për artikull"""
        row = len(self.items) + 1
        
        # Përshkrimi
        desc_entry = ctk.CTkEntry(self.items_table_frame, width=300)
        desc_entry.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        
        # Sasia
        qty_entry = ctk.CTkEntry(self.items_table_frame, width=100)
        qty_entry.insert(0, "0")
        qty_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        qty_entry.bind("<KeyRelease>", lambda e, r=row: self.update_item_subtotal(r))
        
        # Çmimi
        price_entry = ctk.CTkEntry(self.items_table_frame, width=100)
        price_entry.insert(0, "0")
        price_entry.grid(row=row, column=2, padx=5, pady=5, sticky="ew")
        price_entry.bind("<KeyRelease>", lambda e, r=row: self.update_item_subtotal(r))
        
        # Nëntotali
        subtotal_label = ctk.CTkLabel(self.items_table_frame, text="0,00", width=100)
        subtotal_label.grid(row=row, column=3, padx=5, pady=5, sticky="ew")
        
        # Butoni për fshirje
        btn_delete = ctk.CTkButton(
            self.items_table_frame,
            text="X",
            width=30,
            height=30,
            command=lambda r=row: self.remove_item_row(r),
            fg_color="red",
            hover_color="darkred"
        )
        btn_delete.grid(row=row, column=4, padx=5, pady=5)
        
        # Ruaj referencat
        self.items.append({
            'row': row,
            'desc_entry': desc_entry,
            'qty_entry': qty_entry,
            'price_entry': price_entry,
            'subtotal_label': subtotal_label,
            'btn_delete': btn_delete
        })
    
    def remove_item_row(self, row):
        """Heq një rresht artikulli"""
        item = next((i for i in self.items if i['row'] == row), None)
        if item:
            # Fshi widget-et
            item['desc_entry'].destroy()
            item['qty_entry'].destroy()
            item['price_entry'].destroy()
            item['subtotal_label'].destroy()
            item['btn_delete'].destroy()
            
            # Heq nga lista
            self.items.remove(item)
            
            # Rishiko totalet
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
        """Llogarit totalet"""
        subtotal = 0
        for item in self.items:
            try:
                qty = float(item['qty_entry'].get().replace(",", "."))
                price = float(item['price_entry'].get().replace(",", "."))
                subtotal += qty * price
            except:
                pass
        
        self.subtotal_label.configure(text=f"{subtotal:,.2f}".replace(",", " ").replace(".", ","))
        
        # TVSH
        try:
            vat_percentage = float(self.vat_percentage_entry.get().replace(",", "."))
            vat_amount = subtotal * (vat_percentage / 100)
            total = subtotal + vat_amount
            
            self.vat_amount_label.configure(text=f"{vat_amount:,.2f}".replace(",", " ").replace(".", ","))
            self.total_label.configure(text=f"{total:,.2f}".replace(",", " ").replace(".", ","))
        except:
            self.vat_amount_label.configure(text="0,00")
            self.total_label.configure(text=f"{subtotal:,.2f}".replace(",", " ").replace(".", ","))
    
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
