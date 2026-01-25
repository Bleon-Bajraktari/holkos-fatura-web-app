"""
Dritarja e cilësimeve - v1.2.0 (Shtuar SMTP)
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from models.database import Database
from models.company import Company
from models.client import Client
from models.invoice import Invoice
import os
import json
from datetime import datetime, date
from config.settings import IMAGES_DIR

class SettingsWindow(ctk.CTkToplevel):
    """Dritarja e cilësimeve për kompaninë"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Cilësimet")
        self.geometry("550x600")
        self.resizable(True, True)
        
        # Qendërzo në ekran
        self.update_idletasks()
        try:
            width = 550
            height = 600
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            if y < 0: y = 0
            self.geometry(f"{width}x{height}+{x}+{y}")
        except: pass
        
        self.db = Database()
        self.db.connect()
        
        self.company = Company(self.db)
        self.company.load()
        
        self.create_widgets()
        self.load_company_data()
    
    def create_widgets(self):
        """Krijon widget-et"""
        title = ctk.CTkLabel(
            self,
            text="Cilësimet e Kompanisë",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- Seksioni: Informacione Bazë ---
        ctk.CTkLabel(form_frame, text="INFORMACIONE BAZË", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FF6600").grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w")
        
        self._add_field(form_frame, "Emri i kompanisë:", "name_entry", 1)
        self._add_field(form_frame, "Adresa:", "address_entry", 2)
        self._add_field(form_frame, "Telefoni:", "phone_entry", 3)
        self._add_field(form_frame, "Email Publik:", "email_entry", 4)
        self._add_field(form_frame, "Numri unik:", "unique_number_entry", 5)
        self._add_field(form_frame, "Numri fiskal:", "fiscal_number_entry", 6)
        self._add_field(form_frame, "Llogaria NLB:", "account_nib_entry", 7)
        
        # Logo
        logo_frame = ctk.CTkFrame(form_frame)
        logo_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(logo_frame, text="Logo:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        self.logo_path_label = ctk.CTkLabel(logo_frame, text="Nuk është zgjedhur logo", font=ctk.CTkFont(size=11), text_color="gray")
        self.logo_path_label.pack(side="left", padx=10)
        ctk.CTkButton(logo_frame, text="Zgjedh Logo", command=self.browse_logo, width=120).pack(side="left", padx=10)
        
        # --- Seksioni: Cilësimet e Email-it (SMTP) ---
        ctk.CTkLabel(form_frame, text="CILËSIMET E EMAIL-IT (SMTP)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FF6600").grid(row=9, column=0, columnspan=2, pady=(20, 5), sticky="w")
        
        self._add_field(form_frame, "SMTP Server:", "smtp_server_entry", 10)
        self._add_field(form_frame, "SMTP Port:", "smtp_port_entry", 11)
        self._add_field(form_frame, "SMTP Email:", "smtp_user_entry", 12)
        
        # Password me maskim
        ctk.CTkLabel(form_frame, text="SMTP Password:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=13, column=0, padx=10, pady=10, sticky="w")
        self.smtp_password_entry = ctk.CTkEntry(form_frame, width=400, show="*")
        self.smtp_password_entry.grid(row=13, column=1, padx=10, pady=10, sticky="ew")
        
        info_txt = "Për Gmail, përdorni 'App Password'. Porti 587 për TLS."
        ctk.CTkLabel(form_frame, text=info_txt, font=ctk.CTkFont(size=10), text_color="gray").grid(row=14, column=1, sticky="w", padx=10)

        # --- Seksioni: Backup ---
        ctk.CTkLabel(form_frame, text="TË DHËNAT DHE BACKUP", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FF6600").grid(row=15, column=0, columnspan=2, pady=(20, 5), sticky="w")
        
        backup_frame = ctk.CTkFrame(form_frame)
        backup_frame.grid(row=16, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(backup_frame, text="Ruaj kopje rezervë të të gjitha të dhënave (JSON):", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkButton(backup_frame, text="Ruaj Backup", command=self.backup_data, width=120, fg_color="#3498DB", hover_color="#2980B9").pack(side="right", padx=10)

        # Butonat
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(buttons_frame, text="Ruaj", command=self.save_settings, width=150, height=40, fg_color="#2ECC71", hover_color="#27AE60").pack(side="left", padx=10)
        ctk.CTkButton(buttons_frame, text="Anulo", command=self.destroy, width=150, height=40, fg_color="gray", hover_color="#555555").pack(side="left", padx=10)

    def _add_field(self, parent, label, attr_name, row):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold")).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        entry = ctk.CTkEntry(parent, width=400)
        entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        parent.grid_columnconfigure(1, weight=1)
        setattr(self, attr_name, entry)

    def load_company_data(self):
        self.name_entry.insert(0, self.company.name or "")
        self.address_entry.insert(0, self.company.address or "")
        self.phone_entry.insert(0, self.company.phone or "")
        self.email_entry.insert(0, self.company.email or "")
        self.unique_number_entry.insert(0, self.company.unique_number or "")
        self.fiscal_number_entry.insert(0, self.company.fiscal_number or "")
        self.account_nib_entry.insert(0, self.company.account_nib or "")
        
        self.smtp_server_entry.insert(0, self.company.smtp_server or "smtp.gmail.com")
        self.smtp_port_entry.insert(0, str(self.company.smtp_port or 587))
        self.smtp_user_entry.insert(0, self.company.smtp_user or "")
        self.smtp_password_entry.insert(0, self.company.smtp_password or "")
        
        if self.company.logo_path and os.path.exists(self.company.logo_path):
            self.logo_path_label.configure(text=os.path.basename(self.company.logo_path))
    
    def browse_logo(self):
        filename = filedialog.askopenfilename(title="Zgjedh Logo", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if filename:
            import shutil
            dest_path = os.path.join(IMAGES_DIR, "logo.png")
            try:
                shutil.copy2(filename, dest_path)
                self.company.logo_path = dest_path
                self.logo_path_label.configure(text=os.path.basename(dest_path))
            except Exception as e: messagebox.showerror("Gabim", f"Gabim: {str(e)}")
    
    def save_settings(self):
        self.company.name = self.name_entry.get()
        self.company.address = self.address_entry.get()
        self.company.phone = self.phone_entry.get()
        self.company.email = self.email_entry.get()
        self.company.unique_number = self.unique_number_entry.get()
        self.company.fiscal_number = self.fiscal_number_entry.get()
        self.company.account_nib = self.account_nib_entry.get()
        
        self.company.smtp_server = self.smtp_server_entry.get()
        try: self.company.smtp_port = int(self.smtp_port_entry.get())
        except: self.company.smtp_port = 587
        self.company.smtp_user = self.smtp_user_entry.get()
        self.company.smtp_password = self.smtp_password_entry.get()
        
        if self.company.save():
            messagebox.showinfo("Sukses", "Cilësimet u ruajtën!")
            self.destroy()
        else:
            messagebox.showerror("Gabim", "Gabim në ruajtje!")

    def backup_data(self):
        """Krijon një backup të plotë në format JSON"""
        try:
            clients = Client.get_all(self.db)
            invoices = Invoice.get_all(self.db)
            
            # Për secilën faturë, merr artikujt full (sepse get_all është i lehtë)
            full_invoices = []
            for inv_data in invoices:
                inv = Invoice.get_by_id(inv_data['id'], self.db)
                if inv:
                    full_invoices.append(inv.to_dict())
            
            data = {
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'company': self.company.name,
                'clients': clients,
                'invoices': full_invoices
            }
            
            filename = f"Holkos_Backup_{date.today().strftime('%Y-%m-%d')}.json"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=filename,
                filetypes=[("JSON Files", "*.json")]
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, default=str, ensure_ascii=False)
                messagebox.showinfo("Sukses", f"Backup u ruajt me sukses!\n{filepath}")
                
        except Exception as e:
            messagebox.showerror("Gabim", f"Backup dështoi: {str(e)}")
