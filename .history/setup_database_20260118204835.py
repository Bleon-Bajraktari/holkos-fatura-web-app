"""
Skript për setup të databazës
Ekzekuto këtë skript për të krijuar databazën dhe tabelat
"""
import mysql.connector
from mysql.connector import Error
import os
from config.database import DatabaseConfig
from config.settings import SQL_DIR

def create_database(is_backup=False):
    """Krijon databazën dhe tabelat (Primary ose Backup)"""
    config = DatabaseConfig()
    
    # Përcakto parametrat e lidhjes
    if is_backup:
        db_label = "LOKALE (Backup)"
        host = "localhost"
        port = 3306
        user = "root"
        password = ""
        db_name = "holkos_fatura1"
    else:
        db_label = "CLOUD (Primary)"
        host = config.host
        port = config.port
        user = config.user
        password = config.password
        db_name = config.database

    try:
        # Lidhu me MySQL
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 1. Krijo databazën
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            # print(f"✓ Databaza {db_label} '{db_name}' u kontrollua.")
            
            # 2. Përdor databazën
            cursor.execute(f"USE {db_name}")
            
            # 3. Lexo dhe ekzekuto skemën
            schema_path = os.path.join(SQL_DIR, "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    
                    # Sigurohu që nuk po ekzekutojmë komanda USE të forta nga file
                    prepared_sql = ""
                    for line in schema_sql.splitlines():
                        if not line.strip().upper().startswith("USE "):
                            prepared_sql += line + "\n"
                            
                    for statement in prepared_sql.split(';'):
                        if statement.strip():
                            try:
                                cursor.execute(statement)
                            except:
                                pass
                
                connection.commit()
                
                # 4. Arnim për kolonat e reja (nëse mungojnë)
                updates = [
                    "ALTER TABLE offer_items ADD COLUMN IF NOT EXISTS order_index INT DEFAULT 0",
                    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS smtp_server VARCHAR(255) DEFAULT 'smtp.gmail.com'",
                    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS smtp_port INT DEFAULT 587",
                    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS smtp_user VARCHAR(255)",
                    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS smtp_password VARCHAR(255)",
                    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
                    "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS status ENUM('draft', 'sent', 'paid') DEFAULT 'draft'",
                    "DROP INDEX IF EXISTS invoice_number ON invoices"
                ]
                
                for up_sql in updates:
                    try: cursor.execute(up_sql)
                    except: pass
                
                connection.commit()
                print(f"✓ {db_label} sinkronizuar.")

            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"⚠️ Njoftim {db_label}: {e}")

def run_setup():
    print("Duke kontrolluar databazat (Cloud & Backup Lokal)...")
    create_database(is_backup=False) # Primary
    create_database(is_backup=True)  # Backup
    print("✓ Kontrolli i databazave përfundoi.")

if __name__ == "__main__":
    run_setup()

