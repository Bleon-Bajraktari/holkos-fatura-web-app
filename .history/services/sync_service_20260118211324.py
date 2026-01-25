"""
Shërbimi për sinkronizimin e të dhënave (Local -> Cloud)
"""
import pymysql.cursors
from models.database import Database

class SyncService:
    @staticmethod
    def sync_local_to_cloud():
        """Merr të gjitha të dhënat lokale dhe i dërgon në Cloud (UPSERT)"""
        db = Database()
        if not db.connect():
            return False, "S'ka lidhje me asnjë databazë."
        
        # Nëse nuk kemi lidhje Cloud, s'kemi ku t'i sinkronizojmë
        if not db.connection:
            return False, "Offline: Sinkronizimi do të kryhet kur të keni internet."

        print("🔄 Duke nisur sinkronizimin Local -> Cloud...")
        
        tables = [
            'companies', 'clients', 'templates', 'settings', 
            'invoices', 'offers', 'invoice_items', 'offer_items'
        ]
        
        try:
            for table in tables:
                # 1. Merr të dhënat nga LOKALI
                with db.backup_connection.cursor() as local_cursor:
                    local_cursor.execute(f"SELECT * FROM {table}")
                    rows = local_cursor.fetchall()
                
                if not rows:
                    continue

                # 2. Dërgoi në CLOUD (UPSERT logjika)
                # Përdorim 'REPLACE INTO' ose 'INSERT ... ON DUPLICATE KEY UPDATE'
                # REPLACE INTO është më i thjeshtë për të gjitha fushat
                
                columns = list(rows[0].keys())
                placeholders = ", ".join(["%s"] * len(columns))
                col_names = ", ".join(columns)
                
                query = f"REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
                
                with db.connection.cursor() as cloud_cursor:
                    data_to_sync = [tuple(row[col] for col in columns) for row in rows]
                    cloud_cursor.executemany(query, data_to_sync)
                
                db.connection.commit()
                # print(f"✅ Sinkronizuar tabela: {table} ({len(rows)} rreshta)")
            
            print("✅ Sinkronizimi Local -> Cloud përfundoi me sukses.")
            return True, "Sinkronizimi u krye."
        except Exception as e:
            print(f"❌ Gabim gjatë sinkronizimit: {e}")
            return False, str(e)
