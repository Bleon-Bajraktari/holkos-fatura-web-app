"""
Menaxhimi i klientëve
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.client import Client

class ClientManagerView(ctk.CTkFrame):
    """Menaxhimi i klientëve - Premium Redesign"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="#FFFFFF")
        
        # Ngjyrat dhe Stili
        self.primary_color = "#FF6600"
        self.bg_secondary = "#F8F9FA"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        self.border_color = "#E9ECEF"
        
        self.db = Database()
        self.db.connect()
        self.selected_client_id = None
        
        self.create_widgets()
        self.load_clients()
    
    def create_widgets(self):
        """Ndërtimi i strukturës premium"""
        # 1. Header (Titulli dhe Kërkimi)
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_lbl = ctk.CTkLabel(
            header_frame, 
            text="Menaxhimi i Klientëve", 
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=self.text_main
        )
        title_lbl.pack(side="left")
        
        # Search Entry (Small and clean)
        self.search_entry = ctk.CTkEntry(
            header_frame, 
            placeholder_text="Kërko klientin...",
            width=250,
            height=35,
            fg_color=self.bg_secondary,
            border_color=self.border_color,
            corner_radius=8
        )
        self.search_entry.pack(side="right", padx=(20, 0))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_clients())
        
        # 2. Form Frame (Compact & Professional)
        form_outer = ctk.CTkFrame(self, fg_color=self.bg_secondary, corner_radius=12)
        form_outer.pack(fill="x", padx=30, pady=10)
        
        form_grid = ctk.CTkFrame(form_outer, fg_color="transparent")
        form_grid.pack(fill="x", padx=20, pady=15)
        
        # Rreshti i parë: Emri, Adresa, Numri Unik
        self._add_field(form_grid, "Emri i Klientit:", "name_entry", 0, 0)
        self._add_field(form_grid, "Adresa:", "address_entry", 0, 1)
        self._add_field(form_grid, "Numri Unik:", "unique_number_entry", 0, 2)
        
        # Rreshti i dytë: Telefoni, Email + Butonat
        self._add_field(form_grid, "Telefoni:", "phone_entry", 1, 0)
        self._add_field(form_grid, "Email:", "email_entry", 1, 1)
        
        # Butonat
        btn_container = ctk.CTkFrame(form_grid, fg_color="transparent")
        btn_container.grid(row=1, column=2, sticky="e", pady=(20, 0))
        
        self.btn_save = ctk.CTkButton(
            btn_container,
            text="Ruaj Klientin",
            command=self.save_client,
            fg_color=self.primary_color,
            hover_color="#E65C00",
            font=ctk.CTkFont(family="Inter", weight="bold"),
            width=130,
            height=35
        )
        self.btn_save.pack(side="right", padx=(10, 0))
        
        self.btn_clear = ctk.CTkButton(
            btn_container,
            text="Pastro",
            command=self.clear_form,
            fg_color="transparent",
            border_width=1,
            border_color=self.border_color,
            text_color=self.text_secondary,
            hover_color="#F1F1F1",
            width=80,
            height=35
        )
        self.btn_clear.pack(side="right")
        
        form_grid.columnconfigure((0,1,2), weight=1)

        # 3. Lista e Klientëve (Pjesa kryesore - u rrit si kërkesë)
        list_label = ctk.CTkLabel(
            self, 
            text="Lista e Klientëve të Regjistruar", 
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=self.text_main,
            anchor="w"
        )
        list_label.pack(fill="x", padx=35, pady=(20, 5))

        # Tabelë Container (I nevojshëm për layout-in e listës)
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Table Header (Guaranteed Alignment)
        self.header_frame = ctk.CTkFrame(table_container, fg_color="#F1F3F5", height=45, corner_radius=8)
        self.header_frame.pack(fill="x", pady=(0, 5))
        self.header_frame.pack_propagate(False)
        
        # Configure grid for header
        self.header_frame.grid_columnconfigure(0, weight=3, uniform="col") # Emri
        self.header_frame.grid_columnconfigure(1, weight=2, uniform="col") # Adresa
        self.header_frame.grid_columnconfigure(2, weight=2, uniform="col") # Numri
        self.header_frame.grid_columnconfigure(3, weight=2, uniform="col") # Telefoni
        self.header_frame.grid_columnconfigure(4, weight=2, uniform="col") # Email
        self.header_frame.grid_columnconfigure(5, weight=1, uniform="col") # Actions
        
        cols = ["EMRI", "ADRESA", "NUMRI UNIK", "TELEFONI", "EMAIL", "VEPRIMET"]
        for i, col in enumerate(cols):
            anchor = "w" if i < 5 else "center"
            lbl = ctk.CTkLabel(
                self.header_frame, 
                text=col, 
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"), 
                text_color=self.text_secondary,
                anchor=anchor
            )
            lbl.grid(row=0, column=i, padx=(20 if i==0 else 10, 10), sticky="ew" if i < 5 else "ns")

        # Scrollable Area
        self.scroll_container = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True)

    def _add_field(self, parent, label, attr_name, row, col):
        """Shton një fushë hyrëse në formë"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(container, text=label, font=ctk.CTkFont(family="Inter", size=12, weight="bold"), text_color=self.text_main).pack(anchor="w")
        entry = ctk.CTkEntry(
            container, 
            height=35, 
            fg_color="#FFFFFF", 
            border_color=self.border_color,
            corner_radius=8
        )
        entry.pack(fill="x", pady=(5, 0))
        setattr(self, attr_name, entry)

    def load_clients(self):
        """Ngarkon klientët me dizajni e ri"""
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        search_term = self.search_entry.get().lower()
        if search_term:
            clients = Client.search(search_term, self.db)
        else:
            clients = Client.get_all(self.db)
            
        if not clients:
            self._show_empty_state()
            return
            
        for client in clients:
            self.add_client_row(client)

    def add_client_row(self, client):
        """Shton një rresht premium me rreshtim perfekt"""
        row = ctk.CTkFrame(self.scroll_container, fg_color="#FFFFFF", height=55, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        
        # PERFECT ALIGNMENT: Përdorim të njëjtat weight dhe uniform
        row.grid_columnconfigure(0, weight=3, uniform="col") 
        row.grid_columnconfigure(1, weight=2, uniform="col")
        row.grid_columnconfigure(2, weight=2, uniform="col")
        row.grid_columnconfigure(3, weight=2, uniform="col")
        row.grid_columnconfigure(4, weight=2, uniform="col")
        row.grid_columnconfigure(5, weight=1, uniform="col")
        
        # Hover effect
        def on_enter(e): row.configure(fg_color="#F8F9FA")
        def on_leave(e): row.configure(fg_color="#FFFFFF")
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        
        # Të dhënat
        fields = [
            (client['name'], "Inter", "bold", self.text_main),
            (client.get('address', '-'), "Inter", "normal", self.text_secondary),
            (client.get('unique_number', '-'), "Inter", "normal", self.text_secondary),
            (client.get('phone', '-'), "Inter", "normal", self.text_secondary),
            (client.get('email', '-'), "Inter", "normal", self.text_secondary)
        ]
        
        for i, (text, family, weight, color) in enumerate(fields):
            lbl = ctk.CTkLabel(
                row, 
                text=text, 
                font=ctk.CTkFont(family=family, size=12, weight=weight), 
                text_color=color,
                anchor="w"
            )
            lbl.grid(row=0, column=i, padx=(20 if i==0 else 10, 10), sticky="ew")
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
        
        # Veprimet (Qendra)
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=10)
        
        # Edit btn
        btn_edit = ctk.CTkButton(
            actions, text="✎", width=32, height=32, fg_color="#F1F1F1", text_color=self.text_main,
            hover_color="#E5E5E5", corner_radius=6, command=lambda c_id=client['id']: self.edit_client(c_id)
        )
        btn_edit.pack(side="left", padx=2)
        
        # Delete btn
        btn_del = ctk.CTkButton(
            actions, text="🗑", width=32, height=32, fg_color="#FFF0F0", text_color="#E74C3C",
            hover_color="#FFE5E5", corner_radius=6, command=lambda c_id=client['id']: self.delete_client(c_id)
        )
        btn_del.pack(side="left", padx=2)

    def _show_empty_state(self):
        """Shfaqet kur nuk ka rezultate"""
        container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        container.pack(expand=True, pady=100)
        ctk.CTkLabel(container, text="📭", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(container, text="Nuk u gjet asnjë klient", font=ctk.CTkFont(family="Inter", size=16), text_color=self.text_secondary).pack(pady=10)

    def clear_form(self):
        """Pastron formularin"""
        self.selected_client_id = None
        self.name_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.unique_number_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self.btn_save.configure(text="Ruaj Klientin")
    
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
            self.btn_save.configure(text="Përditëso")
            # Shko te pjesa e sipërme
            # self.master.focus_set() # Nuk na duhet
    
    def delete_client(self, client_id):
        """Fshin klientin me konfirmim modern"""
        if not messagebox.askyesno("Konfirmim", "Jeni të sigurt që dëshironi të fshini këtë klient?"):
            return
        
        client = Client.get_by_id(client_id, self.db)
        if client and client.delete():
            self.clear_form()
            self.load_clients()
        else:
            messagebox.showerror("Gabim", "Gabim në fshirjen e klientit!")
    
    def save_client(self):
        """Ruaj ose përditëso klientin"""
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
            self.clear_form()
            self.load_clients()
        else:
            messagebox.showerror("Gabim", "Gabim në ruajtjen e klientit!")

