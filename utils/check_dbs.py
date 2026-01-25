
import pymysql

def check_dbs():
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            dbs = cursor.fetchall()
            print("Databazat ne MySQL:")
            for db in dbs:
                print(f"- {db['Database']}")
        conn.close()
    except Exception as e:
        print(f"Gabim: {e}")

if __name__ == "__main__":
    check_dbs()
