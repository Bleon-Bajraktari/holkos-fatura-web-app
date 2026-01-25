import pymysql

class DatabaseConfig:
    """Klasa për konfigurimin e databazës"""
    
    def __init__(self):
        self.host = "sql112.infinityfree.com"
        self.port = 3306
        self.database = "if0_40934720_holkos"
        self.user = "if0_40934720"
        self.password = "OxdBMSINTJ"  # Ndrysho nëse ke password për MySQL
        
    def get_connection(self):
        """Krijon dhe kthen një lidhje me databazën duke përdorur PyMySQL"""
        try:
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                autocommit=True  # Për të siguruar që ruajtja bëhet menjëherë
            )
        except Exception as e:
            print(f"Gabim në lidhjen me databazën: {e}")
            return None

    def test_connection(self):
        """Teston lidhjen me databazën"""
        connection = self.get_connection()
        if connection:
            connection.close()
            return True
        return False
