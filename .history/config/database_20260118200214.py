import pymysql

class DatabaseConfig:
    """Klasa për konfigurimin e databazës"""
    
    def __init__(self):
        # 1. KONFIGURIMI TiDB CLOUD (Online)
        # Bëni Copy-Paste këtu të dhënat nga butoni 'Connect' në TiDB Cloud
        self.host = "gateway01.eu-central-1.prod.aws.tidbcloud.com"       # p.sh. gateway01.eu-central-1.prod.aws.tidbcloud.com
        self.port = 4000
        self.database = "test"  # Ose emri i databazës suaj
        self.user = "23pY2336LXLw5MR.root"       # Emri i gjatë (p.sh. 2N1kS....root)
        self.password = "oFv0JzSZ1dk8olqt"   # Passwordi juaj
        
        # 2. KONFIGURIMI LOKAL (XAMPP - Opsional)
        # self.host = "localhost"
        # self.port = 3306
        # self.database = "holkos_fatura1"
        # self.user = "root"
        # self.password = ""
        
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
