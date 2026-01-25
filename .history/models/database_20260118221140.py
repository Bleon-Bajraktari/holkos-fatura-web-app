"""
Klasa për menaxhimin e lidhjes me databazën MySQL
"""
from config.database import DatabaseConfig

class Database:
    """Klasa për operacionet me databazën (Shared Connection State)"""
    
    _cloud_conn = None
    _backup_conn = None
    _is_offline = False
    _config = DatabaseConfig()

    def __init__(self):
        # Referencat lokalisht por që përdorin gjendjen e përbashkët
        self.config = Database._config
        self.connection = Database._cloud_conn
        self.backup_connection = Database._backup_conn
        self.is_offline = Database._is_offline
    
    def connect(self):
        """Lidhet me databazat. Kthen True nëse të paktën njëra funksionon."""
        # 1. Provo lidhjen Cloud (Primary)
        try:
            Database._cloud_conn = self.config.get_connection()
            if Database._cloud_conn:
                Database._is_offline = False
            else:
                Database._is_offline = True
                Database._cloud_conn = None
        except:
            Database._is_offline = True
            Database._cloud_conn = None

        # 2. Provo lidhjen Lokale (Backup)
        try:
            Database._backup_conn = self.config.get_backup_connection()
        except:
            Database._backup_conn = None

        # Përditëso instancën aktuale
        self.connection = Database._cloud_conn
        self.backup_connection = Database._backup_conn
        self.is_offline = Database._is_offline

        return (self.connection is not None or self.backup_connection is not None)
    
    def disconnect(self):
        """Mbyll lidhjet"""
        if Database._cloud_conn:
            try: Database._cloud_conn.close()
            except: pass
            Database._cloud_conn = None
        if Database._backup_conn:
            try: Database._backup_conn.close()
            except: pass
            Database._backup_conn = None
        self.connection = None
        self.backup_connection = None
    
    def execute_query(self, query, params=None):
        """Ekzekuton query me Fallback inteligjent"""
        # Sigurohu qe jemi lidhur nese thirrja vjen nga nje instance e re
        if Database._cloud_conn is None and Database._backup_conn is None:
            self.connect()

        is_select = query.strip().upper().startswith('SELECT')
        
        # 1. Provo Cloud (vetëm nese nuk kemi dështuar më parë në këtë sesion)
        if Database._cloud_conn and not Database._is_offline:
            try:
                # Ping i shpejtë për të parë nëse jemi ende online
                try: Database._cloud_conn.ping(reconnect=True)
                except: raise Exception("Lost connection")

                with Database._cloud_conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        result = cursor.fetchall()
                        return result
                    else:
                        Database._cloud_conn.commit()
                        last_id = cursor.lastrowid
                        
                        # DUAL WRITE: Ruaj edhe në Backup nese jemi online
                        if Database._backup_conn:
                            try:
                                with Database._backup_conn.cursor() as b_cursor:
                                    b_cursor.execute(query, params or ())
                                    Database._backup_conn.commit()
                            except: pass
                        return last_id
            except Exception as e:
                if not Database._is_offline:
                    print(f"⚠️ Cloud e paarritshme (Silent): {e}")
                
                Database._is_offline = True
                # Nuk mbyllim connection qe te mos provojme ping cdo sekonde ne kete instance,
                # por e markojme si offline globalisht.

        # 2. Provo Backup (Local)
        if Database._backup_conn:
            try:
                with Database._backup_conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        return cursor.fetchall()
                    else:
                        Database._backup_conn.commit()
                        return cursor.lastrowid
            except Exception as e:
                print(f"❌ Gabim në Backup: {e}")

        return [] if is_select else None
    
    def execute_many(self, query, params_list):
        """Ekzekuton shumë query me Fallback inteligjent"""
        if Database._cloud_conn is None and Database._backup_conn is None:
            self.connect()

        # 1. Provo Cloud
        if Database._cloud_conn and not Database._is_offline:
            try:
                Database._cloud_conn.ping(reconnect=True)
                with Database._cloud_conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    Database._cloud_conn.commit()
                    
                    # DUAL WRITE
                    if Database._backup_conn:
                        try:
                            with Database._backup_conn.cursor() as b_cursor:
                                b_cursor.executemany(query, params_list)
                                Database._backup_conn.commit()
                        except: pass
                return True
            except Exception as e:
                print(f"⚠️ Cloud e paarritshme (Silent-Bulk): {e}")
                Database._is_offline = True

        # 2. Provo Backup (Local)
        if Database._backup_conn:
            try:
                with Database._backup_conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    Database._backup_conn.commit()
                return True
            except Exception as e:
                print(f"❌ Gabim bulk në Backup: {e}")

        return False

    @classmethod
    def check_connection_status(cls):
        """Probon lidhjen Cloud në background për të përditësuar statusin"""
        if cls._cloud_conn:
            try:
                cls._cloud_conn.ping(reconnect=True)
                cls._is_offline = False
                return True
            except:
                cls._is_offline = True
                return False
        else:
            # Provo ri-lidhjen
            try:
                cls._cloud_conn = cls._config.get_connection()
                if cls._cloud_conn:
                    cls._is_offline = False
                    return True
            except:
                pass
            cls._is_offline = True
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
