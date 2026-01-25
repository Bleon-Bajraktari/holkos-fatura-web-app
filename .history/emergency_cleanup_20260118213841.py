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
            
        invoices = self.db.execute_query("SELECT id, invoice_number, date, total FROM invoices ORDER BY date DESC, id DESC")
        
        if not invoices:
            ctk.CTkLabel(self.frame, text="Nuk u gjet asnjë faturë.").pack()
            return

        for inv in invoices:
            row = ctk.CTkFrame(self.frame)
            row.pack(fill="x", pady=2, padx=5)
            
            txt = f"ID: {inv['id']} | {inv['invoice_number']} | Data: {inv['date']} | Shuma: {inv['total']} €"
            ctk.CTkLabel(row, text=txt).pack(side="left", padx=10)
            
            btn = ctk.CTkButton(row, text="Fshi", width=60, fg_color="#cc0000", command=lambda i=inv['id']: self.delete_one(i))
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
