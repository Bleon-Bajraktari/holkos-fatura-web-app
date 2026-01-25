"""
Menaxhimi i shabllonave - v1.1.0 (Zoom Out)
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.template import Template

class TemplateManagerView(ctk.CTkFrame):
    """Menaxhimi i shabllonave - Zoom Out"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="#FFFFFF")
        
        self.db = Database()
        self.db.connect()
        
        self.selected_template_id = None
        
        self.create_widgets()
        self.load_templates()
    
    def create_widgets(self):
        """Ndërtimi - Zoom Out"""
        # Titulli (Reduktuar)
        title = ctk.CTkLabel(
            self,
            text="Menaxhimi i Shabllonave",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(15, 5))
        
        info_label = ctk.CTkLabel(
            self,
            text="Shablloni default është i integruar në sistem. Mund të shtoni shabllona të reja në të ardhmen.",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))
        
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        scrollable_table = ctk.CTkScrollableFrame(table_container, fg_color="white", border_width=1, border_color="#E9ECEF")
        scrollable_table.pack(fill="both", expand=True)
        
        self.table_frame = ctk.CTkFrame(scrollable_table, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        headers = ["Emri", "Përshkrimi", "Aktiv", "Default", "Veprimet"]
        header_frame = ctk.CTkFrame(self.table_frame, fg_color="#F8F9FA", height=35)
        header_frame.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 5))
        
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#6C757D"
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            header_frame.grid_columnconfigure(i, weight=1 if i < 4 else 0)
            self.table_frame.grid_columnconfigure(i, weight=1 if i < 4 else 0)
    
    def load_templates(self):
        for widget in self.table_frame.winfo_children():
            if widget.grid_info().get('row', 0) > 0: widget.destroy()
        
        templates = Template.get_all(self.db)
        if not templates:
            self.create_default_template()
            templates = Template.get_all(self.db)
        
        for i, template in enumerate(templates, start=1):
            self.add_template_row(i, template)
    
    def create_default_template(self):
        template = Template(self.db)
        template.name = "Shablloni Default"; template.template_file = "default"
        template.description = "Shablloni bazë i faturave bazuar në dizajnin e HOLKOS"
        template.is_active = True; template.is_default = True
        template.save()
    
    def add_template_row(self, row, template):
        ctk.CTkLabel(self.table_frame, text=template['name'], font=ctk.CTkFont(size=11, weight="bold")).grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(self.table_frame, text=template.get('description', ''), font=ctk.CTkFont(size=11)).grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        
        active_text = "Po" if template['is_active'] else "Jo"
        ctk.CTkLabel(self.table_frame, text=active_text, font=ctk.CTkFont(size=11), text_color="#2ECC71" if template['is_active'] else "#E74C3C").grid(row=row, column=2, padx=5, pady=5, sticky="ew")
        
        default_text = "Po" if template['is_default'] else "Jo"
        ctk.CTkLabel(self.table_frame, text=default_text, font=ctk.CTkFont(size=11), text_color="#FF6600" if template['is_default'] else "gray").grid(row=row, column=3, padx=5, pady=5, sticky="ew")
        
        actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        actions_frame.grid(row=row, column=4, padx=5, pady=5)
        
        if not template['is_default']:
            ctk.CTkButton(actions_frame, text="Default", width=60, height=24, command=lambda t_id=template['id']: self.set_default(t_id), font=ctk.CTkFont(size=10), fg_color="#FF6600", cursor="hand2").pack(side="left", padx=2)
        
        ctk.CTkButton(actions_frame, text="Aktivizo", width=70, height=24, command=lambda t_id=template['id']: self.toggle_active(t_id), font=ctk.CTkFont(size=10), fg_color="#555555" if template['is_active'] else "#FF6600", cursor="hand2").pack(side="left", padx=2)

    def set_default(self, template_id):
        template = Template.get_by_id(template_id, self.db)
        if template and template.set_as_default(): self.load_templates()
    
    def toggle_active(self, template_id):
        template = Template.get_by_id(template_id, self.db)
        if template:
            template.is_active = not template.is_active
            if template.save(): self.load_templates()
