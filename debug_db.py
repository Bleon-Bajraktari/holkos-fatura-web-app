import mysql.connector
from config.database import DatabaseConfig

def inspect_db():
    with open('debug_output.log', 'w', encoding='utf-8') as f:
        config = DatabaseConfig()
        try:
            conn = mysql.connector.connect(
                host=config.host,
                user=config.user,
                password=config.password,
                database=config.database
            )
            cursor = conn.cursor()
            
            f.write(f"Connected to database: {config.database}\n")
            
            # Check counts
            cursor.execute("SELECT COUNT(*) FROM invoices")
            count_inv = cursor.fetchone()[0]
            f.write(f"Invoices count: {count_inv}\n")
            
            cursor.execute("SELECT COUNT(*) FROM clients")
            count_clients = cursor.fetchone()[0]
            f.write(f"Clients count: {count_clients}\n")
                
            conn.close()
        except Exception as e:
            f.write(f"Connection error: {e}\n")

if __name__ == "__main__":
    inspect_db()
