"""
Shërbimi për sinkronizimin e të dhënave (Local -> Cloud)
"""
import pymysql.cursors
from models.database import Database

class SyncService:
    @staticmethod
    def sync_local_to_cloud():
        """Smart-Sync: Sinkronizim i sigurt sekuencial (Më i riu fiton + Mbrojtje Artikujsh)"""
        db = Database()
        if not db.connect() or not db.connection or not db.backup_connection:
            return False, "Offline"

        print("🔄 Duke nisur sinkronizimin mbrojtës (Invoices -> Items)...")
        
        try:
            # NJIHSIMI: Funksion për sinkronizim të sigurt të fushave standarde
            def sync_table_standard(table_name):
                with db.connection.cursor() as c_cur:
                    c_cur.execute(f"SELECT * FROM {table_name}")
                    cloud_rows = c_cur.fetchall()
                with db.backup_connection.cursor() as l_cur:
                    l_cur.execute(f"SELECT * FROM {table_name}")
                    local_rows = l_cur.fetchall()
                
                all_raw = cloud_rows + local_rows
                if not all_raw: return
                
                # Merre një shembull për kolonat
                columns = list(all_raw[0].keys())
                placeholders = ", ".join(["%s"] * len(columns))
                update_stmt = ", ".join([f"{c}=VALUES({c})" for c in columns if c != 'id'])
                sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_stmt}"
                
                # Dërgo të dhënat në të dyja anët
                data = [tuple(r[c] for c in columns) for r in all_raw]
                with db.connection.cursor() as c_cur: c_cur.executemany(sql, data)
                with db.backup_connection.cursor() as l_cur: l_cur.executemany(sql, data)
                db.connection.commit()
                db.backup_connection.commit()

            # 1. SINKRONIZO TABELAT THEMELORE
            for t in ['companies', 'clients', 'templates', 'settings']:
                sync_table_standard(t)

            # 2. SINKRONIZO FATURAT DHE OFERTAT (ME DEDUPLIKIM DHE RINUMËRIM)
            for t in ['invoices', 'offers']:
                with db.connection.cursor() as c_cur:
                    c_cur.execute(f"SELECT * FROM {t}")
                    cloud_list = c_cur.fetchall()
                with db.backup_connection.cursor() as l_cur:
                    l_cur.execute(f"SELECT * FROM {t}")
                    local_list = l_cur.fetchall()
                
                # Bashko duke identifikuar duplikate mbrenda se njejtes pajisje ose ID
                # Ne kete rast, ID eshte me e rendesishmja
                all_raw = cloud_list + local_list
                merged_docs = {}
                for d in all_raw:
                    # Nese kemi ID te njejte, me i riu fiton
                    doc_id = d['id']
                    if doc_id not in merged_docs:
                        merged_docs[doc_id] = d
                    else:
                        if d['updated_at'] > merged_docs[doc_id]['updated_at']:
                            merged_docs[doc_id] = d
                
                if not merged_docs: continue

                # Rendit sipas kohes
                sorted_docs = sorted(merged_docs.values(), key=lambda x: x['created_at'])
                by_year = {}
                for d in sorted_docs:
                    yr = d['date'].year if hasattr(d['date'], 'year') else d['created_at'].year
                    if yr not in by_year: by_year[yr] = []
                    by_year[yr].append(d)
                
                for yr in sorted(by_year.keys()):
                    count = 1
                    for doc in sorted(by_year[yr], key=lambda x: x['created_at']):
                        num_col = 'invoice_number' if t == 'invoices' else 'offer_number'
                        doc[num_col] = f"{'FATURA' if t == 'invoices' else 'OFERTA'} NR.{count}"
                        count += 1
                        
                        cols = list(doc.keys())
                        update_sql = ", ".join([f"{c}=VALUES({c})" for c in cols if c != 'id'])
                        sql = f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))}) ON DUPLICATE KEY UPDATE {update_sql}"
                        val = tuple(doc[c] for c in cols)
                        
                        with db.connection.cursor() as c_cur: c_cur.execute(sql, val)
                        with db.backup_connection.cursor() as l_cur: l_cur.execute(sql, val)
                db.connection.commit()
                db.backup_connection.commit()

            # 3. SINKRONIZO ARTIKUJT (VETËM PASI KANË PËRFUNDUAR FATURAT)
            for t in ['invoice_items', 'offer_items']:
                sync_table_standard(t)

            print("✅ Sinkronizimi i sigurt (Invoices -> Items) përfundoi.")
            return True, "Sukses"
        except Exception as e:
            print(f"❌ Gabim gjatë sinkronizimit: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
