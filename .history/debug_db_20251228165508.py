import mysql.connector
from config.database import DatabaseConfig

def inspect_db():
    config = DatabaseConfig()
    try:
        conn = mysql.connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database
        )
        cursor = conn.cursor()
        
        print(f"Connected to database: {config.database}")
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables found:", [t[0] for t in tables])
        
        # Describe invoices
        print("\nDesc invoices:")
        try:
            cursor.execute("DESCRIBE invoices")
            for col in cursor.fetchall():
                print(col)
        except Exception as e:
            print(f"Error describing invoices: {e}")

        # Describe clients
        print("\nDesc clients:")
        try:
            cursor.execute("DESCRIBE clients")
            for col in cursor.fetchall():
                print(col)
        except Exception as e:
            print(f"Error describing clients: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    inspect_db()
