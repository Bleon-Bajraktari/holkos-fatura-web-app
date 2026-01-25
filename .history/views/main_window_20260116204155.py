"""
Dritarja kryesore - v1.1.0 (Fullscreen Fix & Manual Component Scaling)
"""
import customtkinter as ctk
from views.dashboard import DashboardView
from views.invoice_form import InvoiceFormView
from views.offer_form import OfferFormView
from views.invoice_list import InvoiceListView
from views.offer_list import OfferListView
from views.client_manager import ClientManagerView
from views.template_manager import TemplateManagerView
from views.settings_window import SettingsWindow
import os
import sys

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Holkos Fatura - v1.1.0")
        
        # 1. HEQIM SCALING-UN GLOBAL (Ky ishte shkaktari i problemit në Fullscreen)
        ctk.set_appearance_mode("light")
        # Nuk përdorim më ctk.set_widget_scaling këtu
        
        self.set_icon()
        self.primary_color = "#FF6600"
        
        # 2. Ndërtojmë strukturën
        self.create_sidebar()
        self.create_main_area()
        self.show_dashboard()
        
        # 3. FULLSCREEN - Tani do të funksionojë pasi dritarja është në 100%
        self.after(100, self.set_fullscreen)

    def set_fullscreen(self):
        """Hap dritaren në Fullscreen perfekt"""
        self.state('zoomed')
        self.update()

    def set_icon(self):
        try:
            from config.settings import IMAGES_DIR
            icon_path = os.path.join(IMAGES_DIR, "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except: pass

    def create_sidebar(self):
        # Sidebar pak më i ngushtë për të lënë hapësirë
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=("#F2F2F2", "#121212"))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="HOLKOS", font=ctk.CTkFont(size=22, weight="bold"), text_color="#FF6600").pack(pady=20)
        
        self.nav_buttons = {}
        nav_info = [
            ("Raporte", "📊", self.show_dashboard),
            ("Fatura të reja", "📝", self.show_invoice_form),
            ("Oferta", "📋", self.show_offer_form),
            ("Lista ofertave", "🗂️", self.show_offer_list),
            ("Lista faturave", "📑", self.show_invoice_list),
            ("Klientë", "👥", self.show_client_manager),
            ("Shabllona", "🎨", self.show_template_manager),
            ("Cilësime", "⚙️", self.show_settings)
        ]
        
        for text, icon, command in nav_info:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {text}", command=command,
                height=35, width=160, corner_radius=8, fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"),
                anchor="w", font=ctk.CTkFont(size=12, weight="bold"), cursor="hand2"
            )
            btn.pack(pady=2, padx=10)
            self.nav_buttons[text] = btn
            
        ctk.CTkLabel(self.sidebar, text="v1.1.0 Premium", font=ctk.CTkFont(size=10), text_color="gray").pack(side="bottom", pady=20)

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#FFFFFF")
        self.main_frame.pack(side="right", fill="both", expand=True)
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
        self.current_view = None

    def clear_content(self):
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def update_nav_styles(self, active_text):
        for text, btn in self.nav_buttons.items():
            if text == active_text:
                btn.configure(fg_color="#FF6600", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

    def show_dashboard(self):
        self.clear_content()
        self.current_view = DashboardView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Raporte")
    
    def show_invoice_form(self, invoice_id=None, is_clone=False):
        self.clear_content()
        self.current_view = InvoiceFormView(self.content_frame, invoice_id=invoice_id, is_clone=is_clone)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Fatura të reja")

    def show_offer_form(self, offer_id=None):
        self.clear_content()
        self.current_view = OfferFormView(self.content_frame, offer_id=offer_id)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Oferta")
    
    def show_offer_list(self):
        self.clear_content()
        self.current_view = OfferListView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Lista ofertave")
    
    def show_invoice_list(self):
        self.clear_content()
        self.current_view = InvoiceListView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Lista faturave")

    def show_client_manager(self):
        self.clear_content()
        self.current_view = ClientManagerView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Klientë")

    def show_template_manager(self):
        self.clear_content()
        self.current_view = TemplateManagerView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Shabllona")

    def show_settings(self):
        settings = SettingsWindow(self)
        settings.grab_set()
