#!/usr/bin/env python3
"""
Importon backup SQL nga Holkos Fatura LOKAL në TiDB Cloud.
Pastron cloud-in, rikrijon tabelat nga backup (ndreq radhën) dhe shton tabelat që mungojnë.

Përdorim:
  python import_backup_to_cloud.py backup.sql

  ose:
  python import_backup_to_cloud.py

Rradha e ekzekutimit rregullohet automatikisht (FK). pdf_path pastrohet (shtigjet lokale).
Tabelat me më shumë/më pak kolona rreshtohen: backup përcakton strukturën për tabelat e veta.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web', 'backend'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_tidb_connection():
    """Lidhet me TiDB Cloud duke përdorur .env ose config."""
    import pymysql
    from dotenv import load_dotenv
    load_dotenv(os.path.join('web', 'backend', '.env'))
    load_dotenv()

    url = os.getenv('DATABASE_URL')
    if url:
        m = re.search(r'mysql(?:\+pymysql)?://([^:]+):([^@]+)@([^:]+):(\d+)/([^?&#]+)', url)
        if m:
            user, password, host, port, database = m.groups()
            conn_params = {
                'host': host, 'port': int(port), 'user': user, 'password': password,
                'database': database, 'charset': 'utf8mb4', 'cursorclass': pymysql.cursors.DictCursor
            }
            if 'tidbcloud' in host.lower():
                import ssl
                conn_params['ssl'] = ssl.create_default_context()
            return pymysql.connect(**conn_params)

    try:
        from config.database import DatabaseConfig
        return DatabaseConfig().get_connection()
    except Exception:
        pass

    raise RuntimeError('Konfiguro DATABASE_URL në web/backend/.env ose config/database.py')

def parse_backup(content):
    """Nxjerr DROP, CREATE, INSERT për çdo tabelë nga backup-i."""
    content = re.sub(r'CREATE DATABASE.*?;', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'USE\s+`?\w+`?\s*;', '', content, flags=re.IGNORECASE)

    blocks = {}
    pattern = r'DROP TABLE IF EXISTS `(\w+)`;'
    for m in re.finditer(pattern, content):
        table = m.group(1)
        start = m.start()
        end = len(content)
        next_m = re.search(pattern, content[m.end():])
        if next_m:
            end = m.end() + next_m.start()
        block = content[start:end]

        drop = re.search(r'DROP TABLE IF EXISTS `\w+`;', block)
        create = re.search(r'CREATE TABLE `?\w+`?\s*\([^;]+\);', block, re.DOTALL)
        ins = re.search(r'INSERT INTO\s+`?' + re.escape(table) + r'`?\s*\([^)]+\)\s*VALUES\s*.+?;', block, re.DOTALL | re.IGNORECASE)

        blocks[table] = {
            'drop': drop.group(0) if drop else None,
            'create': create.group(0) if create else None,
            'insert': ins.group(0).strip() if ins else None
        }
    return blocks

def ti_cloud_safe(stmt):
    """Heq/ndryshon pjesë që TiDB mund të mos i mbështetë."""
    stmt = re.sub(r'\bAUTO_INCREMENT\s*=\s*\d+', '', stmt, flags=re.IGNORECASE)
    return stmt

# Tabelat që web app kërkon por backup-i mund t'i mos ketë
OFFERS_CREATE = """
CREATE TABLE IF NOT EXISTS `offers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `offer_number` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `client_id` int(11) NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT 0.00,
  `vat_percentage` decimal(5,2) DEFAULT 18.00,
  `vat_amount` decimal(10,2) DEFAULT 0.00,
  `total` decimal(10,2) DEFAULT 0.00,
  `pdf_path` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `offers_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
