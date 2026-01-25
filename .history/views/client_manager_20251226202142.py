"""
Menaxhimi i klientëve
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.client import Client

class ClientManagerView(ctk.CTkFrame):
    """Menaxhimi i klientëve me CRUD operations"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Scrollable frame për përmbajtjen
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        self.db = Database()
        self.db.connect()
        
        self.selected_client_id = None
        
        self.create_widgets()
        self.load_clients()
    
    def create_widgets(self):
        """Krijon widget-et"""
        # Titulli
        title = ctk.CTkLabel(
            self,
            text="Menaxhimi i Klientëve",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Frame për formularin
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        # Emri
        ctk.CTkLabel(form_frame, text="Emri:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=300)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Adresa
        ctk.CTkLabel(form_frame, text="Adresa:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.address_entry = ctk.CTkEntry(form_frame, width=300)
        self.address_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Numri unik
        ctk.CTkLabel(form_frame, text="Numri unik:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.unique_number_entry = ctk.CTkEntry(form_frame, width=300)
        self.unique_number_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # Telefoni
        ctk.CTkLabel(form_frame, text="Telefoni:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.phone_entry = ctk.CTkEntry(form_frame, width=300)
        self.phone_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        # Email
        ctk.CTkLabel(form_frame, text="Email:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.email_entry = ctk.CTkEntry(form_frame, width=300)
        self.email_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        
        # Butonat e formularit
        buttons_frame = ctk.CTkFrame(form_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        btn_save = ctk.CTkButton(
            buttons_frame,
            text="Ruaj",
            command=self.save_client,
            width=120,
            height=35
        )
        btn_save.pack(side="left", padx=10)
        
        btn_clear = ctk.CTkButton(
            buttons_frame,
            text="Pastro",
            command=self.clear_form,
            width=120,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        )
        btn_clear.pack(side="left", padx=10)
        
        # Kërkimi
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        ctk.CTkLabel(search_frame, text="Kërko:", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        self.search_entry = ctk.CTkEntry(search_frame, width=300)
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_clients())
        
        # Tabela e klientëve (me scroll)
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        scrollable_table = ctk.CTkScrollableFrame(table_container)
        scrollable_table.pack(fill="both", expand=True)
        
        table_frame = ctk.CTkFrame(scrollable_table)
        table_frame.pack(fill="both", expand=True)
        
        # Header
        headers = ["Emri", "Adresa", "Numri unik", "Telefoni", "Email", "Veprimet"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
            table_frame.grid_columnconfigure(i, weight=1 if i < 5 else 0)
        
        self.table_frame = table_frame
    
    def clear_form(self):
        """Pastron formularin"""
        self.selected_client_id = None
        self.name_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.unique_number_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
    
    def load_clients(self):
        """Ngarkon klientët"""
        # Pastro tabelën
        for widget in self.table_frame.winfo_children():
            if widget.grid_info()['row'] > 0:
                widget.destroy()
        
        # Merr klientët
        search_term = self.search_entry.get()
        if search_term:
            clients = Client.search(search_term, self.db)
        else:
            clients = Client.get_all(self.db)
        
        # Shfaq në tabelë
        for i, client in enumerate(clients, start=1):
            self.add_client_row(i, client)
    
    def add_client_row(self, row, client):
        """Shton një rresht klienti në tabelë"""
        # Emri
        name_label = ctk.CTkLabel(
            self.table_frame,
            text=client['name'],
            font=ctk.CTkFont(size=11)
        )
        name_label.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        
        # Adresa
        address_label = ctk.CTkLabel(
            self.table_frame,
            text=client.get('address', ''),
            font=ctk.CTkFont(size=11)
        )
        address_label.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        
        # Numri unik
        unique_label = ctk.CTkLabel(
            self.table_frame,
            text=client.get('unique_number', ''),
            font=ctk.CTkFont(size=11)
        )
        unique_label.grid(row=row, column=2, padx=5, pady=5, sticky="ew")
        
        # Telefoni
        phone_label = ctk.CTkLabel(
            self.table_frame,
            text=client.get('phone', ''),
            font=ctk.CTkFont(size=11)
        )
        phone_label.grid(row=row, column=3, padx=5, pady=5, sticky="ew")
        
        # Email
        email_label = ctk.CTkLabel(
            self.table_frame,
            text=client.get('email', ''),
            font=ctk.CTkFont(size=11)
        )
        email_label.grid(row=row, column=4, padx=5, pady=5, sticky="ew")
        
        # Veprimet
        actions_frame = ctk.CTkFrame(self.table_frame)
        actions_frame.grid(row=row, column=5, padx=5, pady=5)
        
        btn_edit = ctk.CTkButton(
            actions_frame,
            text="Redakto",
            width=70,
            height=25,
            command=lambda c_id=client['id']: self.edit_client(c_id),
            font=ctk.CTkFont(size=10),
            fg_color="orange",
            hover_color="darkorange"
        )
        btn_edit.pack(side="left", padx=2)
        
        btn_delete = ctk.CTkButton(
            actions_frame,
            text="Fshi",
            width=60,
            height=25,
            command=lambda c_id=client['id']: self.delete_client(c_id),
            font=ctk.CTkFont(size=10),
            fg_color="red",
            hover_color="darkred"
        )
        btn_delete.pack(side="left", padx=2)
    
    def edit_client(self, client_id):
        """Redakton klientin"""
        client = Client.get_by_id(client_id, self.db)
        if client:
            self.selected_client_id = client_id
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, client.name)
            self.address_entry.delete(0, "end")
            self.address_entry.insert(0, client.address or "")
            self.unique_number_entry.delete(0, "end")
            self.unique_number_entry.insert(0, client.unique_number or "")
            self.phone_entry.delete(0, "end")
            self.phone_entry.insert(0, client.phone or "")
            self.email_entry.delete(0, "end")
            self.email_entry.insert(0, client.email or "")
    
    def delete_client(self, client_id):
        """Fshin klientin"""
        if not messagebox.askyesno("Konfirmim", "Jeni të sigurt që dëshironi të fshini këtë klient?"):
            return
        
        client = Client.get_by_id(client_id, self.db)
        if client and client.delete():
            messagebox.showinfo("Sukses", "Klienti u fshi me sukses!")
            self.clear_form()
            self.load_clients()
        else:
            messagebox.showerror("Gabim", "Gabim në fshirjen e klientit!")
    
    def save_client(self):
        """Ruaj klientin"""
        name = self.name_entry.get()
        if not name:
            messagebox.showerror("Gabim", "Ju lutem shkruani emrin e klientit!")
            return
        
        client = Client(self.db)
        if self.selected_client_id:
            client.id = self.selected_client_id
        
        client.name = name
        client.address = self.address_entry.get()
        client.unique_number = self.unique_number_entry.get()
        client.phone = self.phone_entry.get()
        client.email = self.email_entry.get()
        
        if client.save():
            messagebox.showinfo("Sukses", "Klienti u ruajt me sukses!")
            self.clear_form()
            self.load_clients()
        else:
            messagebox.showerror("Gabim", "Gabim në ruajtjen e klientit!")

