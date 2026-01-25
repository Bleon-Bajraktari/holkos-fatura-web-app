"""
Skript për setup të databazës
Ekzekuto këtë skript për të krijuar databazën dhe tabelat
"""
import mysql.connector
from mysql.connector import Error
import os

def create_database():
    """Krijon databazën dhe tabelat"""
    try:
        # Lidhu me MySQL (pa databazë specifike)
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password=""  # Ndrysho nëse ke password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Krijo databazën
            cursor.execute("CREATE DATABASE IF NOT EXISTS holkos_fatura")
            print("✓ Databaza 'holkos_fatura' u krijua ose ekzistonte tashmë")
            
            # Përdor databazën
            cursor.execute("USE holkos_fatura")
            
            # Lexo dhe ekzekuto skemën
            schema_path = os.path.join(os.path.dirname(__file__), "sql", "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    # Ekzekuto çdo komandë veç e veç
                    for statement in schema_sql.split(';'):
                        if statement.strip():
                            try:
                                cursor.execute(statement)
                            except Error as e:
                                if "already exists" not in str(e).lower():
                                    print(f"Vërejtje: {e}")
                
                connection.commit()
                print("✓ Tabelat u krijuan me sukses")
            else:
                print(f"✗ Skema nuk u gjet në: {schema_path}")
            
            cursor.close()
            connection.close()
            print("\n✓ Setup i databazës u përfundua me sukses!")
            print("Tani mund të ekzekutosh aplikacionin me: python main.py")
            
    except Error as e:
        print(f"✗ Gabim: {e}")
        print("\nJu lutem sigurohuni që:")
        print("1. MySQL është i startuar në xampp")
        print("2. Credentials në config/database.py janë të sakta")
        print("3. MySQL user ka të drejta për të krijuar databaza")

if __name__ == "__main__":
    print("Setup i databazës për Holkos Fatura")
    print("=" * 40)
    create_database()

