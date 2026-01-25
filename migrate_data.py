import pymysql
from config.database import DatabaseConfig
import sys

# 1. Konfigurimi i Databazës LOKALE (Burimi)
LOCAL_HOST = "localhost"
LOCAL_USER = "root"
LOCAL_PASS = ""
LOCAL_DB = "holkos_fatura1"
LOCAL_PORT = 3306

def get_local_connection():
    try:
        return pymysql.connect(
            host=LOCAL_HOST,
            user=LOCAL_USER,
            password=LOCAL_PASS,
            database=LOCAL_DB,
            port=LOCAL_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Gabim lidhje Lokale: {e}")
        return None

def get_remote_connection():
    # Përdorim klasën ekzistuese që tani është e konfiguruar për TiDB
    conf = DatabaseConfig()
    return conf.get_connection()

def migrate():
    print("--- FILLIMI I UDHËTIMIT TË TË DHËNAVE (MIGRIMI) ---")
    print(f"Burimi: {LOCAL_DB} @ {LOCAL_HOST}")
    
    # Lidhja lokale
    local_conn = get_local_connection()
    if not local_conn:
        print("❌ Nuk mund të lidhem me databazën lokale në XAMPP. Sigurohu që MySQL është ndezur.")
        return

    # Lidhja remote
    remote_conn = get_remote_connection()
    if not remote_conn:
        print("❌ Nuk mund të lidhem me databazën në Cloud (TiDB).")
        return

    print("✅ Lidhja me dy databazat u vendos me sukses.")

    # Lista e tabelave sipas radhës (për shkak të Foreign Keys)
    # Fshijmë fëmijët fillimisht, pastaj prindërit
    tables_order = [
        "invoice_items", "offer_items",  # Fëmijë
        "invoices", "offers",            # Prindër me FK te Clients
        "clients", "templates", "companies", "settings" # Të pavarur
    ]
    
    # Për importim, i mbushim nga prindërit te fëmijët
    import_order = [
         "companies", "clients", "templates", "settings",
         "invoices", "offers",
         "invoice_items", "offer_items"
    ]

    try:
        l_cursor = local_conn.cursor()
        r_cursor = remote_conn.cursor()

        # 1. Pastrimi i Databazës Remote (Opsionale por e rekomanduar për start të pastër)
        print("\nDuke pastruar databazën remote për të shmangur dublikatat...")
        r_cursor.execute("SET FOREIGN_KEY_CHECKS=0;") # Çaktivizo kontrollin e FK
        
        for table in tables_order:
            print(f" - Duke fshirë të dhënat e vjetra në: {table}")
            try:
                r_cursor.execute(f"TRUNCATE TABLE {table}")
            except:
                r_cursor.execute(f"DELETE FROM {table}") # Fallback nëse truncate dështon
        
        # 2. Migrimi
        print("\nDuke kopjuar të dhënat...")
        
        for table in import_order:
            # Lexo nga Lokale
            l_cursor.execute(f"SELECT * FROM {table}")
            rows = l_cursor.fetchall()
            
            if not rows:
                print(f" ⚠️ Tabela '{table}' është bosh lokalisht. Po kalohet.")
                continue
                
            print(f" 📥 Duke migruar {len(rows)} rreshta për tabelën '{table}'...")
            
            # Ndërto query-në INSERT
            # Marrim emrat e kolonave nga rreshti i parë
            columns = list(rows[0].keys())
            col_str = ", ".join(columns)
            val_placeholders = ", ".join(["%s"] * len(columns))
            
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({val_placeholders})"
            
            # Konverto dict values në list për executemany
            data_to_insert = []
            for row in rows:
                data_to_insert.append(list(row.values()))
            
            try:
                r_cursor.executemany(sql, data_to_insert)
                print(f"    ✅ Sukses: {table}")
            except Exception as e:
                print(f"    ❌ GABIM te {table}: {e}")

        r_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        remote_conn.commit()
        print("\n✅ MIGRIMI PËRFUNDOI ME SUKSES!")
        print("Të gjitha të dhënat tuaja lokale tani janë në Cloud.")

    except Exception as e:
        print(f"\n❌ Ndodhi një gabim i papritur: {e}")
        remote_conn.rollback()
    finally:
        local_conn.close()
        remote_conn.close()

if __name__ == "__main__":
    choice = input("Ky proces do të fshijë të dhënat në Cloud dhe do t'i zëvendësojë me ato Lokale.\nA jeni i sigurt? (po/jo): ")
    if choice.lower() == "po":
        migrate()
    else:
        print("Procesi u anulua.")
