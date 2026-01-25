"""
Dritarja kryesore - v1.0.5 (Fix i detyruar për Fullscreen)
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
    def __init__(self):
        super().__init__()
        
        self.title("Holkos Fatura - v1.0.5")
        
        # Vendos madhësinë fillestare, por do ta maksimizojmë
        self.geometry("1000x600")
        
        # Scaling pak më i vogël (0.75) për t'ju dhënë më shumë hapësirë
        ctk.set_appearance_mode("light")
        ctk.set_widget_scaling(0.75) 
        ctk.set_window_scaling(0.75)
        
        self.set_icon()
        self.primary_color = "#FF6600"
        
        self.create_sidebar()
        self.create_main_area()
        self.show_dashboard()
        
        # DETYRIMI I FULLSCREEN (Metoda 1)
        self.after(200, self.force_maximize)
        
    def force_maximize(self):
        """Detyron dritaren në Fullscreen (Maximized)"""
        self.state('zoomed')
        self.update()

    def set_icon(self):
        try:
            if getattr(sys, 'frozen', False):
                bundle_dir = sys._MEIPASS
            else:
                bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(bundle_dir, "assets", "images", "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except: pass

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=("#F2F2F2", "#121212"))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="HOLKOS", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF6600").pack(pady=30)
        
        self.nav_buttons = {}
        nav_info = [
            ("Raporte", "📊", self.show_dashboard),
            ("Fatura të reja", "📝", self.show_invoice_form),
            ("Lista faturave", "📑", self.show_invoice_list),
            ("Klientë", "👥", self.show_client_manager),
            ("Shabllona", "🎨", self.show_template_manager)
        ]
        
        for text, icon, command in nav_info:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {text}", command=command,
                height=40, width=180, corner_radius=8, fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray80", "gray25"),
                anchor="w", font=ctk.CTkFont(size=13, weight="bold"), cursor="hand2"
            )
            btn.pack(pady=3, padx=10)
            self.nav_buttons[text] = btn
            
        ctk.CTkLabel(self.sidebar, text="v1.0.5 Premium", font=ctk.CTkFont(size=10), text_color="gray").pack(side="bottom", pady=20)

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
