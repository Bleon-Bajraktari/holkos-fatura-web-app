"""
Modeli për faturave
"""
from models.database import Database
from datetime import datetime, date
from decimal import Decimal

class Invoice:
    """Klasa për menaxhimin e faturave"""
    
    def __init__(self, db=None):
        self.db = db or Database()
        self.id = None
        self.invoice_number = ""
        self.date = date.today()
        self.payment_due_date = None
        self.client_id = None
        self.template_id = None
        self.subtotal = Decimal('0.00')
        self.vat_percentage = Decimal('18.00')
        self.vat_amount = Decimal('0.00')
        self.total = Decimal('0.00')
        self.status = 'draft'
        self.pdf_path = None
        self.created_at = None
        self.updated_at = None
        self.items = []  # Lista e artikujve
    
    @staticmethod
    def get_all(db=None, filters=None, limit=None):
        """Merr të gjitha faturaet - optimizuar me LIMIT"""
        database = db or Database()
        query = """SELECT i.*, c.name as client_name 
                   FROM invoices i
                   LEFT JOIN clients c ON i.client_id = c.id
                   WHERE 1=1"""
        params = []
        
        if filters:
            if filters.get('client_id'):
                query += " AND i.client_id = %s"
                params.append(filters['client_id'])
            if filters.get('status'):
                query += " AND i.status = %s"
                params.append(filters['status'])
            if filters.get('date_from'):
                query += " AND i.date >= %s"
                params.append(filters['date_from'])
            if filters.get('date_to'):
                query += " AND i.date <= %s"
                params.append(filters['date_to'])
            if filters.get('search'):
                query += " AND (i.invoice_number LIKE %s OR c.name LIKE %s)"
                search_pattern = f"%{filters['search']}%"
                params.extend([search_pattern, search_pattern])
        
        query += " ORDER BY i.date DESC, i.id DESC"
        
        # LIMIT vetëm nëse specifikohet eksplicitisht
        if limit and limit > 0:
            query += f" LIMIT {limit}"
        
        result = database.execute_query(query, tuple(params) if params else None)
        return result or []
    
    @staticmethod
    def get_by_id(invoice_id, db=None):
        """Merr një fatura sipas ID"""
        database = db or Database()
        query = "SELECT * FROM invoices WHERE id = %s"
        result = database.execute_query(query, (invoice_id,))
        
        if result and len(result) > 0:
            invoice = Invoice(db)
            data = result[0]
            invoice.id = data['id']
            invoice.invoice_number = data['invoice_number'] or ""
            invoice.date = data['date']
            invoice.payment_due_date = data['payment_due_date']
            invoice.client_id = data['client_id']
            invoice.template_id = data['template_id']
            invoice.subtotal = Decimal(str(data['subtotal']))
            invoice.vat_percentage = Decimal(str(data['vat_percentage']))
            invoice.vat_amount = Decimal(str(data['vat_amount']))
            invoice.total = Decimal(str(data['total']))
            invoice.status = data['status']
            invoice.pdf_path = data.get('pdf_path')
            invoice.created_at = data['created_at']
            invoice.updated_at = data['updated_at']
            
            # Ngarko artikujt
            invoice.load_items()
            return invoice
        return None
    
    @staticmethod
    def get_next_invoice_number(db=None):
        """Gjeneron numrin e ardhshëm të faturave, duke rinisur çdo vit"""
        database = db or Database()
        current_year = date.today().year
        
        # Merr faturën e fundit të këtij viti
        query = "SELECT invoice_number FROM invoices WHERE YEAR(date) = %s ORDER BY id DESC LIMIT 1"
        result = database.execute_query(query, (current_year,))
        
        if result and len(result) > 0:
            last_number = result[0]['invoice_number']
            # Format: 'FATURA NR.24'
            try:
                if "NR." in last_number.upper():
                    # Merr pjesën numerike pas 'NR.'
                    num_part = last_number.upper().split("NR.")[-1].strip()
                    # Pastro nëse ka karaktere të tjera (p.sh. /2025)
                    num_clean = "".join([c for c in num_part if c.isdigit()])
                    if num_clean:
                        return f"FATURA NR.{int(num_clean) + 1}"
            except:
                pass
        
        # Nëse ska fatura këtë vit ose dështon, fillo me 1
        return "FATURA NR.1"
    
    def load_items(self):
        """Ngarkon artikujt e faturave"""
        if not self.id:
            return
        
        query = "SELECT * FROM invoice_items WHERE invoice_id = %s ORDER BY order_index, id"
        result = self.db.execute_query(query, (self.id,))
        
        self.items = []
        if result:
            for item in result:
                self.items.append({
                    'id': item['id'],
                    'description': item['description'],
                    'quantity': Decimal(str(item['quantity'])),
                    'unit_price': Decimal(str(item['unit_price'])),
                    'subtotal': Decimal(str(item['subtotal'])),
                    'order_index': item['order_index']
                })
    
    def calculate_totals(self):
        """Llogarit totalet bazuar në artikujt"""
        self.subtotal = sum(item['subtotal'] for item in self.items)
        self.vat_amount = self.subtotal * (self.vat_percentage / Decimal('100'))
        self.total = self.subtotal + self.vat_amount
    
    def add_item(self, description, quantity, unit_price):
        """Shton një artikull"""
        subtotal = Decimal(str(quantity)) * Decimal(str(unit_price))
        self.items.append({
            'id': None,
            'description': description,
            'quantity': Decimal(str(quantity)),
            'unit_price': Decimal(str(unit_price)),
            'subtotal': subtotal,
            'order_index': len(self.items)
        })
        self.calculate_totals()
    
    def remove_item(self, index):
        """Heq një artikull"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            # Rishiko indekset
            for i, item in enumerate(self.items):
                item['order_index'] = i
            self.calculate_totals()
    
    def save(self):
        """Ruaj faturave dhe artikujt e saj"""
        # Llogarit totalet para se të ruhet
        self.calculate_totals()
        
        if self.id:
            # Update
            query = """UPDATE invoices SET 
                invoice_number = %s, date = %s, payment_due_date = %s,
                client_id = %s, template_id = %s, subtotal = %s,
                vat_percentage = %s, vat_amount = %s, total = %s, status = %s,
                pdf_path = %s
                WHERE id = %s"""
            params = (self.invoice_number, self.date, self.payment_due_date,
                     self.client_id, self.template_id, float(self.subtotal),
                     float(self.vat_percentage), float(self.vat_amount),
                     float(self.total), self.status, self.pdf_path, self.id)
        else:
            # Insert
            query = """INSERT INTO invoices 
                (invoice_number, date, payment_due_date, client_id, template_id,
                 subtotal, vat_percentage, vat_amount, total, status, pdf_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            params = (self.invoice_number, self.date, self.payment_due_date,
                     self.client_id, self.template_id, float(self.subtotal),
                     float(self.vat_percentage), float(self.vat_amount),
                     float(self.total), self.status, self.pdf_path)
        
        result = self.db.execute_query(query, params)
        if result:
            if not self.id:
                self.id = result
            
            # Ruaj artikujt
            # Fshi artikujt e vjetër
            delete_query = "DELETE FROM invoice_items WHERE invoice_id = %s"
            self.db.execute_query(delete_query, (self.id,))
            
            # Shto artikujt e rinj
            if self.items:
                insert_query = """INSERT INTO invoice_items 
                    (invoice_id, description, quantity, unit_price, subtotal, order_index)
                    VALUES (%s, %s, %s, %s, %s, %s)"""
                items_params = [
                    (self.id, item['description'], float(item['quantity']),
                     float(item['unit_price']), float(item['subtotal']),
                     item['order_index'])
                    for item in self.items
                ]
                self.db.execute_many(insert_query, items_params)
            
            return True
        return False
    
    def delete(self):
        """Fshi faturave (artikujt fshihen automatikisht për shkak të CASCADE)"""
        if not self.id:
            return False
        
        query = "DELETE FROM invoices WHERE id = %s"
        result = self.db.execute_query(query, (self.id,))
        return result is not None
    
    @staticmethod
    def get_stats(db=None):
        """Merr statistikat e përgjithshme përmes SQL për performance"""
        database = db or Database()
        
        # Total dhe Revenue
        query = """
            SELECT 
                COUNT(*) as total_count,
                SUM(total) as total_revenue,
                SUM(vat_amount) as total_vat
            FROM invoices
        """
        res = database.execute_query(query)
        stats = res[0] if res else {'total_count': 0, 'total_revenue': 0, 'total_vat': 0}
        
        # Month stats
        first_day = date.today().replace(day=1)
        query_month = "SELECT COUNT(*) as month_count FROM invoices WHERE date >= %s"
        res_month = database.execute_query(query_month, (first_day,))
        stats['month_count'] = res_month[0]['month_count'] if res_month else 0
        
        return stats

    @staticmethod
    def get_available_years(db=None):
        """Kthen listën e viteve që kanë fatura"""
        database = db or Database()
        query = "SELECT DISTINCT YEAR(date) as year FROM invoices ORDER BY year DESC"
        result = database.execute_query(query)
        years = [str(r['year']) for r in result] if result else []
        current_year = str(date.today().year)
        if current_year not in years:
            years.insert(0, current_year)
        return years

    def to_dict(self):
        """Kthen të dhënat si dictionary"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'date': self.date,
            'payment_due_date': self.payment_due_date,
            'client_id': self.client_id,
            'template_id': self.template_id,
            'subtotal': float(self.subtotal),
            'vat_percentage': float(self.vat_percentage),
            'vat_amount': float(self.vat_amount),
            'total': float(self.total),
            'status': self.status,
            'items': [item.copy() for item in self.items],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

