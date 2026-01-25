import time
import threading
from config.database import DatabaseConfig
import pymysql

class Database:
    """Klasa hibride për operacionet me databazën (Cloud & Local Backup)"""
    
    _cloud_conn = None
    _backup_conn = None
    _is_offline = False
    _is_connecting = False
    _config = DatabaseConfig()
    _last_attempt_time = 0

    def __init__(self):
        self.config = Database._config
    
    def connect(self, force=False):
        """Përpiqet të lidhet pa bllokuar shumë Main Thread."""
        if Database._is_connecting:
            return False
            
        current_time = time.time()
        # Throttling
        if not force and (current_time - Database._last_attempt_time < 15):
            return (Database._cloud_conn is not None or Database._backup_conn is not None)

        Database._last_attempt_time = current_time
        Database._is_connecting = True
        
        try:
            # 1. Provo Cloud
            if not Database._cloud_conn:
                Database._cloud_conn = self.config.get_connection() # 2s timeout
            
            # 2. Provo Backup vetem nese Cloud deshtoi ose jemi ne force
            if not Database._backup_conn:
                # Perdorim nje timeout shume te ulet per localhost
                try:
                    Database._backup_conn = pymysql.connect(
                        host="localhost", port=3306, user="root", password="",
                        database="holkos_fatura1", charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor,
                        connect_timeout=1, autocommit=True
                    )
                except:
                    Database._backup_conn = None
                
            Database._is_offline = (Database._cloud_conn is None)
        finally:
            Database._is_connecting = False
            
        return (Database._cloud_conn is not None or Database._backup_conn is not None)

    def execute_query(self, query, params=None):
        """Ekzekuton query. Nëse skemi lidhje, fillon një në background."""
        is_select = query.strip().upper().startswith('SELECT')
        
        # 1. Kontrolli i lidhjes
        if not Database._cloud_conn and not Database._backup_conn:
            if not Database._is_connecting:
                # Provo lidhjen shpejt ne background nese eshte hera e pare
                threading.Thread(target=self.connect, kwargs={'force': True}, daemon=True).start()
            return [] if is_select else None

        # 2. Provo Cloud (Prioritet)
        if Database._cloud_conn:
            try:
                Database._cloud_conn.ping(reconnect=True)
                Database._is_offline = False
                with Database._cloud_conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        return cursor.fetchall()
                    Database._cloud_conn.commit()
                    last_id = cursor.lastrowid
                    
                    # DUAL WRITE (Silent)
                    if Database._backup_conn:
                        try:
                            with Database._backup_conn.cursor() as b_cursor:
                                b_cursor.execute(query, params or ())
                                Database._backup_conn.commit()
                        except: pass
                    return last_id
            except:
                Database._is_offline = True
                # Bejme fallback te Backup nese ka

        # 3. Provo Backup (Local)
        if Database._backup_conn:
            try:
                with Database._backup_conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if is_select:
                        return cursor.fetchall()
                    Database._backup_conn.commit()
                    return cursor.lastrowid
            except:
                Database._backup_conn = None # Mark as dead
                
        return [] if is_select else None

    def execute_many(self, query, params_list):
        """Ekzekuton shumë query me Fallback"""
        if not Database._cloud_conn and not Database._backup_conn:
            return False

        if Database._cloud_conn:
            try:
                Database._cloud_conn.ping(reconnect=True)
                with Database._cloud_conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    Database._cloud_conn.commit()
                    if Database._backup_conn:
                        try:
                            with Database._backup_conn.cursor() as b_cursor:
                                b_cursor.executemany(query, params_list)
                                Database._backup_conn.commit()
                        except: pass
                return True
            except:
                Database._is_offline = True

        if Database._backup_conn:
            try:
                with Database._backup_conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    Database._backup_conn.commit()
                return True
            except:
                Database._backup_conn = None
        return False

    @classmethod
    def check_connection_status(cls):
        """Status check që përdoret nga UI thread"""
        if cls._is_connecting: return False
        
        if cls._cloud_conn:
            try:
                cls._cloud_conn.ping(reconnect=True)
                cls._is_offline = False
                return True
            except:
                cls._is_offline = True
                return False
        else:
            current_time = time.time()
            if current_time - cls._last_attempt_time < 15:
                return False
            
            # Shmang bllokimin e UI
            threading.Thread(target=cls._bg_connect, daemon=True).start()
            return False

    @classmethod
    def _bg_connect(cls):
        if cls._is_connecting: return
        cls._is_connecting = True
        try:
            cls._cloud_conn = cls._config.get_connection()
            cls._backup_conn = cls._config.get_backup_connection()
            cls._is_offline = (cls._cloud_conn is None)
        except: pass
        finally:
            cls._is_connecting = False
            cls._last_attempt_time = time.time()
            
    def disconnect(self):
        if Database._cloud_conn:
            try: Database._cloud_conn.close()
            except: pass
        if Database._backup_conn:
            try: Database._backup_conn.close()
            except: pass
        Database._cloud_conn = None
        Database._backup_conn = None

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
