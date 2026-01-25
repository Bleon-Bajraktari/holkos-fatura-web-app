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

        # 3. Description Area (Note/Conditions) - Now Main Content
        self.desc_card = ctk.CTkFrame(self.scrollable_frame, fg_color=self.bg_card, corner_radius=12, border_width=1, border_color=self.border_color)
        self.desc_card.pack(fill="both", expand=True, padx=30, pady=(15, 15))
        
        ctk.CTkLabel(self.desc_card, text="Përshkrimi i Ofertës / Kushtet:", font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=self.text_main).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.description_text = ctk.CTkTextbox(self.desc_card, height=300, font=ctk.CTkFont(size=12), fg_color="#FBFBFB", border_color=self.border_color, border_width=1, corner_radius=8)
        self.description_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 4. Action Buttons
        actions_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        actions_frame.pack(side="right", padx=30, pady=(0, 30))

        self.btn_save_only = ctk.CTkButton(actions_frame, text="Ruaj", command=lambda: self.process_save(action='save'), fg_color="#34495E", hover_color="#2C3E50", text_color="#FFFFFF", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), width=100, height=38, corner_radius=8, cursor="hand2")
        self.btn_save_only.pack(side="left", padx=5)

        self.btn_save_pdf = ctk.CTkButton(actions_frame, text="Ruaj & PDF", command=lambda: self.process_save(action='pdf'), fg_color=self.primary_color, hover_color="#E65C00", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), width=120, height=38, corner_radius=8, cursor="hand2")
        self.btn_save_pdf.pack(side="left", padx=5)
    
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
    
    def load_offer_data(self):
        if not self.offer: return
        client = Client.get_by_id(self.offer.client_id, self.db)
        if client: self.client_var.set(f"{client.name} ({client.unique_number})")
        
        self.date_entry.delete(0, "end"); self.date_entry.insert(0, self.offer.date.strftime("%d.%m.%Y") if self.offer.date else "")
        self.offer_number_entry.delete(0, "end"); self.offer_number_entry.insert(0, self.offer.offer_number)
        self.subject_entry.delete(0, "end"); self.subject_entry.insert(0, self.offer.subject or "")
        
        self.description_text.insert("0.0", self.offer.description or "")
    
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
        
        offer = Offer(self.db)
        offer.id = self.offer_id
        offer.offer_number = offer_number
        offer.subject = subject
        offer.date = date_obj
        offer.client_id = client_id
        offer.description = self.description_text.get("0.0", "end").strip()
        
        # Zero totals as we removed items
        offer.subtotal = Decimal("0.00")
        offer.vat_percentage = Decimal("0.00")
        offer.vat_amount = Decimal("0.00")
        offer.total = Decimal("0.00")
        
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
                self.description_text.delete("0.0", "end")
                self.subject_entry.delete(0, "end")
                
            except Exception as e: messagebox.showerror("Gabim", f"Gabim gjatë procesimit: {str(e)}")
            finally: target_btn.configure(text=original_text, state="normal")
        else:
            target_btn.configure(text=original_text, state="normal")
            messagebox.showerror("Gabim", "Gabim në ruajtjen e ofertës!")
