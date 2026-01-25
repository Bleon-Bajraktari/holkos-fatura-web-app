"""
Klasa për menaxhimin e lidhjes me databazën MySQL
"""
from config.database import DatabaseConfig

class Database:
    """Klasa për operacionet me databazën"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.connection = None
    
    def connect(self):
        """Lidhet me databazën"""
        try:
            self.connection = self.config.get_connection()
            return self.connection is not None
        except Exception as e:
            print(f"Gabim në lidhjen me databazën: {e}")
            return False
    
    def disconnect(self):
        """Mbyll lidhjen me databazën"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None):
        """Ekzekuton një query dhe kthen rezultatet"""
        try:
            if self.connection:
                try:
                    self.connection.ping(reconnect=True)
                except:
                    self.connect()
            else:
                self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                # Nëse është SELECT, kthen rezultatet
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return result
                else:
                    # PyMySQL me autocommit=True nuk ka nevojë për commit manual
                    # por po e lëmë për siguri nëse autocommit nuk është aktiv
                    self.connection.commit()
                    return cursor.lastrowid
        except Exception as e:
            print(f"Gabim në ekzekutimin e query: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def execute_many(self, query, params_list):
        """Ekzekuton një query me shumë parametra"""
        try:
            if self.connection:
                try:
                    self.connection.ping(reconnect=True)
                except:
                    self.connect()
            else:
                self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.executemany(query, params_list)
                self.connection.commit()
            return True
        except Exception as e:
            print(f"Gabim në ekzekutimin e query: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
