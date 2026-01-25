
import customtkinter as ctk
from datetime import datetime

class TestView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.primary_color = "#FF6600"
        self.text_main = "#1A1A1A"
        self.text_secondary = "#6C757D"
        self.border_color = "#E9ECEF"
        self.bg_card = "#FFFFFF"
        
        self.rows_container = ctk.CTkFrame(self)
        self.rows_container.pack(fill="both", expand=True)
        self.items = []
        
        self.add_aligned_row(row_type='item')

    def add_aligned_row(self, initial_data=None, row_type='item'):
        row_id = datetime.now().timestamp()
        row_frame = ctk.CTkFrame(self.rows_container)
        row_frame.pack(fill="x")
        
        desc_text = ctk.CTkTextbox(row_frame, height=80)
        desc_text.pack(side="left")

        if row_type == 'item':
            right_side_container = ctk.CTkFrame(row_frame)
            right_side_container.pack(side="left")
            modules_list_frame = ctk.CTkFrame(right_side_container)
            modules_list_frame.pack()
            subtotal_label = ctk.CTkLabel(right_side_container, text="0.00")
            subtotal_label.pack()
        else:
            modules_list_frame = None
            subtotal_label = None

        item_entry = {
            'row': row_id, 'container': row_frame,
            'desc_text': desc_text,
            'row_type': row_type,
            'modules_container': modules_list_frame,
            'subtotal_label': subtotal_label,
            'modules': []
        }
        self.items.append(item_entry)
        if row_type == 'item':
            self.add_module_to_row(row_id, "Sasia", "")

    def add_module_to_row(self, row_id, label_text="", unit_text=""):
        item = next((i for i in self.items if i['row'] == row_id), None)
        mod_id = datetime.now().timestamp()
        mod_frame = ctk.CTkFrame(item['modules_container'])
        mod_frame.pack(side="left")
        
        input_container = ctk.CTkFrame(mod_frame)
        input_container.pack()
        
        val_entry = ctk.CTkEntry(input_container)
        val_entry.pack(side="left")
        
        unit_values = ["€", "m2"]
        unit_entry = ctk.CTkComboBox(input_container, width=65, height=24, font=ctk.CTkFont(size=10, weight="bold"), 
                                     values=unit_values,
                                     fg_color="#F8F9FA", border_width=0, button_color="#F8F9FA",
                                     button_hover_color="#E9ECEF", dropdown_font=ctk.CTkFont(size=10),
                                     text_color=self.primary_color)
        unit_entry.pack(side="left")
        print("ComboBox created successfully")

if __name__ == "__main__":
    root = ctk.CTk()
    view = TestView(root)
    view.pack()
    root.after(1000, root.destroy)
    root.mainloop()
