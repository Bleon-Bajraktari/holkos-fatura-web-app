"""
Modeli për kompaninë - v1.2.0 (Shtuar SMTP)
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
        # SMTP Settings
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_user = ""
        self.smtp_password = ""
    
    def load(self):
        """Ngarkon informacionet e kompanisë nga databaza - me caching"""
        from utils.cache import Cache
        
        cached = Cache.get("company_data")
        if cached:
            data = cached
        else:
            query = "SELECT * FROM companies LIMIT 1"
            result = self.db.execute_query(query)
            
            if result and len(result) > 0:
                data = result[0]
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
        # SMTP
        self.smtp_server = data.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = data.get('smtp_port', 587)
        self.smtp_user = data.get('smtp_user', '')
        self.smtp_password = data.get('smtp_password', '')
        return True
    
    def save(self):
        """Ruaj informacionet e kompanisë"""
        if self.id:
            query = """UPDATE companies SET 
                name = %s, address = %s, phone = %s, email = %s,
                unique_number = %s, fiscal_number = %s, account_nib = %s,
                logo_path = %s, smtp_server = %s, smtp_port = %s,
                smtp_user = %s, smtp_password = %s
                WHERE id = %s"""
            params = (self.name, self.address, self.phone, self.email,
                     self.unique_number, self.fiscal_number, self.account_nib,
                     self.logo_path, self.smtp_server, self.smtp_port,
                     self.smtp_user, self.smtp_password, self.id)
        else:
            query = """INSERT INTO companies 
                (name, address, phone, email, unique_number, fiscal_number, 
                 account_nib, logo_path, smtp_server, smtp_port, smtp_user, smtp_password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            params = (self.name, self.address, self.phone, self.email,
                     self.unique_number, self.fiscal_number, self.account_nib,
                     self.logo_path, self.smtp_server, self.smtp_port, 
                     self.smtp_user, self.smtp_password)
        
        result = self.db.execute_query(query, params)
        if result and not self.id:
            self.id = result
        
        from utils.cache import Cache
        Cache.clear("company_data")
        return result is not None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'unique_number': self.unique_number,
            'fiscal_number': self.fiscal_number,
            'account_nib': self.account_nib,
            'logo_path': self.logo_path,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'smtp_user': self.smtp_user,
            'smtp_password': self.smtp_password
        }
