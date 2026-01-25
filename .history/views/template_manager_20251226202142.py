"""
Menaxhimi i shabllonave
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.template import Template

class TemplateManagerView(ctk.CTkFrame):
    """Menaxhimi i shabllonave"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.db = Database()
        self.db.connect()
        
        self.selected_template_id = None
        
        self.create_widgets()
        self.load_templates()
    
    def create_widgets(self):
        """Krijon widget-et"""
        # Titulli
        title = ctk.CTkLabel(
            self,
            text="Menaxhimi i Shabllonave",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Info
        info_label = ctk.CTkLabel(
            self,
            text="Shablloni default është i integruar në sistem. Mund të shtoni shabllona të reja në të ardhmen.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # Tabela e shabllonave (me scroll)
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        scrollable_table = ctk.CTkScrollableFrame(table_container)
        scrollable_table.pack(fill="both", expand=True)
        
        table_frame = ctk.CTkFrame(scrollable_table)
        table_frame.pack(fill="both", expand=True)
        
        # Header
        headers = ["Emri", "Përshkrimi", "Aktiv", "Default", "Veprimet"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
            table_frame.grid_columnconfigure(i, weight=1 if i < 4 else 0)
        
        self.table_frame = table_frame
    
    def load_templates(self):
        """Ngarkon shabllonat"""
        # Pastro tabelën
        for widget in self.table_frame.winfo_children():
            if widget.grid_info()['row'] > 0:
                widget.destroy()
        
        # Merr shabllonat
        templates = Template.get_all(self.db)
        
        # Nëse nuk ka shabllona, krijo default
        if not templates:
            self.create_default_template()
            templates = Template.get_all(self.db)
        
        # Shfaq në tabelë
        for i, template in enumerate(templates, start=1):
            self.add_template_row(i, template)
    
    def create_default_template(self):
        """Krijon shabllonin default"""
        template = Template(self.db)
        template.name = "Shablloni Default"
        template.description = "Shablloni bazë i faturave bazuar në dizajnin e HOLKOS"
        template.template_file = "default"
        template.is_active = True
        template.is_default = True
        template.save()
    
    def add_template_row(self, row, template):
        """Shton një rresht shablloni në tabelë"""
        # Emri
        name_label = ctk.CTkLabel(
            self.table_frame,
            text=template['name'],
            font=ctk.CTkFont(size=11)
        )
        name_label.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        
        # Përshkrimi
        desc_label = ctk.CTkLabel(
            self.table_frame,
            text=template.get('description', ''),
            font=ctk.CTkFont(size=11)
        )
        desc_label.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        
        # Aktiv
        active_text = "Po" if template['is_active'] else "Jo"
        active_label = ctk.CTkLabel(
            self.table_frame,
            text=active_text,
            font=ctk.CTkFont(size=11),
            text_color="green" if template['is_active'] else "red"
        )
        active_label.grid(row=row, column=2, padx=5, pady=5, sticky="ew")
        
        # Default
        default_text = "Po" if template['is_default'] else "Jo"
        default_label = ctk.CTkLabel(
            self.table_frame,
            text=default_text,
            font=ctk.CTkFont(size=11),
            text_color="#FF6600" if template['is_default'] else "gray"
        )
        default_label.grid(row=row, column=3, padx=5, pady=5, sticky="ew")
        
        # Veprimet
        actions_frame = ctk.CTkFrame(self.table_frame)
        actions_frame.grid(row=row, column=4, padx=5, pady=5)
        
        if not template['is_default']:
            btn_set_default = ctk.CTkButton(
                actions_frame,
                text="Vendos Default",
                width=100,
                height=25,
                command=lambda t_id=template['id']: self.set_default(t_id),
                font=ctk.CTkFont(size=10),
                fg_color="#FF6600",
                hover_color="#FF8533"
            )
            btn_set_default.pack(side="left", padx=2)
        
        btn_toggle = ctk.CTkButton(
            actions_frame,
            text="Aktivizo/Deaktivizo",
            width=120,
            height=25,
            command=lambda t_id=template['id']: self.toggle_active(t_id),
            font=ctk.CTkFont(size=10),
            fg_color="orange" if template['is_active'] else "gray",
            hover_color="darkorange"
        )
        btn_toggle.pack(side="left", padx=2)
    
    def set_default(self, template_id):
        """Vendos shabllonin si default"""
        template = Template.get_by_id(template_id, self.db)
        if template and template.set_as_default():
            messagebox.showinfo("Sukses", "Shablloni u vendos si default!")
            self.load_templates()
        else:
            messagebox.showerror("Gabim", "Gabim në vendosjen e shabllonit si default!")
    
    def toggle_active(self, template_id):
        """Aktivizon/deaktivizon shabllonin"""
        template = Template.get_by_id(template_id, self.db)
        if template:
            template.is_active = not template.is_active
            if template.save():
                messagebox.showinfo("Sukses", "Statusi i shabllonit u përditësua!")
                self.load_templates()
            else:
                messagebox.showerror("Gabim", "Gabim në përditësimin e shabllonit!")

