from config.database import DatabaseConfig
import pymysql

def fix_db():
    print("Duke rregulluar strukturën e tabelës në Cloud...")
    conf = DatabaseConfig()
    try:
        conn = conf.get_connection()
        if not conn:
            print("Nuk mund të lidhem me Cloud DB.")
            return

        cursor = conn.cursor()
        
        # 1. Shto kolonën 'order_index' në offer_items nëse mungon
        try:
            cursor.execute("ALTER TABLE offer_items ADD COLUMN order_index INT DEFAULT 0")
            print("✅ Kolona 'order_index' u shtua me sukses në offer_items.")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("ℹ️ Kolona 'order_index' ekziston tashmë.")
            else:
                print(f"⚠️ Paralajmërim: {e}")

        conn.commit()
        conn.close()
        print("\nRregullimi përfundoi. Tani provoni sërish migrimin.")

    except Exception as e:
        print(f"Gabim: {e}")

if __name__ == "__main__":
    fix_db()
