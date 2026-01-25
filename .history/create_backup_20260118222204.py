import os
import datetime
import pymysql
import customtkinter as ctk
from tkinter import filedialog, messagebox
from config.database import DatabaseConfig

class BackupManager:
    def __init__(self):
        self.config = DatabaseConfig()
        
    def create_backup(self, progress_callback=None):
        """Krijon një backup të plotë të databazës lokale"""
        try:
            # Parametrat e lidhjes lokale
            host = "localhost"
            user = "root"
            password = ""
            db_name = "holkos_fatura1"
            
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # 1. Merr listën e tabelave
                cursor.execute("SHOW TABLES")
                tables = [list(row.values())[0] for row in cursor.fetchall()]
                
                if not tables:
                    return False, "Nuk u gjetën tabela për backup."
                
                # 2. Përgatit emrin e skedarit
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"backup_fatura_{timestamp}.sql"
                
                backup_content = [
                    f"-- Holkos Fatura Backup",
                    f"-- Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                    f"USE `{db_name}`;\n"
                ]
                
                for i, table in enumerate(tables):
                    if progress_callback:
                        progress_callback(f"Duke ruajtur tabelën: {table}...", (i / len(tables)))
                    
                    # Ruaj Strukturën
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    create_stmt = cursor.fetchone()
                    table_sql = list(create_stmt.values())[1]
                    backup_content.append(f"DROP TABLE IF EXISTS `{table}`;")
                    backup_content.append(f"{table_sql};\n")
                    
                    # Ruaj të Dhënat
                    cursor.execute(f"SELECT * FROM `{table}`")
                    rows = cursor.fetchall()
                    if rows:
                        cols = ", ".join([f"`{c}`" for c in rows[0].keys()])
                        backup_content.append(f"INSERT INTO `{table}` ({cols}) VALUES")
                        
                        val_list = []
                        for row in rows:
                            # Formato vlerat për SQL
                            vals = []
                            for v in row.values():
                                if v is None: vals.append("NULL")
                                elif isinstance(v, (int, float, complex)): vals.append(str(v))
                                else: vals.append(f"'{conn.escape_string(str(v))}'")
                            val_list.append(f"({', '.join(vals)})")
                        
                        backup_content.append(",\n".join(val_list) + ";\n")
                
                # 3. Ruaj në disk
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("\n".join(backup_content))
                
                conn.close()
                return True, filename
                
        except Exception as e:
            return False, str(e)

def run_gui():
    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.title("Backup - Holkos Fatura")
    root.geometry("400x250")
    
    label = ctk.CTkLabel(root, text="Ruajtja e të Dhënave (Backup)", font=ctk.CTkFont(size=18, weight="bold"))
    label.pack(pady=20)
    
    info_label = ctk.CTkLabel(root, text="Ky proces do të krijojë një skedar .sql me të gjitha\ntë dhënat tuaja lokale të faturave.", font=ctk.CTkFont(size=12))
    info_label.pack(pady=10)
    
    progress_bar = ctk.CTkProgressBar(root, width=300)
    progress_bar.set(0)
    progress_bar.pack(pady=10)
    
    status_label = ctk.CTkLabel(root, text="Gati", font=ctk.CTkFont(size=10))
    status_label.pack()

    def start_backup():
        btn.configure(state="disabled")
        status_label.configure(text="Duke nisur...")
        
        def update_progress(text, val):
            status_label.configure(text=text)
            progress_bar.set(val)
            root.update_idletasks()
            
        manager = BackupManager()
        success, result = manager.create_backup(update_progress)
        
        if success:
            progress_bar.set(1)
            messagebox.showinfo("Sukses", f"Backup u krye me sukses!\nSkedari: {result}")
            root.destroy()
        else:
            messagebox.showerror("Gabim", f"Dështoi krijimi i backup: {result}")
            btn.configure(state="normal")
            status_label.configure(text="Gabim!")

    btn = ctk.CTkButton(root, text="Krijo Backup Tani", command=start_backup, fg_color="#FF6600", hover_color="#E65C00")
    btn.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    run_gui()
