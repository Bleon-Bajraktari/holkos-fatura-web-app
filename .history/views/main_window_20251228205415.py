"""
Dritarja kryesore e aplikacionit
"""
import customtkinter as ctk
from views.dashboard import DashboardView
from views.invoice_form import InvoiceFormView
from views.invoice_list import InvoiceListView
from views.client_manager import ClientManagerView
from views.template_manager import TemplateManagerView
from views.settings_window import SettingsWindow

import os
import sys

class MainWindow(ctk.CTk):
    """Dritarja kryesore e aplikacionit"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Holkos Fatura - Sistem Inteligjent i Faturimit")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Vendos ikonën
        self.set_icon()
        
        # Ngjyrat Premium
        self.primary_color = "#FF6600"
        self.hover_color = "#FF8533"
        self.bg_color = ("#FFFFFF", "#1A1A1A")
        self.sidebar_color = ("#F2F2F2", "#121212")
        
        # UI Scaling (Zoom Out)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(0.8)
        ctk.set_window_scaling(0.8)
        
        # Layout
        self.create_sidebar()
        self.create_main_area()
        
        # Default View
        self.show_dashboard()
        
        # Hapeni në fullscreen me vonesë dhe update të detyruar
        self.update_idletasks()
        self.after(500, self.force_fullscreen)
    
    def force_fullscreen(self):
        """Detyron hapjen në fullscreen"""
        self.state('zoomed')
    
    def set_icon(self):
        """Vendos ikonën e dritares"""
        try:
            if getattr(sys, 'frozen', False):
                bundle_dir = sys._MEIPASS
            else:
                bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            icon_path = os.path.join(bundle_dir, "assets", "images", "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Nuk u ngarkua ikona: {e}")
    
    def create_sidebar(self):
        """Krijon sidebar për navigim me stil modern"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 30), padx=20, fill="x")
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="HOLKOS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.primary_color
        )
        logo_label.pack(anchor="w")
        
        # Navigimi
        self.nav_buttons = {}
        nav_info = [
            ("Raporte", "📊", self.show_dashboard),
            ("Fatura të reja", "📝", self.show_invoice_form),
            ("Lista faturave", "📑", self.show_invoice_list),
            ("Klientë", "👥", self.show_client_manager),
            ("Shabllona", "🎨", self.show_template_manager),
            ("Cilësime", "⚙️", self.show_settings)
        ]
        
        for text, icon, command in nav_info:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {text}",
                command=command,
                height=40,
                width=180,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                cursor="hand2"
            )
            btn.pack(pady=3, padx=10)
            self.nav_buttons[text] = btn
            
        # Version Info
        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.0.3 Premium",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(side="bottom", pady=20)
    
    def create_main_area(self):
        """Zona kryesore ku shfaqet përmbajtja"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.bg_color)
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
        
        self.current_view = None
    
    def clear_content(self):
        """Pastron dritaren për pamjen e re"""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None
    
    def update_nav_styles(self, active_text):
        """Përditëson stilin e butonave të navigimit"""
        for text, btn in self.nav_buttons.items():
            if text == active_text:
                btn.configure(fg_color=self.primary_color, text_color="white", hover_color=self.primary_color)
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"))

    def show_dashboard(self):
        self.clear_content()
        self.current_view = DashboardView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Raporte")
    
    def show_invoice_form(self, invoice_id=None):
        self.clear_content()
        self.current_view = InvoiceFormView(self.content_frame, invoice_id=invoice_id)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_styles("Fatura të reja")
    
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
