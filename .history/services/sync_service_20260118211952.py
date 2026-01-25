"""
Shërbimi për sinkronizimin e të dhënave (Local -> Cloud)
"""
import pymysql.cursors
from models.database import Database

class SyncService:
    @staticmethod
    def sync_local_to_cloud():
        """Sinkronizim i Mençur: Krahasohet koha e ndryshimit (updated_at)"""
        db = Database()
        if not db.connect() or not db.connection or not db.backup_connection:
            return False, "Offline"

        print("🔄 Duke nisur Smart-Sync (Më i riu fiton)...")
        
        tables = [
            'companies', 'clients', 'templates', 'settings', 
            'invoices', 'offers', 'invoice_items', 'offer_items'
        ]
        
        try:
            for table in tables:
                # 1. Merr të dhënat nga të dyja anët
                with db.connection.cursor() as cloud_cursor:
                    cloud_cursor.execute(f"SELECT * FROM {table}")
                    cloud_data = {row['id'] if 'id' in row else i: row for i, row in enumerate(cloud_cursor.fetchall())}
                
                with db.backup_connection.cursor() as local_cursor:
                    local_cursor.execute(f"SELECT * FROM {table}")
                    local_data = {row['id'] if 'id' in row else i: row for i, row in enumerate(local_cursor.fetchall())}

                # Përgatit kolonat
                if not cloud_data and not local_data: continue
                sample_row = list(cloud_data.values())[0] if cloud_data else list(local_data.values())[0]
                columns = list(sample_row.keys())
                col_names = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))

                # 2. Krahaso dhe vendos kush duhet dërguar/marrë
                to_cloud = []
                to_local = []

                # Shiko çfarë ka lokali
                for id, l_row in local_data.items():
                    if id not in cloud_data:
                        # Mungon në Cloud -> Dërgoje
                        to_cloud.append(tuple(l_row[col] for col in columns))
                    else:
                        c_row = cloud_data[id]
                        # Nëse tabela ka fushën 'updated_at', krahaso kohën
                        if 'updated_at' in l_row and l_row['updated_at'] and c_row['updated_at']:
                            if l_row['updated_at'] > c_row['updated_at']:
                                to_cloud.append(tuple(l_row[col] for col in columns))
                            elif c_row['updated_at'] > l_row['updated_at']:
                                to_local.append(tuple(c_row[col] for col in columns))
                        else:
                            # Për tabelat pa timestamp (si artikujt), përdorim dual-replace për siguri
                            to_cloud.append(tuple(l_row[col] for col in columns))

                # Shiko çfarë ka Cloud-i që lokali nuk e ka
                for id, c_row in cloud_data.items():
                    if id not in local_data:
                        to_local.append(tuple(c_row[col] for col in columns))

                # 3. Ekzekuto ndryshimet
                if to_cloud:
                    with db.connection.cursor() as cursor:
                        cursor.executemany(f"REPLACE INTO {table} ({col_names}) VALUES ({placeholders})", to_cloud)
                    db.connection.commit()
                
                if to_local:
                    with db.backup_connection.cursor() as cursor:
                        cursor.executemany(f"REPLACE INTO {table} ({col_names}) VALUES ({placeholders})", to_local)
                    db.backup_connection.commit()
            
            print("✅ Smart-Sync përfundoi me sukses.")
            return True, "Sukses"
        except Exception as e:
            print(f"❌ Gabim gjatë Smart-Sync: {e}")
            return False, str(e)


