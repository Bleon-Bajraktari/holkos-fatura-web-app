#!/usr/bin/env python3
"""
Krijon tabelat në TiDB Cloud duke ekzekutuar sql/schema.sql.
Ekzekutoje këtë nëse tabelat nuk ekzistojnë (gabim: Table 'test.companies' doesn't exist).

Përdorim:
  python setup_cloud_db.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web', 'backend'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_conn():
    import pymysql
    from dotenv import load_dotenv
    load_dotenv(os.path.join('web', 'backend', '.env'))
    load_dotenv()

    url = os.getenv('DATABASE_URL')
    if url:
        m = re.search(r'mysql(?:\+pymysql)?://([^:]+):([^@]+)@([^:]+):(\d+)/([^?&#]+)', url)
        if m:
            user, password, host, port, database = m.groups()
            params = {
                'host': host, 'port': int(port), 'user': user, 'password': password,
                'database': database, 'charset': 'utf8mb4'
            }
            if 'tidbcloud' in host.lower():
                import ssl
                params['ssl'] = ssl.create_default_context()
            return pymysql.connect(**params)

    try:
        from config.database import DatabaseConfig
        return DatabaseConfig().get_connection()
    except Exception:
        pass
    raise RuntimeError('Konfiguro DATABASE_URL në web/backend/.env')

def main():
    schema_path = os.path.join(os.path.dirname(__file__), 'sql', 'schema.sql')
    if not os.path.isfile(schema_path):
        print('[GABIM] sql/schema.sql nuk u gjet.')
        sys.exit(1)

    with open(schema_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Heq USE dhe ndaj në deklarata
    content = re.sub(r'USE\s+\w+\s*;', '', content, flags=re.IGNORECASE)
    raw = [s.strip() for s in content.split(';') if s.strip() and not s.strip().startswith('--')]
    stmts = [s + ';' for s in raw]

    print('--- SETUP SCHEMA NË CLOUD (TiDB) ---')
    conn = get_conn()
    cursor = conn.cursor()

    try:
        for stmt in stmts:
            if not stmt.strip() or stmt.strip() == ';':
                continue
            try:
                cursor.execute(stmt)
                first_line = stmt.split('\n')[0][:70]
                print(f'  [OK] {first_line}...' if len(stmt) > 80 else f'  [OK] {first_line}')
            except Exception as e:
                print(f'  [WARN] {e}')
        conn.commit()
        print('\n[OK] SCHEMA U KRIJUA ME SUKSES!')
    except Exception as e:
        conn.rollback()
        print(f'\n[GABIM] {e}')
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
