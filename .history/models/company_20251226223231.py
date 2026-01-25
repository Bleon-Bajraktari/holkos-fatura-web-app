"""
Modeli për kompaninë
"""
from models.database import Database

class Company:
    """Klasa për menaxhimin e informacioneve të kompanisë"""
    
    def __init__(self, db=None):
        self.db = db or Database()
        self.id = None
        self.name = ""
        self.address = ""
        self.phone = ""
        self.email = ""
        self.unique_number = ""
        self.fiscal_number = ""
        self.account_nib = ""
        self.logo_path = ""
    
    def load(self):
        """Ngarkon informacionet e kompanisë nga databaza - me caching"""
        from utils.cache import Cache
        
        # Provo të marrësh nga cache
        cached = Cache.get("company_data")
        if cached:
            data = cached
        else:
            query = "SELECT * FROM companies LIMIT 1"
            result = self.db.execute_query(query)
            
            if result and len(result) > 0:
                data = result[0]
                # Ruaj në cache për 10 minuta
                Cache.set("company_data", data, ttl=600)
            else:
                return False
        
        self.id = data['id']
        self.name = data['name'] or ""
        self.address = data['address'] or ""
        self.phone = data['phone'] or ""
        self.email = data['email'] or ""
        self.unique_number = data['unique_number'] or ""
        self.fiscal_number = data['fiscal_number'] or ""
        self.account_nib = data['account_nib'] or ""
        self.logo_path = data['logo_path'] or ""
        return True
    
    def save(self):
        """Ruaj informacionet e kompanisë"""
        if self.id:
            # Update
            query = """UPDATE companies SET 
                name = %s, address = %s, phone = %s, email = %s,
                unique_number = %s, fiscal_number = %s, account_nib = %s,
                logo_path = %s
                WHERE id = %s"""
            params = (self.name, self.address, self.phone, self.email,
                     self.unique_number, self.fiscal_number, self.account_nib,
                     self.logo_path, self.id)
        else:
            # Insert
            query = """INSERT INTO companies 
                (name, address, phone, email, unique_number, fiscal_number, account_nib, logo_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            params = (self.name, self.address, self.phone, self.email,
                     self.unique_number, self.fiscal_number, self.account_nib,
                     self.logo_path)
        
        result = self.db.execute_query(query, params)
        if result and not self.id:
            self.id = result
        
        # Fshi cache pas ruajtjes
        from utils.cache import Cache
        Cache.clear("company_data")
        
        return result is not None
    
    def to_dict(self):
        """Kthen të dhënat si dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'unique_number': self.unique_number,
            'fiscal_number': self.fiscal_number,
            'account_nib': self.account_nib,
            'logo_path': self.logo_path
        }

