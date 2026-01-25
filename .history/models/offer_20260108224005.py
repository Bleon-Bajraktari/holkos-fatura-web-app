from datetime import date
from decimal import Decimal
import mysql.connector

class Offer:
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.id = None
        self.offer_number = ""
        self.date = date.today()
        self.client_id = None
        self.description = ""
        self.subtotal = Decimal("0.00")
        self.vat_percentage = Decimal("18.00")
        self.vat_amount = Decimal("0.00")
        self.total = Decimal("0.00")
        self.pdf_path = None
        self.items = [] # List of dicts: {'description': str, 'unit': str, 'quantity': Decimal, 'unit_price': Decimal, 'subtotal': Decimal}
        self.status = 'sent' # Default for compatibility
        self.client_name = "" # Helper for display/email

    def add_item(self, description, unit, quantity, unit_price):
        """Shton një artikull në ofertë"""
        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price))
        subtotal = quantity * unit_price
        
        self.items.append({
            'description': description,
            'unit': unit,
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': subtotal
        })
        self.calculate_totals()

    def calculate_totals(self):
        """Llogarit totalet e ofertës"""
        self.subtotal = sum(item['subtotal'] for item in self.items)
        self.vat_amount = self.subtotal * (self.vat_percentage / Decimal("100.00"))
        self.total = self.subtotal + self.vat_amount

    def saved_in_db(self):
        return self.id is not None

    def save(self):
        """Ruan ofertën në database"""
        if not self.db:
            return False
            
        cursor = self.db.cursor()
        try:
            if not self.id:
                # Insert
                query = """
                    INSERT INTO offers (offer_number, date, client_id, description, subtotal, vat_percentage, vat_amount, total, pdf_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    self.offer_number, self.date, self.client_id, self.description,
                    self.subtotal, self.vat_percentage, self.vat_amount, self.total, self.pdf_path
                )
                cursor.execute(query, values)
                self.id = cursor.lastrowid
            else:
                # Update
                query = """
                    UPDATE offers 
                    SET offer_number=%s, date=%s, client_id=%s, description=%s,
                        subtotal=%s, vat_percentage=%s, vat_amount=%s, total=%s, pdf_path=%s
                    WHERE id=%s
                """
                values = (
                    self.offer_number, self.date, self.client_id, self.description,
                    self.subtotal, self.vat_percentage, self.vat_amount, self.total, self.pdf_path,
                    self.id
                )
                cursor.execute(query, values)
            
            # Save items (Delete all and re-insert for simplicity)
            if self.id:
                cursor.execute("DELETE FROM offer_items WHERE offer_id = %s", (self.id,))
                
                if self.items:
                    item_query = """
                        INSERT INTO offer_items (offer_id, description, unit, quantity, unit_price, subtotal, order_index)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    item_values = []
                    for idx, item in enumerate(self.items):
                        item_values.append((
                            self.id, item['description'], item['unit'], 
                            item['quantity'], item['unit_price'], item['subtotal'], idx
                        ))
                    cursor.executemany(item_query, item_values)

            self.db.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error saving offer: {err}")
            self.db.rollback()
            return False
        finally:
            cursor.close()

    @staticmethod
    def get_next_offer_number(db_connection):
        """Gjeneron numrin e ardhshëm të ofertës (e.g. OF-2024-001)"""
        cursor = db_connection.cursor()
        year = date.today().year
        try:
            # Merr numrin e fundit për këtë vit
            query = "SELECT offer_number FROM offers WHERE YEAR(date) = %s ORDER BY id DESC LIMIT 1"
            cursor.execute(query, (year,))
            result = cursor.fetchone()
            
            if result:
                last_number = result[0]
                # last_number format: OF-YYYY-XXX
                parts = last_number.split('-')
                if len(parts) == 3 and parts[1] == str(year):
                    try:
                        next_seq = int(parts[2]) + 1
                        return f"OF-{year}-{next_seq:03d}"
                    except ValueError:
                        pass
            
            # Default first number
            return f"OF-{year}-001"
            
        except Exception as e:
            print(f"Error getting next offer number: {e}")
            return f"OF-{year}-001"
        finally:
            cursor.close()

    @staticmethod
    def get_by_id(offer_id, db_connection):
        """Merr një ofertë nga ID"""
        cursor = db_connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM offers WHERE id = %s", (offer_id,))
            offer_data = cursor.fetchone()
            
            if not offer_data:
                return None
                
            offer = Offer(db_connection)
            offer.id = offer_data['id']
            offer.offer_number = offer_data['offer_number']
            offer.date = offer_data['date']
            offer.client_id = offer_data['client_id']
            offer.description = offer_data['description']
            offer.subtotal = offer_data['subtotal']
            offer.vat_percentage = offer_data['vat_percentage']
            offer.vat_amount = offer_data['vat_amount']
            offer.total = offer_data['total']
            offer.pdf_path = offer_data['pdf_path']
            
            # Get items
            cursor.execute("SELECT * FROM offer_items WHERE offer_id = %s ORDER BY order_index", (offer_id,))
            items_data = cursor.fetchall()
            
            for item in items_data:
                offer.items.append({
                    'description': item['description'],
                    'unit': item['unit'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'subtotal': item['subtotal']
                })
            
            return offer
            
        except Exception as e:
            print(f"Error getting offer: {e}")
            return None
        finally:
            cursor.close()
