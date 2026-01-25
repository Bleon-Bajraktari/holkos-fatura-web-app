from datetime import date
from decimal import Decimal
import mysql.connector
from models.database import Database

class Offer:
    def __init__(self, db_connection=None):
        self.db = db_connection or Database()
        self.id = None
        self.offer_number = ""
        self.date = date.today()
        self.client_id = None
        self.subject = "" # Titulli i ofertës (e.g. Montim Xhami)
        self.description = ""
        self.subtotal = Decimal("0.00")
        self.vat_percentage = Decimal("18.00")
        self.vat_amount = Decimal("0.00")
        self.total = Decimal("0.00")
        self.pdf_path = None
        self.items = [] # List of dicts
        self.status = 'sent' # Default for compatibility
        self.client_name = "" 

    def add_item(self, description, unit, quantity, unit_price, custom_attributes=None, row_type='item'):
        """Shton një artikull në ofertë"""
        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price))
        subtotal = quantity * unit_price
        
        self.items.append({
            'description': description,
            'unit': unit,
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': subtotal,
            'row_type': row_type,
            'custom_attributes': custom_attributes # JSON string or list/dict
        })
        self.calculate_totals()

    def calculate_totals(self):
        """Llogarit totalet e ofertës"""
        # Only sum items of type 'item'
        self.subtotal = sum(item['subtotal'] for item in self.items if item.get('row_type', 'item') == 'item')
        self.vat_amount = self.subtotal * (self.vat_percentage / Decimal("100.00"))
        self.total = self.subtotal + self.vat_amount

    def saved_in_db(self):
        return self.id is not None

    def save(self):
        """Ruan ofertën në database"""
        if not self.db:
            return False
            
        try:
            if not self.id:
                # Insert
                query = """
                    INSERT INTO offers (offer_number, date, client_id, subject, description, subtotal, vat_percentage, vat_amount, total, pdf_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    self.offer_number, self.date, self.client_id, self.subject, self.description,
                    float(self.subtotal), float(self.vat_percentage), float(self.vat_amount), float(self.total), self.pdf_path
                )
                result = self.db.execute_query(query, values)
                if result:
                    self.id = result
            else:
                # Update
                query = """
                    UPDATE offers 
                    SET offer_number=%s, date=%s, client_id=%s, subject=%s, description=%s,
                        subtotal=%s, vat_percentage=%s, vat_amount=%s, total=%s, pdf_path=%s
                    WHERE id=%s
                """
                values = (
                    self.offer_number, self.date, self.client_id, self.subject, self.description,
                    float(self.subtotal), float(self.vat_percentage), float(self.vat_amount), float(self.total), self.pdf_path,
                    self.id
                )
                self.db.execute_query(query, values)
            
            # Save items
            if self.id:
                self.db.execute_query("DELETE FROM offer_items WHERE offer_id = %s", (self.id,))
                
                if self.items:
                    item_query = """
                        INSERT INTO offer_items (offer_id, description, unit, quantity, unit_price, subtotal, row_type, custom_attributes, order_index)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    item_values = []
                    for idx, item in enumerate(self.items):
                        import json
                        custom_attr_json = json.dumps(item['custom_attributes']) if item.get('custom_attributes') else None
                        item_values.append((
                            self.id, item['description'], item['unit'], 
                            float(item['quantity']), float(item['unit_price']), float(item['subtotal']),
                            item.get('row_type', 'item'),
                            custom_attr_json, idx
                        ))
                    self.db.execute_many(item_query, item_values)
            
            return True
        except Exception as err:
            print(f"Error saving offer: {err}")
            return False

    @staticmethod
    def get_next_offer_number(db_connection=None):
        """Gjeneron numrin e ardhshëm të ofertës"""
        db = db_connection or Database()
        year = date.today().year
        try:
            query = "SELECT offer_number FROM offers WHERE YEAR(date) = %s ORDER BY id DESC LIMIT 1"
            result = db.execute_query(query, (year,))
            
            if result and len(result) > 0:
                last_number = result[0]['offer_number']
                parts = last_number.split('-')
                if len(parts) == 3 and parts[1] == str(year):
                    try:
                        next_seq = int(parts[2]) + 1
                        return f"OF-{year}-{next_seq:03d}"
                    except ValueError:
                        pass
            
            return f"OF-{year}-001"
            
        except Exception as e:
            print(f"Error getting next offer number: {e}")
            return f"OF-{year}-001"

    @staticmethod
    def get_by_id(offer_id, db_connection=None):
        """Merr një ofertë nga ID"""
        db = db_connection or Database()
        try:
            result = db.execute_query("SELECT * FROM offers WHERE id = %s", (offer_id,))
            
            if not result:
                return None
                
            offer_data = result[0]
            offer = Offer(db)
            offer.id = offer_data['id']
            offer.offer_number = offer_data['offer_number']
            offer.date = offer_data['date']
            offer.client_id = offer_data['client_id']
            offer.subject = offer_data.get('subject', '')
            offer.description = offer_data['description']
            offer.subtotal = Decimal(str(offer_data['subtotal']))
            offer.vat_percentage = Decimal(str(offer_data['vat_percentage']))
            offer.vat_amount = Decimal(str(offer_data['vat_amount']))
            offer.total = Decimal(str(offer_data['total']))
            offer.pdf_path = offer_data['pdf_path']
            
            # Get items
            items_result = db.execute_query("SELECT * FROM offer_items WHERE offer_id = %s ORDER BY id ASC", (offer_id,))
            
            if items_result:
                import json
                for item in items_result:
                    custom_attr = None
                    if item.get('custom_attributes'):
                        try:
                            custom_attr = json.loads(item['custom_attributes'])
                        except:
                            custom_attr = None
                            
                    offer.items.append({
                        'description': item['description'],
                        'unit': item['unit'],
                        'quantity': Decimal(str(item['quantity'])),
                        'unit_price': Decimal(str(item['unit_price'])),
                        'subtotal': Decimal(str(item['subtotal'])),
                        'row_type': item.get('row_type', 'item'),
                        'custom_attributes': custom_attr
                    })
            
            return offer
            
        except Exception as e:
            print(f"Error getting offer: {e}")
            return None
