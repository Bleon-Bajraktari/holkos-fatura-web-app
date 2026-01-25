
import pymysql

def count_clients(db_name):
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM clients")
            result = cursor.fetchone()
            print(f"Databaza '{db_name}' ka {result['count']} kliente.")
        conn.close()
    except Exception as e:
        print(f"Gabim te '{db_name}': {e}")

if __name__ == "__main__":
    count_clients("holkos_fatura")
    count_clients("holkos_fatura1")