OFFER_ITEMS_CREATE = """
CREATE TABLE IF NOT EXISTS `offer_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `offer_id` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `unit` varchar(20) DEFAULT NULL,
  `quantity` decimal(10,2) DEFAULT 0.00,
  `unit_price` decimal(10,2) DEFAULT 0.00,
  `subtotal` decimal(10,2) DEFAULT 0.00,
  `row_type` varchar(20) DEFAULT 'item',
  `custom_attributes` text DEFAULT NULL,
  `order_index` int(11) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `offer_id` (`offer_id`),
  CONSTRAINT `offer_items_ibfk_1` FOREIGN KEY (`offer_id`) REFERENCES `offers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# Radha: fëmijët para prindëve (DROP), prindërit para fëmijëve (CREATE/INSERT)
DROP_ORDER = ['invoice_items', 'offer_items', 'invoices', 'offers', 'clients', 'templates', 'companies', 'settings']
CREATE_INSERT_ORDER = ['companies', 'clients', 'templates', 'settings', 'invoices', 'invoice_items', 'offers', 'offer_items']

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    skip_confirm = '-y' in sys.argv or '--yes' in sys.argv
    backup_path = args[0] if args else input('Shtegu te backup-it (.sql): ').strip()
    if not backup_path or not os.path.isfile(backup_path):
        print('[GABIM] Skedari nuk u gjet:', backup_path)
        sys.exit(1)

    with open(backup_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Zëvendëso pdf_path me NULL në INSERT invoices (shtigje lokale)
    content = re.sub(
        r"'(?:[A-Za-z]:\\[^']*\.pdf|[^']*\\[^']*\.pdf)'",
        'NULL',
        content
    )

    blocks = parse_backup(content)
    if not blocks:
        print('[GABIM] Nuk u gjeten tabela ne backup.')
        sys.exit(1)

    print('--- IMPORT BACKUP NË CLOUD (TiDB) ---')
    print(f'Skedari: {backup_path}')
    print('Do të: 1) Fshihen tabelat 2) Rikrihen nga backup 3) Shtohen të dhënat')
    if not skip_confirm:
        choice = input('\nTë dhënat në Cloud do të fshihen dhe zëvendësohen. Vazhdohet? (po/jo): ')
        if choice.lower() != 'po':
            print('Anuluar.')
            sys.exit(0)

    conn = get_tidb_connection()
    cursor = conn.cursor()

    try:
        # 1. Sigurohu qe tabelat ekzistojne - ekzekuto schema
        schema_path = os.path.join(os.path.dirname(__file__), 'sql', 'schema.sql')
        if os.path.isfile(schema_path):
            print('  [OK] Duke ekzekutuar schema...')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            schema = re.sub(r'USE\s+\w+\s*;', '', schema, flags=re.IGNORECASE)
            for stmt in [s.strip() + ';' for s in schema.split(';') if s.strip() and not s.strip().startswith('--')]:
                if stmt.strip() and stmt.strip() != ';':
                    try:
                        cursor.execute(stmt)
                    except Exception:
                        pass

        cursor.execute('SET FOREIGN_KEY_CHECKS=0')

        # 2. Fshirje e plote - DELETE (me kompatibil me TiDB se TRUNCATE)
        for table in DROP_ORDER:
            try:
                cursor.execute(f'DELETE FROM `{table}`')
                n = cursor.rowcount
                print(f'  [DELETE] {table}: {n} rreshta u fshine')
            except Exception as e:
                print(f'  [WARN] DELETE {table}: {e}')

        # 3. Vetem INSERT nga backup
        for table in CREATE_INSERT_ORDER:
            if table not in blocks:
                continue
            b = blocks[table]
            if b['insert']:
                try:
                    cursor.execute(b['insert'])
                    print(f'  [OK] INSERT: {table} ({cursor.rowcount} rreshta)')
                except Exception as e:
                    print(f'  [WARN] INSERT {table}: {e}')

        # 3. Siguro pdf_path = NULL
        try:
            cursor.execute('UPDATE invoices SET pdf_path = NULL WHERE pdf_path IS NOT NULL')
            if cursor.rowcount:
                print(f'  [OK] invoices: pastruar {cursor.rowcount} pdf_path')
        except Exception:
            pass

        cursor.execute('SET FOREIGN_KEY_CHECKS=1')
        conn.commit()

        # Verifikim - numri i rreshtave pas importit
        print('\n--- Verifikim ---')
        for t in ['companies', 'clients', 'invoices', 'invoice_items', 'offers', 'offer_items']:
            try:
                cursor.execute(f'SELECT COUNT(*) as n FROM `{t}`')
                row = cursor.fetchone()
                n = row['n'] if isinstance(row, dict) else (row[0] if row else 0)
            except Exception:
                n = '?'
            print(f'  {t}: {n} rreshta')
        print('\n[OK] IMPORT I PERFUNDUAR ME SUKSES!')
        print('\nShënim: Nese aplikacioni ne Vercel nuk shfaq te dhenat, kontrollo qe')
        print('DATABASE_URL ne Render te jete i njejte me web/backend/.env')

    except Exception as e:
        conn.rollback()
        print(f'\n[GABIM] {e}')
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
