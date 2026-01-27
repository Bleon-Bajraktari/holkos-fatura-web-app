import sqlite3
import json
import os
from datetime import datetime
from decimal import Decimal

# Absolute path for the local backup database
BACKUP_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_backup.sqlite")

class LocalBackupService:
    def __init__(self):
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(BACKUP_DB_PATH)

    def _init_db(self):
        """Initializes the local SQLite database schema for backup"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # We store everything in simple JSON buckets per table for maximum flexibility
        # or we mirror the schema. Mirroring is safer for data loss.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_store (
                table_name TEXT,
                record_id INTEGER,
                data TEXT,
                updated_at DATETIME,
                PRIMARY KEY (table_name, record_id)
            )
        ''')
        conn.commit()
        conn.close()

    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, Decimal)):
            return str(obj)
        raise TypeError (f"Type {type(obj)} not serializable")

    def save_record(self, table_name, record_id, record_dict):
        """Saves or updates a record in the local backup"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Convert record to JSON
            json_data = json.dumps(record_dict, default=self._json_serial)
            
            cursor.execute('''
                INSERT OR REPLACE INTO backup_store (table_name, record_id, data, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (table_name, record_id, json_data, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving to local backup: {e}")
            return False

    def get_all(self, table_name):
        """Retrieves all records for a table from backup"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM backup_store WHERE table_name = ?', (table_name,))
            rows = cursor.fetchall()
            conn.close()
            return [json.loads(row[0]) for row in rows]
        except:
            return []

backup_service = LocalBackupService()
