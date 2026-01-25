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
    
    def connect(self):
        """Lidhet me databazën dhe backup-in"""
        try:
            self.connection = self.config.get_connection()
            # Provo të lidhesh edhe me backup (Local)
            self.backup_connection = self.config.get_backup_connection()
            return self.connection is not None
        except Exception as e:
            print(f"Gabim në lidhjen me databazën: {e}")
            return False
    
    def disconnect(self):
        """Mbyll lidhjen me databazën"""
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.backup_connection:
            try: self.backup_connection.close()
            except: pass
            self.backup_connection = None
    
    def execute_query(self, query, params=None):
        """Ekzekuton një query dhe kthen rezultatet (Dual Write)"""
        try:
            # 1. Sigurohu që Primary është lidhur
            if self.connection:
                try:
                    self.connection.ping(reconnect=True)
                except:
                    self.connect()
            else:
                self.connect()
            
            # 2. Ekzekuto në Primary (Cloud)
            result = None
            last_id = None
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                # Nëse është SELECT, kthen rezultatet
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    last_id = cursor.lastrowid
            
            # 3. BACKUP: Nëse ishte shkrim (jo SELECT), provo në Local
            # Vetëm nëse Primary pati sukses
            if self.backup_connection and not query.strip().upper().startswith('SELECT'):
                try:
                    self.backup_connection.ping(reconnect=True)
                    with self.backup_connection.cursor() as b_cursor:
                        b_cursor.execute(query, params or ())
                        self.backup_connection.commit()
                except Exception as e:
                    # Injoro gabimet e backup-it (nuk duam të bllokojmë programin)
                    # print(f"Backup failed: {e}") 
                    pass

            return last_id

        except Exception as e:
            print(f"Gabim në ekzekutimin e query: {e}")
            if self.connection:
                try: self.connection.rollback()
                except: pass
            return None
    
    def execute_many(self, query, params_list):
        """Ekzekuton një query me shumë parametra (Dual Write)"""
        try:
            if self.connection:
                try:
                    self.connection.ping(reconnect=True)
                except:
                    self.connect()
            else:
                self.connect()
            
            # 1. Primary
            with self.connection.cursor() as cursor:
                cursor.executemany(query, params_list)
                self.connection.commit()
            
            # 2. Backup
            if self.backup_connection:
                try:
                    self.backup_connection.ping(reconnect=True)
                    with self.backup_connection.cursor() as b_cursor:
                        b_cursor.executemany(query, params_list)
                        self.backup_connection.commit()
                except:
                    pass

            return True
        except Exception as e:
            print(f"Gabim në ekzekutimin e query: {e}")
            if self.connection:
                try: self.connection.rollback()
                except: pass
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
