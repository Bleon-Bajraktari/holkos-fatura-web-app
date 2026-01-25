"""
Formulari i Ofertës
"""
import os
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
from models.database import Database
from models.offer import Offer
from models.client import Client
from services.pdf_generator import PDFGenerator
from decimal import Decimal

class OfferFormView(ctk.CTkFrame):
    def __init__(self, parent, offer_id=None):
        super().__init__(parent, fg_color="#F8F9FA")
        
        self.primary_color = "#FF6600"
        self.bg_card = "#FFFFFF"
        self.border_color = "#E9ECEF"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True)
        
        self.db = Database()
        self.db.connect()
        
        self.offer_id = offer_id
        self.offer = None
        self.items = []  
        
        if offer_id:
            self.offer = Offer.get_by_id(offer_id, self.db)
            if not self.offer:
                messagebox.showerror("Gabim", "Oferta nuk u gjet!")
                return
        
        self.all_client_names = self.get_client_names()
        self.create_widgets()
        
        if self.offer:
            self.load_offer_data()
    
    def create_widgets(self):
        # 1. Header
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title_text = "Redakto Ofertën" if self.offer_id else "Krijo Ofertë të Re"
        ctk.CTkLabel(header_frame, text=title_text, font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=self.text_main).pack(side="left")
        
        # 2. Informacione Bazë
        self.info_card = ctk.CTkFrame(self.scrollable_frame, fg_color=self.bg_card, corner_radius=12, border_width=1, border_color=self.border_color)
        self.info_card.pack(fill="x", padx=30, pady=5)
        
        info_grid = ctk.CTkFrame(self.info_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=20, pady=15)
        
        self._add_form_field(info_grid, "Klienti:", 0, 0, is_search=True)
        
        fields_row = ctk.CTkFrame(info_grid, fg_color="transparent")
        fields_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        
        self._add_row_field(fields_row, "Data e Ofertës:", "date_entry", 0, date.today().strftime("%d.%m.%Y"))
        self._add_row_field(fields_row, "Numri i Ofertës:", "offer_number_entry", 1)
        if not self.offer_id:
            self.offer_number_entry.insert(0, Offer.get_next_offer_number(self.db))
        
        # Subject Row
        subject_row = ctk.CTkFrame(info_grid, fg_color="transparent")
        subject_row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self._add_row_field(subject_row, "Titulli / Subjekti i Ofertës:", "subject_entry", 0)
        
        fields_row.columnconfigure((0,1), weight=1)
        subject_row.columnconfigure(0, weight=1)
        info_grid.columnconfigure(0, weight=4)

        # Main Content Area (Rows Container)
        self.rows_container = ctk.CTkScrollableFrame(self.scrollable_frame, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header for the Rows
        header_frame = ctk.CTkFrame(self.rows_container, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Përshkrimi i Ofertës/Artikullit", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.text_secondary).pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="Kalkulimet (Sasia x Njësia x Çmimi)", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.text_secondary).pack(side="right", padx=150)
        
        # Add Button
        ctk.CTkButton(self.scrollable_frame, text="+ Shto Rresht te Ri", command=self.add_aligned_row, fg_color="#F1F3F5", text_color=self.text_main, hover_color="#E9ECEF", width=150, height=32, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), cursor="hand2").pack(pady=(0, 20))

        # Action Buttons
        actions_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        actions_frame.pack(side="right", anchor="e", padx=30, pady=20)

        self.btn_save_only = ctk.CTkButton(actions_frame, text="Ruaj", command=lambda: self.process_save(action='save'), fg_color="#34495E", hover_color="#2C3E50", text_color="#FFFFFF", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), width=100, height=38, corner_radius=8, cursor="hand2")
        self.btn_save_only.pack(side="left", padx=5)

        self.btn_save_pdf = ctk.CTkButton(actions_frame, text="Ruaj & PDF", command=lambda: self.process_save(action='pdf'), fg_color=self.primary_color, hover_color="#E65C00", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), width=120, height=38, corner_radius=8, cursor="hand2")
        self.btn_save_pdf.pack(side="left", padx=5)
        
        if not self.offer_id: self.add_aligned_row()
    
    def _add_form_field(self, parent, label, row, col, is_search=False):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=col, sticky="ew", padx=10)
        ctk.CTkLabel(container, text=label, font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=self.text_main).pack(anchor="w")
        if is_search:
            self.client_var = ctk.StringVar()
            self.client_entry = ctk.CTkEntry(container, textvariable=self.client_var, placeholder_text="Kërko...", height=32, fg_color="#FBFBFB", border_color=self.border_color, corner_radius=8, font=ctk.CTkFont(size=12))
            self.client_entry.pack(fill="x", pady=(3, 0))
            self.client_entry.bind("<KeyRelease>", self.on_client_search)
            self.client_entry.bind("<Button-1>", self.on_client_click)
            self.client_entry.bind("<FocusOut>", lambda e: self.after(200, self.hide_suggestions))
            self.suggestions_container = ctk.CTkFrame(container, fg_color="transparent")
            ctk.CTkButton(parent, text="Klient i ri", command=self.open_new_client, width=80, height=32, fg_color="transparent", border_width=1, text_color=self.primary_color, border_color=self.primary_color, hover_color="#FFF4ED", font=ctk.CTkFont(size=11, weight="bold"), cursor="hand2").grid(row=row, column=2, padx=10, sticky="s", pady=(0, 1))

    def _add_row_field(self, parent, label, attr_name, col, default=""):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=0, column=col, padx=8, sticky="ew")
        ctk.CTkLabel(container, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color=self.text_main).pack(anchor="w")
        entry = ctk.CTkEntry(container, height=32, font=ctk.CTkFont(size=12), fg_color=self.bg_card, border_color=self.border_color, corner_radius=8)
        if default: entry.insert(0, default)
        entry.pack(fill="x", pady=(2, 0))
        setattr(self, attr_name, entry)
    
    def get_client_names(self):
        clients = Client.get_all(self.db)
        return [f"{c['name']} ({c['unique_number']})" for c in clients]
    
    def refresh_clients(self): self.all_client_names = self.get_client_names()
    def on_client_click(self, event): self.show_suggestions(self.all_client_names)
    def on_client_search(self, event):
        search_term = self.client_var.get().lower()
        matches = [name for name in self.all_client_names if search_term in name.lower()]
        if matches: self.show_suggestions(matches)
        elif not search_term: self.show_suggestions(self.all_client_names)
        else: self.hide_suggestions()

    def show_suggestions(self, matches):
        for widget in self.suggestions_container.winfo_children(): widget.destroy()
        self.suggestions_container.pack(fill="x", pady=(2, 0))
        results_frame = ctk.CTkScrollableFrame(self.suggestions_container, height=min(len(matches) * 38, 150), fg_color="#FFFFFF", border_width=1, border_color=self.border_color, corner_radius=8)
        results_frame.pack(fill="x")
        for name in matches:
            parts = name.split(" ("); main_name = parts[0]; unique_no = parts[1].replace(")", "") if len(parts) > 1 else ""
            item_frame = ctk.CTkFrame(results_frame, fg_color="transparent", height=35, cursor="hand2")
            item_frame.pack(fill="x", pady=1); item_frame.pack_propagate(False)
            def on_enter(e, f=item_frame): f.configure(fg_color="#F8F9FA")
            def on_leave(e, f=item_frame): f.configure(fg_color="transparent")
            item_frame.bind("<Enter>", on_enter); item_frame.bind("<Leave>", on_leave)
            display_text = f"  👤  {main_name}"
            if unique_no: display_text += f" • {unique_no}"
            lbl = ctk.CTkLabel(item_frame, text=display_text, font=ctk.CTkFont(size=12), text_color=self.text_main, anchor="w")
            lbl.pack(side="left", fill="both", expand=True, padx=8)
            def on_click(e, n=name): self.select_client(n)
            item_frame.bind("<Button-1>", on_click); lbl.bind("<Button-1>", on_click)

    def hide_suggestions(self): self.suggestions_container.pack_forget()
    def select_client(self, name): self.client_var.set(name); self.hide_suggestions(); self.date_entry.focus_set()
    
    def open_new_client(self):
        from views.client_manager import ClientManagerView
        client_window = ctk.CTkToplevel(self); client_window.title("Shto Klient"); client_window.geometry("850x600")
        client_window.transient(self.winfo_toplevel()); client_window.grab_set(); client_window.focus_set()
        client_window.after(10, lambda: client_window.lift())
        client_view = ClientManagerView(client_window); client_view.pack(fill="both", expand=True)
        client_window.protocol("WM_DELETE_WINDOW", lambda: (client_window.grab_release(), client_window.destroy(), self.refresh_clients()))
    
    def add_aligned_row(self):
        row_id = len(self.items) + 1
        
        # Main row container
        row_frame = ctk.CTkFrame(self.rows_container, fg_color=self.bg_card, corner_radius=8, border_width=1, border_color=self.border_color)
        row_frame.pack(fill="x", pady=5, padx=5)
        
        # Grid layout for the row
        row_frame.columnconfigure(0, weight=3) # Description
        row_frame.columnconfigure(1, weight=1) # Calculations
        
        # Left Side: Description Textbox
        desc_text = ctk.CTkTextbox(row_frame, height=80, font=ctk.CTkFont(size=12), fg_color="#FBFBFB", border_width=0, corner_radius=6)
        desc_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Right Side: Calculations
        calc_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        calc_frame.grid(row=0, column=1, sticky="ne", padx=10, pady=10)
        
        # Inputs: Qty, Unit, Price
        # Unit
        unit_entry = ctk.CTkEntry(calc_frame, width=50, height=28, font=ctk.CTkFont(size=11), placeholder_text="m2")
        unit_entry.pack(side="left", padx=2)
        unit_entry.insert(0, "m2")
        
        # Qty
        qty_entry = ctk.CTkEntry(calc_frame, width=50, height=28, font=ctk.CTkFont(size=11), placeholder_text="Sasia")
        qty_entry.pack(side="left", padx=2)
        
        # Price
        price_entry = ctk.CTkEntry(calc_frame, width=60, height=28, font=ctk.CTkFont(size=11), placeholder_text="Çmimi")
        price_entry.pack(side="left", padx=2)
        
        # Subtotal (hidden calc mostly, but shown for ref)
        subtotal_label = ctk.CTkLabel(calc_frame, text="0.00 €", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.primary_color)
        subtotal_label.pack(side="left", padx=5)
        
        # Delete Button
        ctk.CTkButton(row_frame, text="✕", width=25, height=25, fg_color="transparent", text_color="#E74C3C", hover_color="#FFF0F0", command=lambda r=row_id: self.remove_item_row(r)).grid(row=0, column=2, sticky="ne", padx=5, pady=5)
        
        # Bindings
        def update_sub(e):
            try:
                q = float(qty_entry.get().replace(",", "."))
                p = float(price_entry.get().replace(",", "."))
                subtotal_label.configure(text=f"{q*p:,.2f} €".replace(",", " "))
            except:
                subtotal_label.configure(text="0,00 €")
        
        qty_entry.bind("<KeyRelease>", update_sub)
        price_entry.bind("<KeyRelease>", update_sub)
        
        self.items.append({
            'row': row_id, 'container': row_frame,
            'desc_text': desc_text, # Using textbox for description now
            'unit_entry': unit_entry,
            'qty_entry': qty_entry, 
            'price_entry': price_entry,
            'subtotal_label': subtotal_label
        })
        desc_text.focus_set()

    def remove_item_row(self, row_id):
        item = next((i for i in self.items if i['row'] == row_id), None)
        if item: item['container'].destroy(); self.items.remove(item)
    
    def load_offer_data(self):
        if not self.offer: return
        client = Client.get_by_id(self.offer.client_id, self.db)
        if client: self.client_var.set(f"{client.name} ({client.unique_number})")
        
        self.date_entry.delete(0, "end"); self.date_entry.insert(0, self.offer.date.strftime("%d.%m.%Y") if self.offer.date else "")
        self.offer_number_entry.delete(0, "end"); self.offer_number_entry.insert(0, self.offer.offer_number)
        self.subject_entry.delete(0, "end"); self.subject_entry.insert(0, self.offer.subject or "")
        
        # Offer items now hold the description text for each row
        for item in self.offer.items:
            self.add_aligned_row(); last_item = self.items[-1]
            last_item['desc_text'].insert("0.0", item['description'])
            last_item['unit_entry'].delete(0, "end"); last_item['unit_entry'].insert(0, item['unit'])
            last_item['qty_entry'].delete(0, "end"); last_item['qty_entry'].insert(0, f"{float(item['quantity']):,.2f}".replace(",", " ").replace(".", ","))
            last_item['price_entry'].delete(0, "end"); last_item['price_entry'].insert(0, f"{float(item['unit_price']):,.2f}".replace(",", " ").replace(".", ","))
            # Trigger update
            try:
                q = float(item['quantity'])
                p = float(item['unit_price'])
                last_item['subtotal_label'].configure(text=f"{q*p:,.2f} €".replace(",", " "))
            except: pass

    def get_offer_data(self):
        client_text = self.client_var.get()
        if not client_text: return None
        client_name = client_text.split(" (")[0]; clients = Client.get_all(self.db); client_id = next((c['id'] for c in clients if c['name'] == client_name), None)
        if not client_id:
            self.client_entry.configure(border_color="#E74C3C"); messagebox.showerror("Gabim", "Zgjidhni klientin!")
            return None
        self.client_entry.configure(border_color=self.border_color)
        
        try: date_obj = datetime.strptime(self.date_entry.get(), "%d.%m.%Y").date()
        except: messagebox.showerror("Gabim", "Data gabim!"); return None
        
        offer_number = self.offer_number_entry.get()
        subject = self.subject_entry.get()
        if not offer_number: messagebox.showerror("Gabim", "Nr ofertës!"); return None
        
        items = []
        for item in self.items:
            desc = item['desc_text'].get("0.0", "end").strip()
            # If both desc and numbers are empty/zero, skip?
            # User might want just text, or just numbers.
            # If desc is present, we keep it. Use 0 for numbers if empty.
            
            qty_val = item['qty_entry'].get()
            price_val = item['price_entry'].get()
            
            if not desc and not qty_val and not price_val: continue

            try:
                qty = float(qty_val.replace(",", ".")) if qty_val else 0.0
                price = float(price_val.replace(",", ".")) if price_val else 0.0
                unit = item['unit_entry'].get()
                items.append({'description': desc, 'unit': unit, 'quantity': qty, 'unit_price': price})
            except: 
                # If numbers fail but desc exists, save with 0s
                if desc:
                    items.append({'description': desc, 'unit': "", 'quantity': 0, 'unit_price': 0})
                continue
        
        if not items:
             messagebox.showerror("Gabim", "Shto të paktën një rresht!"); return None
        
        offer = Offer(self.db)
        offer.id = self.offer_id
        offer.offer_number = offer_number
        offer.subject = subject
        offer.date = date_obj
        offer.client_id = client_id
        offer.description = "" # Main description is not used in this layout, or is spread across items
        
        subtotal = sum(i['quantity'] * i['unit_price'] for i in items)
        
        offer.subtotal = Decimal(str(subtotal))
        offer.vat_percentage = Decimal("0.00") 
        offer.vat_amount = Decimal("0.00")
        offer.total = Decimal(str(subtotal))
        
        for it in items: offer.add_item(it['description'], it['unit'], it['quantity'], it['unit_price'])
        
        return offer
    
    def process_save(self, action='save'):
        offer = self.get_offer_data()
        if not offer: return
        
        target_btn = self.btn_save_only
        if action == 'pdf': target_btn = self.btn_save_pdf
        
        original_text = target_btn.cget("text")
        target_btn.configure(text="Duke u ruajtur...", state="disabled"); self.update_idletasks()
        
        if offer.save():
            self.offer_id = offer.id
            try:
                if action == 'pdf':
                    generator = PDFGenerator()
                    output_path = generator.generate_offer(offer)
                    offer.pdf_path = output_path; offer.save()
                    os.startfile(output_path)
                    messagebox.showinfo("Sukses", "Oferta u ruajt dhe u hap PDF!")
                else:
                    messagebox.showinfo("Sukses", "Oferta u ruajt me sukses!")
                
                # Reset for new offer
                self.offer_id = None
                self.offer = None
                
                next_num = Offer.get_next_offer_number(self.db)
                self.offer_number_entry.delete(0, "end")
                self.offer_number_entry.insert(0, next_num)
                self.subject_entry.delete(0, "end")
                
                # Clear items
                for item in list(self.items): item['container'].destroy()
                self.items = []
                self.add_aligned_row()
                
            except Exception as e: messagebox.showerror("Gabim", f"Gabim gjatë procesimit: {str(e)}")
            finally: target_btn.configure(text=original_text, state="normal")
        else:
            target_btn.configure(text=original_text, state="normal")
            messagebox.showerror("Gabim", "Gabim në ruajtjen e ofertës!")
