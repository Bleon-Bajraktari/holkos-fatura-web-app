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
        # 1. Main Form Container (Centered Sheet Style)
        self.main_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=(50, 50)) # Pull content inwards
        self.main_container.columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))
        
        title_text = "Redakto Ofertën" if self.offer_id else "Krijo Ofertë të Re"
        ctk.CTkLabel(header_frame, text=title_text, font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=self.text_main).pack(side="left")
        
        # 2. Informacione Bazë
        self.info_card = ctk.CTkFrame(self.main_container, fg_color=self.bg_card, corner_radius=12, border_width=1, border_color=self.border_color)
        self.info_card.pack(fill="x", pady=5)
        
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
        self.rows_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, pady=10)
        
        # Header for the Rows
        row_header = ctk.CTkFrame(self.rows_container, fg_color="transparent")
        row_header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(row_header, text="PËRSHKRIMI I ARTIKUJVE DHE KALKULIMET", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_secondary).pack(side="left", padx=5)
        
        # Add Buttons Toolbar
        toolbar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        toolbar.pack(pady=(10, 20))

        ctk.CTkButton(toolbar, text="+ Artikull", command=lambda: self.add_aligned_row(row_type='item'), fg_color="#F1F3F5", text_color=self.text_main, hover_color="#E9ECEF", width=120, height=32, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), cursor="hand2").pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="+ Titull", command=lambda: self.add_aligned_row(row_type='header'), fg_color="#E3F2FD", text_color="#1976D2", hover_color="#BBDEFB", width=100, height=32, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), cursor="hand2").pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="+ Tekst", command=lambda: self.add_aligned_row(row_type='text'), fg_color="#F3E5F5", text_color="#7B1FA2", hover_color="#E1BEE7", width=100, height=32, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), cursor="hand2").pack(side="left", padx=5)

        # Action Buttons
        actions_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        actions_frame.pack(fill="x", pady=20)
        
        btn_box = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_box.pack(side="right") # Still right-aligned but within the centered container

        self.btn_save_only = ctk.CTkButton(btn_box, text="Ruaj", command=lambda: self.process_save(action='save'), fg_color="#34495E", hover_color="#2C3E50", text_color="#FFFFFF", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), width=100, height=38, corner_radius=8, cursor="hand2")
        self.btn_save_only.pack(side="left", padx=5)
        self.btn_save_pdf = ctk.CTkButton(btn_box, text="Ruaj & PDF", command=lambda: self.process_save(action='pdf'), fg_color=self.primary_color, hover_color="#E65C00", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), width=120, height=38, corner_radius=8, cursor="hand2")
        self.btn_save_pdf.pack(side="left", padx=5)
        
        if not self.offer_id: self.add_aligned_row(row_type='item')
    
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
    
    def add_aligned_row(self, initial_data=None, row_type='item'):
        row_id = datetime.now().timestamp() # Unique enough for UI
        
        # Main row container
        row_frame = ctk.CTkFrame(self.rows_container, fg_color=self.bg_card, corner_radius=8, border_width=1, border_color=self.border_color)
        row_frame.pack(fill="x", pady=5, padx=5)
        
        # Grid layout for the row
        row_frame.columnconfigure(1, weight=3) # Description
        row_frame.columnconfigure(2, weight=1) # Calculations/Modules
        
        # Reorder Buttons (Far Left)
        reorder_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=30)
        reorder_frame.grid(row=0, column=0, sticky="n", pady=10, padx=2)
        
        ctk.CTkButton(reorder_frame, text="▲", width=20, height=20, fg_color="transparent", text_color=self.text_secondary, command=lambda: self.move_row(row_id, -1)).pack()
        ctk.CTkButton(reorder_frame, text="▼", width=20, height=20, fg_color="transparent", text_color=self.text_secondary, command=lambda: self.move_row(row_id, 1)).pack()

        # Left Side/Main: Description Textbox or Header Entry
        if row_type == 'header':
            desc_text = ctk.CTkEntry(row_frame, height=40, font=ctk.CTkFont(size=16, weight="bold"), fg_color="#E3F2FD", text_color="#1976D2", placeholder_text="TITULLI I SEKSIONIT...")
            desc_text.grid(row=0, column=1, columnspan=2, sticky="ew", padx=10, pady=10)
            modules_list_frame = None
            subtotal_label = None
        else:
            height = 80 if row_type == 'item' else 60
            placeholder = "Përshkrimi i artikullit..." if row_type == 'item' else "Tekst informativ ose shënime..."
            desc_text = ctk.CTkTextbox(row_frame, height=height, font=ctk.CTkFont(size=12), fg_color="#FBFBFB", border_width=0, corner_radius=6)
            desc_text.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
            
            if row_type == 'item':
                # Calculation Bar at the bottom
                calc_bar = ctk.CTkFrame(row_frame, fg_color="#F8F9FA", height=40, corner_radius=0)
                calc_bar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=1, pady=(0, 1))
                # Note: corner_radius=0 and pady=(0,1) makes it look like it's part of the bottom of the white card
                
                # Label with Icon style
                label_container = ctk.CTkFrame(calc_bar, fg_color="#E9ECEF", corner_radius=4, width=80, height=24)
                label_container.pack(side="left", padx=10, pady=8)
                label_container.pack_propagate(False)
                
                ctk.CTkLabel(label_container, text="Kalkulimi", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_secondary).pack(expand=True)
                
                # Horizontal Modules List
                modules_list_frame = ctk.CTkFrame(calc_bar, fg_color="transparent")
                modules_list_frame.pack(side="left", fill="x", padx=5)
                
                subtotal_label = ctk.CTkLabel(calc_bar, text="", width=0) # Kept for logic compatibility
                
                # Add Module Button (Integrated into bar)
                add_mod_btn = ctk.CTkButton(calc_bar, text="+ Shto vlerë", width=80, height=26, font=ctk.CTkFont(size=11, weight="bold"), 
                                            fg_color="transparent", text_color=self.primary_color, hover_color="#FFF4ED",
                                            border_width=1, border_color=self.primary_color, corner_radius=12, 
                                            command=lambda: self.add_module_to_row(row_id))
                add_mod_btn.pack(side="right", padx=15)
                
                # Store the list frame for module addition
                item_modules_frame = modules_list_frame
            else:
                item_modules_frame = None
                subtotal_label = None
        
        # Delete Row Button (Far Right, Top)
        del_row_btn = ctk.CTkButton(row_frame, text="✕", width=25, height=25, fg_color="transparent", text_color="#ADB5BD", hover_color="#FFF0F0", command=lambda r=row_id: self.remove_item_row(r))
        del_row_btn.grid(row=0, column=3, sticky="ne", padx=8, pady=8)
        
        item_entry = {
            'row': row_id, 'container': row_frame,
            'desc_text': desc_text,
            'row_type': row_type,
            'modules_container': item_modules_frame,
            'subtotal_label': subtotal_label,
            'modules': [] # List of module dicts
        }
        self.items.append(item_entry)
        
        if row_type == 'item' and not initial_data:
            self.add_module_to_row(row_id, "Sasia", "")
            self.add_module_to_row(row_id, "Çmimi", "€")
            
        desc_text.focus_set()

    def move_row(self, row_id, direction):
        # find index
        idx = next((i for i, item in enumerate(self.items) if item['row'] == row_id), None)
        if idx is None: return
        
        new_idx = idx + direction
        if 0 <= new_idx < len(self.items):
            # Swap in list
            self.items[idx], self.items[new_idx] = self.items[new_idx], self.items[idx]
            # Refresh UI order
            for item in self.items:
                item['container'].pack_forget()
            for item in self.items:
                item['container'].pack(fill="x", pady=5, padx=5)

    def add_module_to_row(self, row_id, label_text="", unit_text=""):
        item = next((i for i in self.items if i['row'] == row_id), None)
        if not item: return
        
        mod_id = datetime.now().timestamp() + len(item['modules'])
        mod_frame = ctk.CTkFrame(item['modules_container'], fg_color="transparent")
        mod_frame.pack(side="left", padx=2)
        
        # If not first, add multiplier symbol
        if len(item['modules']) > 0:
            ctk.CTkLabel(mod_frame, text="x", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ADB5BD").pack(side="left", padx=8)

        # Styled Input Group
        input_container = ctk.CTkFrame(mod_frame, fg_color="#FFFFFF", corner_radius=6, border_width=1, border_color="#DEE2E6")
        input_container.pack(side="left", pady=5)
        
        # Value
        val_entry = ctk.CTkEntry(input_container, width=55, height=24, font=ctk.CTkFont(size=11), fg_color="#FFFFFF", border_width=0, placeholder_text="0")
        val_entry.pack(side="left", padx=(2, 0))
        
        # Unit (ComboBox for quick selection + custom typing)
        unit_values = ["€", "m²", "m'", "m³", "copë"]
        unit_entry = ctk.CTkComboBox(input_container, width=75, height=24, font=ctk.CTkFont(size=10, weight="bold"), 
                                     values=unit_values,
                                     fg_color="#FFFFFF", border_width=0, button_color="#FFFFFF",
                                     button_hover_color="#E9ECEF", dropdown_font=ctk.CTkFont(size=10),
                                     text_color=self.primary_color)
        
        # Set initial value
        if unit_text: unit_entry.set(unit_text)
        elif label_text: unit_entry.set(label_text)
        else: unit_entry.set("")
        
        unit_entry.pack(side="left")
        
        # Mini Delete
        ctk.CTkButton(mod_frame, text="-", width=14, height=14, fg_color="transparent", text_color="#ADB5BD", hover_color="#F1F3F5", command=lambda: self.remove_module_from_row(row_id, mod_id)).pack(side="left", padx=2)
        
        module = {
            'id': mod_id,
            'container': mod_frame,
            'val_entry': val_entry,
            'unit_entry': unit_entry
        }
        item['modules'].append(module)
        
        # Update bindings
        val_entry.bind("<KeyRelease>", lambda e: self.update_row_subtotal(row_id))
        # ComboBox needs command or specific binding
        unit_entry.configure(command=lambda v: self.update_row_subtotal(row_id))
        self.update_row_subtotal(row_id)

    def remove_module_from_row(self, row_id, mod_id):
        item = next((i for i in self.items if i['row'] == row_id), None)
        if not item: return
        
        module = next((m for m in item['modules'] if m['id'] == mod_id), None)
        if module:
            module['container'].destroy()
            item['modules'].remove(module)
            self.update_row_subtotal(row_id)

    def update_row_subtotal(self, row_id):
        item = next((i for i in self.items if i['row'] == row_id), None)
        if not item: return
        
        # We try to calculate a subtotal if there's a "Sasia" and "Çmimi" (or similar)
        # For now, let's keep it simple: if there are 2 or more numeric modules, 
        # try to multiply them? Or user can define which is which.
        # Let's assume the first numeric module is Qty and subsequent are multipliers?
        # Actually, let's just look for modules where unit contains '€' for price and others for qty.
        
        vals = []
        for mod in item['modules']:
            try:
                val_str = mod['val_entry'].get().replace(",", ".")
                if val_str:
                    vals.append(float(val_str))
            except:
                pass
        
        if len(vals) >= 2:
            total = 1.0
            for v in vals: total *= v
            if item['subtotal_label'].winfo_exists():
                item['subtotal_label'].configure(text=f"{total:,.2f} €".replace(",", " "))
        else:
            if len(vals) == 1:
                if item['subtotal_label'].winfo_exists():
                    item['subtotal_label'].configure(text=f"{vals[0]:,.2f} €".replace(",", " "))
            else:
                if item['subtotal_label'].winfo_exists():
                    item['subtotal_label'].configure(text="0.00 €")

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
        
        # Clear default row added in constructor
        for item in list(self.items):
            item['container'].destroy()
        self.items = []
        
        # Load from DB
        for item_data in self.offer.items:
            t = item_data.get('row_type', 'item')
            self.add_aligned_row(initial_data=item_data, row_type=t)
            last_item = self.items[-1]
            
            if t == 'header':
                last_item['desc_text'].delete(0, "end")
                last_item['desc_text'].insert(0, item_data['description'])
            else:
                last_item['desc_text'].delete("0.0", "end")
                last_item['desc_text'].insert("0.0", item_data['description'])
            
            if t == 'item':
                # Clear default modules
                for mod in list(last_item['modules']): mod['container'].destroy()
                last_item['modules'] = []
                
                custom_attr = item_data.get('custom_attributes')
                if custom_attr and isinstance(custom_attr, list):
                    for attr in custom_attr:
                        self.add_module_to_row(last_item['row'], unit_text=attr.get('unit', ''))
                        mod = last_item['modules'][-1]
                        mod['val_entry'].insert(0, str(attr.get('value', '')))
                else:
                    if item_data['quantity'] > 0:
                        self.add_module_to_row(last_item['row'], unit_text=item_data['unit'])
                        last_item['modules'][-1]['val_entry'].insert(0, str(item_data['quantity']))
                    if item_data['unit_price'] > 0:
                        self.add_module_to_row(last_item['row'], unit_text="€")
                        last_item['modules'][-1]['val_entry'].insert(0, str(item_data['unit_price']))
                
                self.update_row_subtotal(last_item['row'])

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
        
        items = []
        total_sum = Decimal("0.00")
        
        for item_entry in self.items:
            t = item_entry['row_type']
            if t == 'header':
                desc = item_entry['desc_text'].get().strip()
            else:
                desc = item_entry['desc_text'].get("0.0", "end").strip()
            
            modules_data = []
            row_vals = []
            
            if t == 'item' and item_entry['modules']:
                for mod in item_entry['modules']:
                    val = mod['val_entry'].get().strip()
                    unit = mod['unit_entry'].get().strip()
                    if val or unit:
                        modules_data.append({'value': val, 'unit': unit})
                        if val:
                            try: row_vals.append(float(val.replace(",", ".")))
                            except: pass
            
            if not desc and not modules_data: continue

            qty = Decimal("1.00")
            price = Decimal("0.00")
            
            if t == 'item':
                if len(row_vals) >= 2:
                    sub = 1.0
                    for v in row_vals: sub *= v
                    price = Decimal(str(sub))
                elif len(row_vals) == 1:
                    price = Decimal(str(row_vals[0]))
                total_sum += price
            
            items.append({
                'description': desc,
                'unit': "", 
                'quantity': qty,
                'unit_price': price,
                'row_type': t,
                'custom_attributes': modules_data
            })
        
        if not items:
             messagebox.showerror("Gabim", "Shto të paktën një rresht!"); return None
        
        offer = Offer(self.db)
        offer.id = self.offer_id
        offer.offer_number = offer_number
        offer.subject = subject
        offer.date = date_obj
        offer.client_id = client_id
        offer.description = "" 
        
        offer.subtotal = total_sum
        offer.vat_percentage = Decimal("0.00") 
        offer.vat_amount = Decimal("0.00")
        offer.total = total_sum
        
        for it in items: 
            offer.add_item(it['description'], it['unit'], it['quantity'], it['unit_price'], it['custom_attributes'], it['row_type'])
        
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
