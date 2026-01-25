"""
Shërbimi për sinkronizimin e të dhënave (Local -> Cloud)
"""
import pymysql.cursors
from models.database import Database

class SyncService:
    @staticmethod
    def sync_local_to_cloud():
        """Smart-Sync: Lidh pajisjet dhe zgjidh konfliktet e numrave sipas kohës"""
        db = Database()
        if not db.connect() or not db.connection or not db.backup_connection:
            return False, "Offline"

        print("🔄 Duke nisur sinkronizimin me zgjidhje konfliktesh sekuenciale...")
        
        tables = [
            'companies', 'clients', 'templates', 'settings', 
            'invoices', 'offers', 'invoice_items', 'offer_items'
        ]
        
        try:
            for table in tables:
                # 1. Për të gjitha tabelat përveç faturave, përdorim logjikën e timestamp
                if table not in ['invoices', 'offers']:
                    with db.connection.cursor() as cloud_cursor:
                        cloud_cursor.execute(f"SELECT * FROM {table}")
                        cloud_data = {row['id'] if 'id' in row else i: row for i, row in enumerate(cloud_cursor.fetchall())}
                    
                    with db.backup_connection.cursor() as local_cursor:
                        local_cursor.execute(f"SELECT * FROM {table}")
                        local_data = {row['id'] if 'id' in row else i: row for i, row in enumerate(local_cursor.fetchall())}

                    if not cloud_data and not local_data: continue
                    sample = list(cloud_data.values())[0] if cloud_data else list(local_data.values())[0]
                    columns = list(sample.keys())
                    sql = f"REPLACE INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s']*len(columns))})"

                    to_cloud, to_local = [], []
                    for id, l_row in local_data.items():
                        if id not in cloud_data: to_cloud.append(tuple(l_row[c] for c in columns))
                        else:
                            c_row = cloud_data[id]
                            if 'updated_at' in l_row and l_row['updated_at'] and c_row['updated_at']:
                                if l_row['updated_at'] > c_row['updated_at']: to_cloud.append(tuple(l_row[c] for c in columns))
                                elif c_row['updated_at'] > l_row['updated_at']: to_local.append(tuple(c_row[c] for c in columns))
                            else: to_cloud.append(tuple(l_row[c] for c in columns))
                    
                    for id, c_row in cloud_data.items():
                        if id not in local_data: to_local.append(tuple(c_row[c] for c in columns))

                    if to_cloud:
                        with db.connection.cursor() as cursor: cursor.executemany(sql, to_cloud)
                        db.connection.commit()
                    if to_local:
                        with db.backup_connection.cursor() as cursor: cursor.executemany(sql, to_local)
                        db.backup_connection.commit()
                    continue

                # 2. LOGJIKA SPECIALE PËR FATURAT (Renditja dhe Rinumërimi me Reset vjetor)
                with db.connection.cursor() as cloud_cursor:
                    cloud_cursor.execute(f"SELECT * FROM {table}")
                    cloud_rows = {row['id']: row for row in cloud_cursor.fetchall()}
                
                with db.backup_connection.cursor() as local_cursor:
                    local_cursor.execute(f"SELECT * FROM {table}")
                    local_rows = {row['id']: row for row in local_cursor.fetchall()}

                all_data = {**cloud_rows, **local_rows}
                if not all_data: continue

                # PASSI 1: Grupo të dhënat sipas vitit
                by_year = {}
                for item in all_data.values():
                    year = item['date'].year if hasattr(item['date'], 'year') else item['created_at'].year
                    if year not in by_year: by_year[year] = []
                    by_year[year].append(item)

                # PASSI 2: Rinumëro çdo vit në mënyrë të pavarur
                for year in sorted(by_year.keys()):
                    year_items = sorted(by_year[year], key=lambda x: x['created_at'])
                    count = 1
                    for item in year_items:
                        num_col = 'invoice_number' if table == 'invoices' else 'offer_number'
                        item[num_col] = f"{'FATURA' if table == 'invoices' else 'OFERTA'} NR.{count}"
                        count += 1
                        
                        columns = list(item.keys())
                        placeholders = ", ".join(["%s"] * len(columns))
                        # Konstrukto UPDATE pjesën për ON DUPLICATE KEY
                        update_parts = [f"{col}=VALUES({col})" for col in columns if col != 'id']
                        update_stmt = ", ".join(update_parts)
                        
                        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_stmt}"
                        
                        val_tuple = tuple(item[c] for c in columns)
                        with db.connection.cursor() as cc: cc.execute(sql, val_tuple)
                        with db.backup_connection.cursor() as lc: lc.execute(sql, val_tuple)
                
                db.connection.commit()
                db.backup_connection.commit()

            print("✅ Sinkronizimi sekuencial u krye me sukses.")
            return True, "Sukses"
        except Exception as e:
            print(f"❌ Gabim gjatë Smart-Sync: {e}")
            return False, str(e)


