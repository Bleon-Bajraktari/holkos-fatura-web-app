"""
Dritarja e cilësimeve
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from models.database import Database
from models.company import Company
import os
from config.settings import IMAGES_DIR

class SettingsWindow(ctk.CTkToplevel):
    """Dritarja e cilësimeve për kompaninë"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Cilësimet")
        self.geometry("600x700")
        self.resizable(False, False)
        
        self.db = Database()
        self.db.connect()
        
        self.company = Company(self.db)
        self.company.load()
        
        self.create_widgets()
        self.load_company_data()
    
    def create_widgets(self):
        """Krijon widget-et"""
        # Titulli
        title = ctk.CTkLabel(
            self,
            text="Cilësimet e Kompanisë",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Frame për formularin
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Emri
        ctk.CTkLabel(form_frame, text="Emri i kompanisë:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=400)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Adresa
        ctk.CTkLabel(form_frame, text="Adresa:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.address_entry = ctk.CTkEntry(form_frame, width=400)
        self.address_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Telefoni
        ctk.CTkLabel(form_frame, text="Telefoni:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.phone_entry = ctk.CTkEntry(form_frame, width=400)
        self.phone_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # Email
        ctk.CTkLabel(form_frame, text="Email:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.email_entry = ctk.CTkEntry(form_frame, width=400)
        self.email_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        # Numri unik
        ctk.CTkLabel(form_frame, text="Numri unik:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.unique_number_entry = ctk.CTkEntry(form_frame, width=400)
        self.unique_number_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        
        # Numri fiskal
        ctk.CTkLabel(form_frame, text="Numri fiskal:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.fiscal_number_entry = ctk.CTkEntry(form_frame, width=400)
        self.fiscal_number_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
        
        # Llogaria NIB
        ctk.CTkLabel(form_frame, text="Llogaria NIB:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.account_nib_entry = ctk.CTkEntry(form_frame, width=400)
        self.account_nib_entry.grid(row=6, column=1, padx=10, pady=10, sticky="ew")
        
        # Logo
        logo_frame = ctk.CTkFrame(form_frame)
        logo_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(logo_frame, text="Logo:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        self.logo_path_label = ctk.CTkLabel(logo_frame, text="Nuk është zgjedhur logo", font=ctk.CTkFont(size=11), text_color="gray")
        self.logo_path_label.pack(side="left", padx=10)
        
        btn_browse = ctk.CTkButton(
            logo_frame,
            text="Zgjedh Logo",
            command=self.browse_logo,
            width=120
        )
        btn_browse.pack(side="left", padx=10)
        
        # Butonat
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        btn_save = ctk.CTkButton(
            buttons_frame,
            text="Ruaj",
            command=self.save_settings,
            width=150,
            height=40,
            fg_color="#28a745",
            hover_color="#34ce57"
        )
        btn_save.pack(side="left", padx=10)
        
        btn_cancel = ctk.CTkButton(
            buttons_frame,
            text="Anulo",
            command=self.destroy,
            width=150,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        btn_cancel.pack(side="left", padx=10)
    
    def load_company_data(self):
        """Ngarkon të dhënat e kompanisë"""
        self.name_entry.insert(0, self.company.name or "")
        self.address_entry.insert(0, self.company.address or "")
        self.phone_entry.insert(0, self.company.phone or "")
        self.email_entry.insert(0, self.company.email or "")
        self.unique_number_entry.insert(0, self.company.unique_number or "")
        self.fiscal_number_entry.insert(0, self.company.fiscal_number or "")
        self.account_nib_entry.insert(0, self.company.account_nib or "")
        
        if self.company.logo_path and os.path.exists(self.company.logo_path):
            self.logo_path_label.configure(text=os.path.basename(self.company.logo_path))
    
    def browse_logo(self):
        """Zgjedh skedarin e logos"""
        filename = filedialog.askopenfilename(
            title="Zgjedh Logo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if filename:
            # Kopjo në assets/images
            import shutil
            dest_path = os.path.join(IMAGES_DIR, "logo.png")
            try:
                shutil.copy2(filename, dest_path)
                self.company.logo_path = dest_path
                self.logo_path_label.configure(text=os.path.basename(dest_path))
                messagebox.showinfo("Sukses", "Logo u kopjua me sukses!")
            except Exception as e:
                messagebox.showerror("Gabim", f"Gabim në kopjimin e logos: {str(e)}")
    
    def save_settings(self):
        """Ruaj cilësimet"""
        self.company.name = self.name_entry.get()
        self.company.address = self.address_entry.get()
        self.company.phone = self.phone_entry.get()
        self.company.email = self.email_entry.get()
        self.company.unique_number = self.unique_number_entry.get()
        self.company.fiscal_number = self.fiscal_number_entry.get()
        self.company.account_nib = self.account_nib_entry.get()
        
        if self.company.save():
            messagebox.showinfo("Sukses", "Cilësimet u ruajtën me sukses!")
            self.destroy()
        else:
            messagebox.showerror("Gabim", "Gabim në ruajtjen e cilësimeve!")

