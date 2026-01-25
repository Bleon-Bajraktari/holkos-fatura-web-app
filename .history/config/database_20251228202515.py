"""
Konfigurimi i lidhjes me databazën MySQL
"""
import mysql.connector
from mysql.connector import Error

class DatabaseConfig:
    """Klasa për konfigurimin e databazës"""
    
    def __init__(self):
        self.host = "localhost"
        self.port = 3306
        self.database = "holkos_fatura"
        self.user = "root"
        self.password = ""  # Ndrysho nëse ke password për MySQL
        
    def get_connection(self):
        """Krijon dhe kthen një lidhje me databazën - optimizuar"""
        try:
            # Provo të përdorësh pool nëse ekziston
            try:
                return mysql.connector.connect(
                    pool_name="holkos_pool",
                    pool_reset_session=True
                )
            except:
                # Krijo lidhje të re me optimizime
                connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    connect_timeout=10,
                    buffered=True,
                    use_pure=True  # E rëndësishme për paketim në .exe
                )
                if connection.is_connected():
                    return connection
        except Error as e:
            print(f"Gabim në lidhjen me databazën: {e}")
            return None
    
    def test_connection(self):
        """Teston lidhjen me databazën"""
        connection = self.get_connection()
        if connection:
            connection.close()
            return True
        return False

