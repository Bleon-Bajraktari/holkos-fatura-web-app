from config.database import DatabaseConfig
import mysql.connector

def add_pdf_column():
    config = DatabaseConfig()
    try:
        conn = mysql.connector.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database
        )
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE invoices ADD COLUMN pdf_path VARCHAR(500) AFTER status")
            conn.commit()
            print("Added pdf_path column.")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("Column pdf_path already exists.")
            else:
                print(f"Error adding column: {e}")
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    add_pdf_column()
