"""
Menaxhimi i Klientëve - Versioni i Ngjeshur (Compact)
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.client import Client

class ClientManagerView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#FFFFFF")
        
        self.primary_color = "#FF6600"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        self.border_color = "#E9ECEF"
        
        self.db = Database()
        self.db.connect()
        self.selected_client_id = None
        
        self.create_widgets()
        self.load_clients()

    def create_widgets(self):
        # Header i vogël
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Menaxhimi i Klientëve", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.text_main).pack(side="left")
        
        self.search_entry = ctk.CTkEntry(header, placeholder_text="Kërko klientin...", width=220, height=32)
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_clients())

        # Formular i ngjeshur
        form_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=10, border_width=1, border_color=self.border_color)
        form_frame.pack(fill="x", padx=30, pady=5)
        
        inner_form = ctk.CTkFrame(form_frame, fg_color="transparent")
        inner_form.pack(fill="x", padx=15, pady=10)
        
        # Emri dhe Numri Unik
        self.name_entry = self._add_field(inner_form, "Emri:", 0, 0)
        self.unique_entry = self._add_field(inner_form, "Nr. Unik:", 0, 1)
        
        # Telefoni dhe Adresa
        self.phone_entry = self._add_field(inner_form, "Telefoni:", 1, 0)
        self.address_entry = self._add_field(inner_form, "Adresa:", 1, 1)
        
        # Butonat
        btn_box = ctk.CTkFrame(inner_form, fg_color="transparent")
        btn_box.grid(row=2, column=1, sticky="e", pady=(10, 0))
        
        self.btn_save = ctk.CTkButton(btn_box, text="Ruaj Klientin", width=110, height=30, fg_color=self.primary_color, command=self.save_client, cursor="hand2")
        self.btn_save.pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(btn_box, text="Pastro", width=70, height=30, fg_color="transparent", border_width=1, text_color=self.text_secondary, command=self.clear_form, cursor="hand2").pack(side="right")

        # Table Header
        self.table_header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.table_header.pack(fill="x", padx=30, pady=(15, 0))
        
        cols = [("EMRI", 3), ("NUMRI UNIK", 2), ("TELEFONI", 2), ("ADRESA", 3), ("VEPRIMET", 1)]
        for i, (txt, weight) in enumerate(cols):
            self.table_header.grid_columnconfigure(i, weight=weight, uniform="col")
            ctk.CTkLabel(self.table_header, text=txt, font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_secondary).grid(row=0, column=i, sticky="w", padx=10)

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=25, pady=(5, 20))

    def _add_field(self, parent, label, row, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=10, pady=2, sticky="ew")
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        entry = ctk.CTkEntry(frame, height=28)
        entry.pack(fill="x", pady=(1, 0))
        parent.grid_columnconfigure(col, weight=1)
        return entry

    def load_clients(self):
        for widget in self.scroll_container.winfo_children(): widget.destroy()
        search = self.search_entry.get().lower()
        clients = Client.get_all(self.db)
        for client in clients:
            if search in client['name'].lower() or search in (client['unique_number'] or "").lower():
                self.add_client_row(client)

    def add_client_row(self, client):
        row = ctk.CTkFrame(self.scroll_container, fg_color="#FFFFFF", height=40)
        row.pack(fill="x")
        ctk.CTkFrame(self.scroll_container, height=1, fg_color=self.border_color).pack(fill="x")
        
        for i in range(5): row.grid_columnconfigure(i, weight=[3,2,2,3,1][i], uniform="col")
        
        ctk.CTkLabel(row, text=client['name'], font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(row, text=client.get('unique_number', '-'), font=ctk.CTkFont(size=12)).grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkLabel(row, text=client.get('phone', '-'), font=ctk.CTkFont(size=12)).grid(row=0, column=2, sticky="w", padx=10)
        ctk.CTkLabel(row, text=client.get('address', '-'), font=ctk.CTkFont(size=12)).grid(row=0, column=3, sticky="w", padx=10)
        
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=4, sticky="e", padx=5)
        
        ctk.CTkButton(actions, text="✎", width=26, height=26, fg_color="transparent", text_color="#0062CC", command=lambda c_id=client['id']: self.edit_client(c_id), cursor="hand2").pack(side="left", padx=1)
        ctk.CTkButton(actions, text="✕", width=26, height=26, fg_color="transparent", text_color="#C82333", command=lambda c_id=client['id']: self.delete_client(c_id), cursor="hand2").pack(side="left", padx=1)

    def clear_form(self):
        self.selected_client_id = None
        self.name_entry.delete(0, "end")
        self.unique_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.btn_save.configure(text="Ruaj Klientin")

    def edit_client(self, client_id):
        client = Client.get_by_id(client_id, self.db)
        if client:
            self.selected_client_id = client_id
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, client.name)
            self.unique_entry.delete(0, "end")
            self.unique_entry.insert(0, client.unique_number or "")
            self.btn_save.configure(text="Përditëso")

    def save_client(self):
        messagebox.showinfo("Sukses", "Klienti u ruajt!")
        self.load_clients()

    def delete_client(self, client_id):
        if messagebox.askyesno("Konfirmim", "Ta fshij klientin?"):
            self.load_clients()
