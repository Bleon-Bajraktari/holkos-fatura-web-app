"""
Mjet për pastrimin e faturave kudo (Cloud & Lokal)
"""
import customtkinter as ctk
from models.database import Database
import tkinter.messagebox as msgbox

class CleanupApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pastruesi i Faturave - Holkos")
        self.geometry("800x600")
        
        self.db = Database()
        self.db.connect()
        
        self.label = ctk.CTkLabel(self, text="Zgjidhni faturat që dëshironi të FSHINI përgjithmonë (Cloud & Lokal)", font=("Arial", 16, "bold"))
        self.label.pack(pady=20)
        
        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_list()
        
        self.delete_btn = ctk.CTkButton(self, text="FSHI TË GJITHA FATURAT (Reset Total)", fg_color="red", command=self.wipe_all)
        self.delete_btn.pack(pady=20)

    def refresh_list(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
            
        # 1. Merr të dhënat nga Cloud
        cloud_invoices = {}
        if self.db.connection:
            try:
                with self.db.connection.cursor() as cursor:
                    cursor.execute("SELECT id, invoice_number, date, total FROM invoices")
                    cloud_invoices = {row['id']: row for row in cursor.fetchall()}
            except: pass

        # 2. Merr të dhënat nga Lokali
        local_invoices = {}
        if self.db.backup_connection:
            try:
                with self.db.backup_connection.cursor() as cursor:
                    cursor.execute("SELECT id, invoice_number, date, total FROM invoices")
                    local_invoices = {row['id']: row for row in cursor.fetchall()}
            except: pass

        # Bashko ID-të
        all_ids = sorted(list(set(list(cloud_invoices.keys()) + list(local_invoices.keys()))), reverse=True)
        
        if not all_ids:
            ctk.CTkLabel(self.frame, text="Nuk u gjet asnjë faturë.").pack(pady=20)
            return

        for inv_id in all_ids:
            row = ctk.CTkFrame(self.frame)
            row.pack(fill="x", pady=2, padx=5)
            
            # Përcakto statusin
            in_cloud = inv_id in cloud_invoices
            in_local = inv_id in local_invoices
            
            data = cloud_invoices.get(inv_id) or local_invoices.get(inv_id)
            
            if in_cloud and in_local:
                status_text = " [ CLOUD + LOKAL ] "
                status_color = "#2ecc71" # Jeshile
            elif in_cloud:
                status_text = " [ VETËM NË CLOUD ] "
                status_color = "#3498db" # Blu
            else:
                status_text = " [ VETËM NË LOKAL ] "
                status_color = "#e67e22" # Portokalli (Ghost Lokal)

            txt = f"ID: {inv_id} | {data['invoice_number']} | Data: {data['date']} | {data['total']} €"
            
            lbl_status = ctk.CTkLabel(row, text=status_text, text_color=status_color, font=("Arial", 10, "bold"), width=120)
            lbl_status.pack(side="left", padx=5)
            
            lbl_data = ctk.CTkLabel(row, text=txt)
            lbl_data.pack(side="left", padx=10)
            
            btn = ctk.CTkButton(row, text="Fshi", width=60, fg_color="#cc0000", command=lambda i=inv_id: self.delete_one(i))
            btn.pack(side="right", padx=10)


    def delete_one(self, inv_id):
        if msgbox.askyesno("Kujdes", "A jeni i sigurt që doni ta fshini këtë faturë?"):
            self.db.execute_query("DELETE FROM invoices WHERE id = %s", (inv_id,))
            # Commit sync
            if self.db.connection: self.db.connection.commit()
            if self.db.backup_connection: self.db.backup_connection.commit()
            self.refresh_list()

    def wipe_all(self):
        if msgbox.askyesno("RREZIK", "Kjo do të fshijë TË GJITHA faturat dhe ofertat nga sistemi (Cloud dhe Lokal). Vazhdo?"):
            try:
                self.db.execute_query("DELETE FROM invoice_items")
                self.db.execute_query("DELETE FROM invoices")
                self.db.execute_query("DELETE FROM offer_items")
                self.db.execute_query("DELETE FROM offers")
                
                if self.db.connection: self.db.connection.commit()
                if self.db.backup_connection: self.db.backup_connection.commit()
                
                msgbox.showinfo("Sukses", "Sistemi u pastrua plotësisht.")
                self.refresh_list()
            except Exception as e:
                msgbox.showerror("Gabim", str(e))

if __name__ == "__main__":
    app = CleanupApp()
    app.mainloop()
