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
            # Konfigurimi bazë
            conn_params = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'database': self.database,
                'charset': 'utf8mb4',
                'cursorclass': pymysql.cursors.DictCursor,
                'connect_timeout': 2,
                'autocommit': True
            }
            
            # Nëse jemi duke u lidhur me TiDB Cloud (port 4000), aktivizo SSL
            if self.port == 4000:
                conn_params['ssl'] = {'ssl': {}} # Default SSL context
            
            return pymysql.connect(**conn_params)
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

    def get_backup_connection(self):
        """Kthen lidhjen lokale për backup"""
        try:
            return pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="",
                database="holkos_fatura1",
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=1,
                autocommit=True
            )
        except:
            return None
