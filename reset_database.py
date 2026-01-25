import mysql.connector
from mysql.connector import Error
import os

def reset_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password=""
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("Dropping database 'holkos_fatura'...")
            cursor.execute("DROP DATABASE IF EXISTS holkos_fatura")
            
            print("Creating database 'holkos_fatura'...")
            cursor.execute("CREATE DATABASE holkos_fatura")
            cursor.execute("USE holkos_fatura")
            
            # Read schema
            schema_path = os.path.join(os.path.dirname(__file__), "sql", "schema.sql")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                for statement in schema_sql.split(';'):
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except Error as e:
                            print(f"Warning: {e}")
            
            connection.commit()
            print("Database reset successfully!")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_database()
