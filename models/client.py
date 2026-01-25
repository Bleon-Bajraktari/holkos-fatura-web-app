"""
Modeli për klientët
"""
from models.database import Database
from datetime import datetime

class Client:
    """Klasa për menaxhimin e klientëve"""
    
    def __init__(self, db=None):
        self.db = db or Database()
        self.id = None
        self.name = ""
        self.address = ""
        self.unique_number = ""
        self.phone = ""
        self.email = ""
        self.created_at = None
        self.updated_at = None
    
    @staticmethod
    def get_all(db=None):
        """Merr të gjithë klientët"""
        database = db or Database()
        query = "SELECT * FROM clients ORDER BY name"
        result = database.execute_query(query)
        return result or []
    
    @staticmethod
    def get_by_id(client_id, db=None):
        """Merr një klient sipas ID"""
        database = db or Database()
        query = "SELECT * FROM clients WHERE id = %s"
        result = database.execute_query(query, (client_id,))
        
        if result and len(result) > 0:
            client = Client(db)
            data = result[0]
            client.id = data['id']
            client.name = data['name'] or ""
            client.address = data['address'] or ""
            client.unique_number = data['unique_number'] or ""
            client.phone = data['phone'] or ""
            client.email = data['email'] or ""
            client.created_at = data['created_at']
            client.updated_at = data['updated_at']
            return client
        return None
    
    @staticmethod
    def search(search_term, db=None):
        """Kërkon klientë"""
        database = db or Database()
        query = """SELECT * FROM clients 
                   WHERE name LIKE %s OR unique_number LIKE %s OR address LIKE %s
                   ORDER BY name"""
        search_pattern = f"%{search_term}%"
        result = database.execute_query(query, (search_pattern, search_pattern, search_pattern))
        return result or []
    
    def save(self):
        """Ruaj klientin"""
        if self.id:
            # Update
            query = """UPDATE clients SET 
                name = %s, address = %s, unique_number = %s, 
                phone = %s, email = %s
                WHERE id = %s"""
            params = (self.name, self.address, self.unique_number,
                     self.phone, self.email, self.id)
        else:
            # Insert
            query = """INSERT INTO clients 
                (name, address, unique_number, phone, email)
                VALUES (%s, %s, %s, %s, %s)"""
            params = (self.name, self.address, self.unique_number,
                     self.phone, self.email)
        
        result = self.db.execute_query(query, params)
        if result and not self.id:
            self.id = result
        return result is not None
    
    def delete(self):
        """Fshi klientin"""
        if not self.id:
            return False
        
        query = "DELETE FROM clients WHERE id = %s"
        result = self.db.execute_query(query, (self.id,))
        return result is not None
    
    def to_dict(self):
        """Kthen të dhënat si dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'unique_number': self.unique_number,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

