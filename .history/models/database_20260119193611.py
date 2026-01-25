"""
Klasa për menaxhimin e lidhjes me databazën MySQL
"""
from config.database import DatabaseConfig
import time

class Database:
    """Klasa për operacionet me databazën (Shared Connection State)"""
    
    _cloud_conn = None
    _backup_conn = None
    _is_offline = False
    _config = DatabaseConfig()
    _last_attempt_time = 0 

    def __init__(self):
        self.config = Database._config
        self.connection = Database._cloud_conn
        self.backup_connection = Database._backup_conn
        self.is_offline = Database._is_offline
    
    def connect(self, force=False):
        """Lidhet me databazat me 'Throttling' për të parandaluar bllokimin"""
        current_time = time.time()
        
        # Mos provo lidhjen më shpesh se çdo 10 sekonda nëse të dyja kanë dështuar
        if not force and Database._cloud_conn is None and Database._backup_conn is None:
            # Përpjekja e parë (kur _last_attempt_time është 0) lejohet gjithmonë
            if Database._last_attempt_time > 0 and (current_time - Database._last_attempt_time < 10):
                return False

        Database._last_attempt_time = current_time

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
        
        # 1. Provo Cloud
        # Provo lidhjen nese e kemi, edhe nese jemi markuar si offline (mbase interneti u kthye)
        if Database._cloud_conn:
            try:
                Database._cloud_conn.ping(reconnect=True)
                Database._is_offline = False # U kthye!
                
                with Database._cloud_conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        return cursor.fetchall()
                    else:
                        Database._cloud_conn.commit()
                        last_id = cursor.lastrowid
                        
                        # DUAL WRITE
                        if Database._backup_conn:
                            try:
                                with Database._backup_conn.cursor() as b_cursor:
                                    b_cursor.execute(query, params or ())
                                    Database._backup_conn.commit()
                            except: pass
                        return last_id
            except Exception as e:
                if not Database._is_offline:
                    print(f"⚠️ Cloud e paarritshme: {e}")
                Database._is_offline = True

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
                Database._backup_conn = None # Mark as dead for this session

        return [] if is_select else None
    
    def execute_many(self, query, params_list):
        """Ekzekuton shumë query me Fallback inteligjent"""
        if Database._cloud_conn is None and Database._backup_conn is None:
            self.connect()

        # 1. Provo Cloud
        if Database._cloud_conn:
            try:
                Database._cloud_conn.ping(reconnect=True)
                Database._is_offline = False # U kthye!
                
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
                if not Database._is_offline:
                    print(f"⚠️ Cloud e paarritshme (Bulk): {e}")
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
                Database._backup_conn = None
        return False

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
            # Throttle edhe për background check nëse s'kemi fare lidhje
            current_time = time.time()
            if cls._last_attempt_time > 0 and (current_time - cls._last_attempt_time < 10):
                return False
                
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
