"""
Klasa për menaxhimin e lidhjes me databazën MySQL
"""
from config.database import DatabaseConfig
from mysql.connector import Error, pooling
import mysql.connector

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
    
    def execute_query(self, query, params=None):
        """Ekzekuton një query dhe kthen rezultatet"""
        try:
            if not self.connection:
                self.connect()
            
            # PyMySQL kthen dictionary automatikisht nese eshte konfiguruar ne connect
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                # Nëse është SELECT, kthen rezultatet
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return result
                else:
                    # Për INSERT, UPDATE, DELETE
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
            if not self.connection:
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

