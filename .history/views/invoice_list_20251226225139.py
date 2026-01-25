"""
Lista e faturave
"""
import customtkinter as ctk
from tkinter import messagebox
from models.database import Database
from models.invoice import Invoice
from services.pdf_generator import PDFGenerator
from views.invoice_form import InvoiceFormView

class InvoiceListView(ctk.CTkFrame):
    """Lista e faturave me filtra dhe veprime"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.db = Database()
        self.db.connect()
        
        self.create_widgets()
        self.load_invoices()
    
    def create_widgets(self):
        """Krijon widget-et"""
        # Titulli
        title = ctk.CTkLabel(
            self,
            text="Lista e Faturave",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Frame për filtra
        filters_frame = ctk.CTkFrame(self)
        filters_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        # Kërkimi - me debouncing për performance më të mirë
        ctk.CTkLabel(filters_frame, text="Kërko:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=10, pady=10)
        self.search_entry = ctk.CTkEntry(filters_frame, width=200)
        self.search_entry.grid(row=0, column=1, padx=10, pady=10)
        self.search_timer = None
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # Statusi
        ctk.CTkLabel(filters_frame, text="Statusi:", font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=10, pady=10)
        self.status_var = ctk.StringVar(value="Të gjitha")
        status_combo = ctk.CTkComboBox(
            filters_frame,
            values=["Të gjitha", "draft", "sent", "paid"],
            variable=self.status_var,
            width=150,
            command=lambda x: self.load_invoices()
        )
        status_combo.grid(row=0, column=3, padx=10, pady=10)
        
        # Butoni për refresh
        btn_refresh = ctk.CTkButton(
            filters_frame,
            text="Refresh",
            command=self.load_invoices,
            width=100
        )
        btn_refresh.grid(row=0, column=4, padx=10, pady=10)
        
        # Frame për tabelën (me scroll vetëm për tabelën)
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Scrollable frame vetëm për tabelën
        self.scrollable_table = ctk.CTkScrollableFrame(table_container)
        self.scrollable_table.pack(fill="both", expand=True)
        
        self.table_frame = ctk.CTkFrame(self.scrollable_table)
        self.table_frame.pack(fill="both", expand=True)
        
        # Header
        headers = ["Numri", "Data", "Klienti", "Totali", "Statusi", "Veprimet"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
            self.table_frame.grid_columnconfigure(i, weight=1 if i < 5 else 0)
        
        self.invoice_rows = []
        self.client_groups = {}  # Ruaj referencat e grupeve
        self._last_toggle_time = 0  # Për debouncing
    
    def on_search_change(self, event):
        """Debounced search - prit 300ms para se të ekzekutojë kërkimin"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.load_invoices)
    
    def load_invoices(self):
        """Ngarkon faturat dhe i grupon sipas blerësit me dropdown - optimizuar"""
        # Pastro tabelën - optimizuar
        widgets_to_destroy = []
        for widget in self.table_frame.winfo_children():
            widget_info = widget.grid_info()
            if widget_info.get('row', 0) > 0:
                widgets_to_destroy.append(widget)
        
        # Fshi në batch për performance më të mirë
        for widget in widgets_to_destroy:
            try:
                widget.destroy()
            except:
                pass
        
        self.invoice_rows = []
        self.client_groups = {}  # Ruaj referencat e grupeve
        
        # Filtra
        filters = {}
        search_term = self.search_entry.get()
        if search_term:
            filters['search'] = search_term
        
        status = self.status_var.get()
        if status != "Të gjitha":
            filters['status'] = status
        
        # Merr faturaet - pa limit për të shfaqur të gjitha
        invoices = Invoice.get_all(self.db, filters)
        
        # Grupo sipas klientit - optimizuar
        grouped_invoices = {}
        for invoice in invoices:
            client_name = invoice.get('client_name', 'Pa klient')
            if client_name not in grouped_invoices:
                grouped_invoices[client_name] = []
            grouped_invoices[client_name].append(invoice)
        
        # Shfaq në tabelë me dropdown për çdo klient - me lazy rendering
        current_row = 1
        sorted_clients = sorted(grouped_invoices.items())
        
        # Krijo vetëm header-et fillimisht (lazy loading)
        for client_name, client_invoices in sorted_clients:
            # Llogarit totalin për këtë klient - optimizuar
            client_total = sum(float(inv['total']) for inv in client_invoices)
            
            # Krijo dropdown për klientin (vetëm header, jo faturaet)
            self.add_client_dropdown(current_row, client_name, len(client_invoices), client_total, client_invoices)
            current_row += 1
    
    def add_client_dropdown(self, row, client_name, count, client_total, invoices):
        """Shton dropdown për grupin e klientit me ngjyrë unike"""
        # Ngjyra të ndryshme për çdo klient (bazuar në hash të emrit)
        colors = [
            "#2B2B2B",  # Gri i errët
            "#1E3A5F",  # Blu i errët
            "#3D5A3D",  # Gjelbër i errët
            "#5A3D3D",  # Kafe i errët
            "#3D3D5A",  # Vjollcë i errët
            "#5A5A3D",  # Verdhë i errët
            "#5A3D5A",  # Rozë i errët
            "#3D5A5A",  # Cyan i errët
        ]
        
        # Përdor hash të emrit për të zgjedhur ngjyrën
        color_index = hash(client_name) % len(colors)
        bg_color = colors[color_index]
        
        # Frame për header të dropdown-it
        header_frame = ctk.CTkFrame(
            self.table_frame,
            fg_color=bg_color,
            corner_radius=5
        )
        header_frame.grid(row=row, column=0, columnspan=6, sticky="ew", padx=5, pady=(5, 0))
        
        # Butoni për hapje/mbyllje - me ruajtje të widget-ve për performance më të mirë
        self.client_groups[client_name] = {
            'expanded': False,
            'header_frame': header_frame,
            'invoices': invoices,
            'row': row,
            'widgets': []  # Ruaj referencat e widget-ve për këtë grup
        }
        
        # Emri i klientit dhe numri i faturave
        header_text = f"▶ {client_name} ({count} fatura{'e' if count > 1 else ''})"
        header_label = ctk.CTkLabel(
            header_frame,
            text=header_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            cursor="hand2"
        )
        header_label.pack(side="left", padx=10, pady=8)
        
        # Totali për këtë klient
        total_text = f"Total: {client_total:,.2f} €".replace(",", " ")
        total_label = ctk.CTkLabel(
            header_frame,
            text=total_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="e"
        )
        total_label.pack(side="right", padx=10, pady=8)
        
        # Bëj vetëm header_frame të klikueshëm (jo çdo widget) për të shmangur event propagation
        def on_header_click(event):
            # Debouncing për të shmangur ekzekutimin e shumëfishtë
            import time
            current_time = time.time()
            if current_time - self._last_toggle_time < 0.3:  # 300ms debounce
                return
            self._last_toggle_time = current_time
            self.toggle_client_group(client_name)
        
        # Bind vetëm në header_frame, jo në widget-et e brendshëm për të shmangur propagation
        header_frame.bind("<Button-1>", on_header_click)
        header_frame.configure(cursor="hand2")
    
    def toggle_client_group(self, client_name):
        """Hap/mbyll grupin e faturave për një klient - version i thjeshtuar"""
        if client_name not in self.client_groups:
            return
        
        group = self.client_groups[client_name]
        was_expanded = group.get('expanded', False)
        group['expanded'] = not was_expanded
        
        if group['expanded']:
            # Hap - shto faturaet nëse nuk janë krijuar ende (lazy loading)
            if 'widgets' not in group or not group['widgets']:
                start_row = group['row'] + 1
                group['widgets'] = []
                invoices = group['invoices']
                
                # Krijo widget-et në batch për performance më të mirë
                for i, invoice in enumerate(invoices):
                    row = start_row + i
                    widgets = self.add_invoice_row(row, invoice, client_name)
                    if widgets:
                        group['widgets'].append(widgets)
            else:
                # Widget-et ekzistojnë, thjesht i shfaq
                start_row = group['row'] + 1
                for i, widgets in enumerate(group['widgets']):
                    row = start_row + i
                    col = 0
                    for widget in widgets:
                        try:
                            # Ri-shfaq widget-in
                            if isinstance(widget, ctk.CTkFrame):
                                widget.grid(row=row, column=5, padx=5, pady=5)
                            else:
                                widget.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                                col += 1
                        except Exception as e:
                            print(f"Error showing widget: {e}")
        else:
            # Mbyll - fshi vetëm widget-et e këtij grupi
            if 'widgets' in group:
                for widgets in group['widgets']:
                    for widget in widgets:
                        try:
                            widget.grid_remove()
                        except:
                            pass
        
        # Përditëso ikonën e dropdown-it
        header_label = None
        for widget in group['header_frame'].winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                text = widget.cget("text")
                if "▶" in text or "▼" in text:
                    header_label = widget
                    break
        
        if header_label:
            current_text = header_label.cget("text")
            if group['expanded']:
                new_text = current_text.replace("▶", "▼")
            else:
                new_text = current_text.replace("▼", "▶")
            header_label.configure(text=new_text)
    
    def add_invoice_row(self, row, invoice, client_group=None):
        """Shton një rresht fatura në tabelë"""
        # Krijo listë për të ruajtur widget-et
        widgets = []
        
        # Numri
        num_label = ctk.CTkLabel(
            self.table_frame,
            text=invoice['invoice_number'],
            font=ctk.CTkFont(size=11)
        )
        if client_group:
            num_label.client_group = client_group
        num_label.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        widgets.append(num_label)
        
        # Data
        date_str = invoice['date'].strftime("%d.%m.%Y") if invoice.get('date') else ""
        date_label = ctk.CTkLabel(
            self.table_frame,
            text=date_str,
            font=ctk.CTkFont(size=11)
        )
        if client_group:
            date_label.client_group = client_group
        date_label.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        widgets.append(date_label)
        
        # Klienti
        client_label = ctk.CTkLabel(
            self.table_frame,
            text=invoice.get('client_name', ''),
            font=ctk.CTkFont(size=11)
        )
        if client_group:
            client_label.client_group = client_group
        client_label.grid(row=row, column=2, padx=5, pady=5, sticky="ew")
        widgets.append(client_label)
        
        # Totali
        total_value = float(invoice.get('total', 0))
        total_str = f"{total_value:,.2f} €".replace(",", " ")
        total_label = ctk.CTkLabel(
            self.table_frame,
            text=total_str,
            font=ctk.CTkFont(size=11)
        )
        if client_group:
            total_label.client_group = client_group
        total_label.grid(row=row, column=3, padx=5, pady=5, sticky="ew")
        widgets.append(total_label)
        
        # Statusi
        status_label = ctk.CTkLabel(
            self.table_frame,
            text=invoice.get('status', ''),
            font=ctk.CTkFont(size=11)
        )
        if client_group:
            status_label.client_group = client_group
        status_label.grid(row=row, column=4, padx=5, pady=5, sticky="ew")
        widgets.append(status_label)
        
        # Veprimet
        actions_frame = ctk.CTkFrame(self.table_frame)
        if client_group:
            actions_frame.client_group = client_group
        actions_frame.grid(row=row, column=5, padx=5, pady=5)
        
        # Butonat - me caching të command-ave për performance
        inv_id = invoice.get('id')
        
        btn_view = ctk.CTkButton(
            actions_frame,
            text="Shiko",
            width=60,
            height=25,
            command=lambda: self.view_invoice(inv_id),
            font=ctk.CTkFont(size=10)
        )
        btn_view.pack(side="left", padx=2)
        
        btn_edit = ctk.CTkButton(
            actions_frame,
            text="Redakto",
            width=60,
            height=25,
            command=lambda: self.edit_invoice(inv_id),
            font=ctk.CTkFont(size=10),
            fg_color="orange",
            hover_color="darkorange"
        )
        btn_edit.pack(side="left", padx=2)
        
        btn_pdf = ctk.CTkButton(
            actions_frame,
            text="PDF",
            width=50,
            height=25,
            command=lambda: self.generate_pdf(inv_id),
            font=ctk.CTkFont(size=10),
            fg_color="#FF6600",
            hover_color="#FF8533"
        )
        btn_pdf.pack(side="left", padx=2)
        
        btn_delete = ctk.CTkButton(
            actions_frame,
            text="Fshi",
            width=50,
            height=25,
            command=lambda: self.delete_invoice(inv_id),
            font=ctk.CTkFont(size=10),
            fg_color="red",
            hover_color="darkred"
        )
        btn_delete.pack(side="left", padx=2)
        
        widgets_list = widgets + [actions_frame]
        
        self.invoice_rows.append({
            'invoice': invoice,
            'widgets': widgets_list
        })
        
        # Kthe listën e widget-ve për ruajtje në grup
        return widgets_list
    
    def view_invoice(self, invoice_id):
        """Shfaq faturave"""
        invoice = Invoice.get_by_id(invoice_id, self.db)
        if invoice:
            # Shfaq në dritare të re
            view_window = ctk.CTkToplevel(self)
            view_window.title(f"Fatura {invoice.invoice_number}")
            view_window.geometry("1000x700")
            
            form = InvoiceFormView(view_window, invoice_id=invoice_id)
            form.pack(fill="both", expand=True)
    
    def edit_invoice(self, invoice_id):
        """Redakton faturave"""
        # Hap dritare të re për redaktim
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Redakto Fatura")
        edit_window.geometry("1000x700")
        
        form = InvoiceFormView(edit_window, invoice_id=invoice_id)
        form.pack(fill="both", expand=True)
    
    def generate_pdf(self, invoice_id):
        """Gjeneron PDF për faturave"""
        invoice = Invoice.get_by_id(invoice_id, self.db)
        if not invoice:
            messagebox.showerror("Gabim", "Fatura nuk u gjet!")
            return
        
        try:
            generator = PDFGenerator()
            output_path = generator.generate(invoice)
            messagebox.showinfo("Sukses", f"PDF u gjenerua me sukses!\n{output_path}")
        except Exception as e:
            messagebox.showerror("Gabim", f"Gabim në gjenerimin e PDF: {str(e)}")
    
    def delete_invoice(self, invoice_id):
        """Fshin faturave"""
        if not messagebox.askyesno("Konfirmim", "Jeni të sigurt që dëshironi të fshini këtë fatura?"):
            return
        
        invoice = Invoice.get_by_id(invoice_id, self.db)
        if invoice and invoice.delete():
            messagebox.showinfo("Sukses", "Fatura u fshi me sukses!")
            self.load_invoices()
        else:
            messagebox.showerror("Gabim", "Gabim në fshirjen e faturave!")

