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
            else:
                self.is_offline = True
                self.connection = None
        except:
            self.is_offline = True
            self.connection = None

        # 2. Provo lidhjen Lokale (Backup)
        try:
            self.backup_connection = self.config.get_backup_connection()
        except:
            self.backup_connection = None

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
        # Sigurohu qe jemi lidhur nese thirrja vjen nga nje instance e re
        if self.connection is None and self.backup_connection is None:
            self.connect()

        is_select = query.strip().upper().startswith('SELECT')
        
        # 1. Provo Cloud (vetëm nese nuk kemi dështuar më parë në këtë sesion)
        if self.connection and not self.is_offline:
            try:
                # Ping i shpejtë për të parë nëse jemi ende online
                try: self.connection.ping(reconnect=True)
                except: raise Exception("Lost connection")

                with self.connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        result = cursor.fetchall()
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
                import tkinter.messagebox as msgbox
                if not self.is_offline:
                    print(f"⚠️ Cloud e paarritshme: {e}")
                    # Shfaq njoftim vetëm herën e parë që dështon
                    try:
                        msgbox.showwarning("Lidhja e humbur", "Nuk u arrit lidhja me Cloud. Programi do të vazhdojë në Offline Mode (Lokal).")
                    except: pass
                
                self.is_offline = True
                self.connection = None # Ndalo tentativat në Cloud për këtë sesion

        # 2. Provo Backup (Local)
        if self.backup_connection:
            try:
                with self.backup_connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        return cursor.fetchall()
                    else:
                        self.backup_connection.commit()
                        return cursor.lastrowid
            except Exception as e:
                print(f"❌ Gabim në Backup: {e}")

        return [] if is_select else None
    
    def execute_many(self, query, params_list):
        """Ekzekuton shumë query me Fallback inteligjent"""
        # 1. Provo Cloud
        if self.connection and not self.is_offline:
            try:
                with self.connection.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    self.connection.commit()
                
                # Sinkronizo me Backup
                if self.backup_connection:
                    try:
                        with self.backup_connection.cursor() as cursor:
                            cursor.executemany(query, params_list)
                            self.backup_connection.commit()
                    except: pass
                return True
            except:
                self.is_offline = True
                self.connection = None

        # 2. Provo Backup
        if self.backup_connection:
            try:
                with self.backup_connection.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    self.backup_connection.commit()
                return True
            except:
                return False

        return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
