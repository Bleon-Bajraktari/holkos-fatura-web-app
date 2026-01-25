"""
Shërbimi për sinkronizimin e të dhënave (Local -> Cloud)
"""
import pymysql.cursors
from models.database import Database

class SyncService:
    @staticmethod
    def sync_local_to_cloud():
        """Sinkronizim i Plotë dhe i Sigurt (Cloud <-> Local)"""
        db = Database()
        if not db.connect() or not db.connection or not db.backup_connection:
            return False, "Offline: Sinkronizimi do të kryhet kur të keni internet."

        print("🔄 Duke nisur sinkronizimin inteligjent...")
        
        tables = [
            'companies', 'clients', 'templates', 'settings', 
            'invoices', 'offers', 'invoice_items', 'offer_items'
        ]
        
        try:
            for table in tables:
                # PASSI 1: MERR NGA CLOUD -> LOKAL (Përditëso backup-in lokal)
                with db.connection.cursor() as cloud_cursor:
                    cloud_cursor.execute(f"SELECT * FROM {table}")
                    cloud_rows = cloud_cursor.fetchall()
                
                if cloud_rows:
                    columns = list(cloud_rows[0].keys())
                    placeholders = ", ".join(["%s"] * len(columns))
                    col_names = ", ".join(columns)
                    
                    # REPLACE INTO në lokal (Cloud fiton mbi Lokalin për faturat ekzistuese)
                    query_local = f"REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
                    with db.backup_connection.cursor() as local_cursor:
                        data_to_local = [tuple(row[col] for col in columns) for row in cloud_rows]
                        local_cursor.executemany(query_local, data_to_local)
                    db.backup_connection.commit()

                # PASSI 2: DËRGO NGA LOKALI -> CLOUD (Vetëm ato që mungojnë - Punë Offline)
                with db.backup_connection.cursor() as local_cursor:
                    local_cursor.execute(f"SELECT * FROM {table}")
                    local_rows = local_cursor.fetchall()
                
                if local_rows:
                    columns = list(local_rows[0].keys())
                    placeholders = ", ".join(["%s"] * len(columns))
                    col_names = ", ".join(columns)
                    
                    # INSERT IGNORE në Cloud (Nuk i prek faturat që janë tashmë në Cloud, shton vetëm të rejat)
                    query_cloud = f"INSERT IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"
                    with db.connection.cursor() as cloud_cursor:
                        data_to_cloud = [tuple(row[col] for col in columns) for row in local_rows]
                        cloud_cursor.executemany(query_cloud, data_to_cloud)
                    db.connection.commit()
            
            print("✅ Sinkronizimi përfundoi: Pajisja juaj është në njëjtën gjendje me Cloud.")
            return True, "Sinkronizimi u krye."
        except Exception as e:
            print(f"❌ Gabim gjatë sinkronizimit: {e}")
            return False, str(e)

