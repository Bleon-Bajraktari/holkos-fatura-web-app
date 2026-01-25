import os
import datetime
import pymysql
import customtkinter as ctk
from tkinter import messagebox
from config.database import DatabaseConfig

class BackupManager:
    def __init__(self):
        self.config = DatabaseConfig()
        
    def create_backup(self, source='local', progress_callback=None):
        """Krijon një backup të plotë të databazës (Local ose Cloud)"""
        conn = None
        try:
            if source == 'local':
                label = "LOKAL"
                host = "localhost"
                port = 3306
                user = "root"
                password = ""
                db_name = "holkos_fatura1"
                ssl = None
            else:
                label = "CLOUD"
                host = self.config.host
                port = self.config.port
                user = self.config.user
                password = self.config.password
                db_name = self.config.database
                ssl = {'ssl': {}} if port == 4000 else None
            
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                ssl=ssl,
                connect_timeout=5
            )
            
            with conn.cursor() as cursor:
                # 1. Merr listën e tabelave
                cursor.execute("SHOW TABLES")
                # PyMySQL returns dict when DictCursor is used, or tuple if not. 
                # Let's handle both just in case.
                res = cursor.fetchall()
                tables = []
                for row in res:
                    tables.append(list(row.values())[0])
                
                if not tables:
                    return False, f"Nuk u gjetën tabela në {label}."
                
                # 2. Përgatit emrin e skedarit
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"backup_{label.lower()}_{timestamp}.sql"
                
                backup_content = [
                    f"-- Holkos Fatura {label} Backup",
                    f"-- Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                    f"USE `{db_name}`;\n"
                ]
                
                for i, table in enumerate(tables):
                    if progress_callback:
                        progress_callback(f"Duke ruajtur {label}: {table}...", (i / len(tables)))
                    
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
                
                return True, filename
                
        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                try: conn.close()
                except: pass

def run_gui():
    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.title("Backup Pro - Holkos Fatura")
    root.geometry("450x350")
    
    label = ctk.CTkLabel(root, text="Ruajtja e të Dhënave (Backup)", font=ctk.CTkFont(size=20, weight="bold"))
    label.pack(pady=20)
    
    info_label = ctk.CTkLabel(root, text="Zgjidhni burimin e të dhënave që dëshironi të ruani.\nKy proces krijon një skedar .sql si kopje rezervë.", font=ctk.CTkFont(size=12))
    info_label.pack(pady=10)
    
    progress_bar = ctk.CTkProgressBar(root, width=350)
    progress_bar.set(0)
    progress_bar.pack(pady=10)
    
    status_label = ctk.CTkLabel(root, text="Gati", font=ctk.CTkFont(size=10))
    status_label.pack()

    def start_backup(source):
        btn_local.configure(state="disabled")
        btn_cloud.configure(state="disabled")
        status_label.configure(text=f"Duke nisur backup {source}...")
        
        def update_progress(text, val):
            status_label.configure(text=text)
            progress_bar.set(val)
            root.update_idletasks()
            
        manager = BackupManager()
        success, result = manager.create_backup(source, update_progress)
        
        if success:
            progress_bar.set(1)
            messagebox.showinfo("Sukses", f"Backup {source.upper()} u krye!\nSkedari: {result}")
            root.destroy()
        else:
            messagebox.showerror("Gabim", f"Dështoi backup {source.upper()}:\n{result}")
            btn_local.configure(state="normal")
            btn_cloud.configure(state="normal")
            status_label.configure(text="Gabim!")

    btn_local = ctk.CTkButton(root, text="1. Backup LOKAL (XAMPP)", 
                             command=lambda: start_backup('local'), 
                             height=45, width=350,
                             fg_color="#34495E", hover_color="#2C3E50")
    btn_local.pack(pady=10)

    btn_cloud = ctk.CTkButton(root, text="2. Backup CLOUD (Internet)", 
                             command=lambda: start_backup('cloud'), 
                             height=45, width=350,
                             fg_color="#FF6600", hover_color="#E65C00")
    btn_cloud.pack(pady=5)
    
    ctk.CTkLabel(root, text="Këshillë: Ruani të dyja rregullisht.", font=ctk.CTkFont(size=10, slant="italic")).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    run_gui()
