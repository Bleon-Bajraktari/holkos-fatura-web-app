"""
Klasa për menaxhimin e lidhjes me databazën MySQL
"""
from config.database import DatabaseConfig

class Database:
    """Klasa për operacionet me databazën"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.connection = None
        self.backup_connection = None
        self.is_offline = False
    
    def connect(self):
        """Lidhet me databazat. Kthen True nëse të paktën njëra funksionon."""
        # 1. Provo lidhjen Cloud (Primary)
        try:
            self.connection = self.config.get_connection()
            if self.connection:
                self.is_offline = False
                # print("✅ Cloud Database Connected.")
            else:
                self.is_offline = True
        except:
            self.is_offline = True
            self.connection = None

        # 2. Provo lidhjen Lokale (Backup)
        try:
            self.backup_connection = self.config.get_backup_connection()
            # if self.backup_connection:
            #     print("✅ Local Backup Database Connected.")
        except:
            self.backup_connection = None

        # Programi mund të nisë nëse të paktën njëra lidhje është aktive
        return (self.connection is not None) or (self.backup_connection is not None)
    
    def disconnect(self):
        """Mbyll lidhjet"""
        if self.connection:
            try: self.connection.close()
            except: pass
            self.connection = None
        if self.backup_connection:
            try: self.backup_connection.close()
            except: pass
            self.backup_connection = None
    
    def execute_query(self, query, params=None):
        """Ekzekuton query me Fallback inteligjent"""
        # Tentativa e parë: Cloud
        if self.connection:
            try:
                # Kontrollo nese lidhja eshte ende e gjalle
                try: self.connection.ping(reconnect=True)
                except: pass
                
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith('SELECT'):
                        result = cursor.fetchall()
                        # Sinkronizo Backup në Background (vetëm për shkrime, por SELECT kthehet këtu)
                        return result
                    else:
                        self.connection.commit()
                        last_id = cursor.lastrowid
                        
                        # DUAL WRITE: Ruaj edhe në Backup nese jemi online
                        if self.backup_connection:
                            try:
                                with self.backup_connection.cursor() as b_cursor:
                                    b_cursor.execute(query, params or ())
                                    self.backup_connection.commit()
                            except: pass
                        return last_id
            except Exception as e:
                print(f"⚠️ Cloud Query Failed, switching to Offline Mode: {e}")
                self.is_offline = True
                # Mos u kthe (return), kalo te logjika e Backup-it poshtë

        # Tentativa e dytë: Backup (Local)
        if self.backup_connection:
            try:
                try: self.backup_connection.ping(reconnect=True)
                except: pass
                
                with self.backup_connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        self.backup_connection.commit()
                        return cursor.lastrowid
            except Exception as e:
                print(f"❌ Backup Query Failed: {e}")
                return None
        
        return None
    
    def execute_many(self, query, params_list):
        """Ekzekuton shumë query me Fallback inteligjent"""
        success = False
        
        # 1. Provo Cloud
        if self.connection:
            try:
                with self.connection.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    self.connection.commit()
                    success = True
                    # print("✓ Dual Write (Primary) OK")
            except:
                self.is_offline = True

        # 2. Provo ose Sinkronizo me Backup
        if self.backup_connection:
            try:
                with self.backup_connection.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    self.backup_connection.commit()
                    # print("✓ Dual Write (Backup) OK")
                    if not self.connection: # Nëse jemi offline, suksesi varet nga ky
                        success = True
            except:
                pass

        return success
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
