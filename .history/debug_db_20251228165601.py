import mysql.connector
from config.database import DatabaseConfig
import sys

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
            
            # Show tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            f.write(f"Tables found: {[t[0] for t in tables]}\n")
            
            # Describe invoices
            f.write("\nDesc invoices:\n")
            try:
                cursor.execute("DESCRIBE invoices")
                for col in cursor.fetchall():
                    f.write(f"{col}\n")
            except Exception as e:
                f.write(f"Error describing invoices: {e}\n")

            # Describe clients
            f.write("\nDesc clients:\n")
            try:
                cursor.execute("DESCRIBE clients")
                for col in cursor.fetchall():
                    f.write(f"{col}\n")
            except Exception as e:
                f.write(f"Error describing clients: {e}\n")
                
            conn.close()
        except Exception as e:
            f.write(f"Connection error: {e}\n")

if __name__ == "__main__":
    inspect_db()
