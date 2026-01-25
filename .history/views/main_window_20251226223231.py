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

class MainWindow(ctk.CTk):
    """Dritarja kryesore e aplikacionit"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Holkos Fatura - Sistem Fatura PDF")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        # Konfiguro theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Krijimi i layout-it
        self.create_menu_bar()
        self.create_sidebar()
        self.create_main_area()
        
        # Shfaq dashboard-in si default
        self.show_dashboard()
    
    def create_menu_bar(self):
        """Krijon menu bar"""
        # Menu bar do të shtohet më vonë nëse nevojitet
        pass
    
    def create_sidebar(self):
        """Krijon sidebar për navigim"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)
        
        # Logo ose titull
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="HOLKOS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FF6600"
        )
        title_label.pack(pady=20)
        
        subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Sistem Fatura",
            font=ctk.CTkFont(size=12)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Butonat e navigimit
        nav_buttons = [
            ("Dashboard", self.show_dashboard),
            ("Fatura të reja", self.show_invoice_form),
            ("Lista faturave", self.show_invoice_list),
            ("Klientë", self.show_client_manager),
            ("Shabllona", self.show_template_manager),
            ("Cilësime", self.show_settings)
        ]
        
        self.nav_buttons = {}
        for text, command in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                width=180,
                height=40,
                corner_radius=5,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w"
            )
            btn.pack(pady=5, padx=10)
            self.nav_buttons[text] = btn
    
    def create_main_area(self):
        """Krijon zonën kryesore për përmbajtjen"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Frame për përmbajtjen aktive (pa padding që të përdorë të gjithë hapësirën)
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        self.current_view = None
    
    def clear_content(self):
        """Pastron përmbajtjen aktuale - optimizuar"""
        if self.current_view:
            # Në vend që të fshijë menjëherë, fshihet në background
            try:
                self.current_view.destroy()
            except:
                pass
            self.current_view = None
    
    def show_dashboard(self):
        """Shfaq dashboard-in"""
        self.clear_content()
        self.current_view = DashboardView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_button("Dashboard")
    
    def show_invoice_form(self):
        """Shfaq formularin për krijimin e faturave"""
        self.clear_content()
        self.current_view = InvoiceFormView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_button("Fatura të reja")
    
    def show_invoice_list(self):
        """Shfaq listën e faturave"""
        self.clear_content()
        self.current_view = InvoiceListView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_button("Lista faturave")
    
    def show_client_manager(self):
        """Shfaq menaxhimin e klientëve"""
        self.clear_content()
        self.current_view = ClientManagerView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_button("Klientë")
    
    def show_template_manager(self):
        """Shfaq menaxhimin e shabllonave"""
        self.clear_content()
        self.current_view = TemplateManagerView(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.update_nav_button("Shabllona")
    
    def show_settings(self):
        """Shfaq cilësimet"""
        # Cilësimet në dritare të veçantë
        settings = SettingsWindow(self)
        settings.grab_set()  # Modal window
    
    def update_nav_button(self, active_button):
        """Përditëson pamjen e butonit aktiv"""
        for text, btn in self.nav_buttons.items():
            if text == active_button:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

