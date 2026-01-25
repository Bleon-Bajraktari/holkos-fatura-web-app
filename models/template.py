"""
Modeli për shabllonat e faturave
"""
from models.database import Database

class Template:
    """Klasa për menaxhimin e shabllonave"""
    
    def __init__(self, db=None):
        self.db = db or Database()
        self.id = None
        self.name = ""
        self.description = ""
        self.template_file = ""
        self.is_active = True
        self.is_default = False
        self.created_at = None
        self.updated_at = None
    
    @staticmethod
    def get_all(db=None):
        """Merr të gjithë shabllonat"""
        database = db or Database()
        query = "SELECT * FROM templates ORDER BY is_default DESC, name"
        result = database.execute_query(query)
        return result or []
    
    @staticmethod
    def get_active(db=None):
        """Merr shabllonat aktive"""
        database = db or Database()
        query = "SELECT * FROM templates WHERE is_active = TRUE ORDER BY is_default DESC, name"
        result = database.execute_query(query)
        return result or []
    
    @staticmethod
    def get_default(db=None):
        """Merr shabllonin default"""
        database = db or Database()
        query = "SELECT * FROM templates WHERE is_default = TRUE LIMIT 1"
        result = database.execute_query(query)
        
        if result and len(result) > 0:
            template = Template(db)
            data = result[0]
            template.id = data['id']
            template.name = data['name'] or ""
            template.description = data['description'] or ""
            template.template_file = data['template_file'] or ""
            template.is_active = data['is_active']
            template.is_default = data['is_default']
            return template
        return None
    
    @staticmethod
    def get_by_id(template_id, db=None):
        """Merr një shabllon sipas ID"""
        database = db or Database()
        query = "SELECT * FROM templates WHERE id = %s"
        result = database.execute_query(query, (template_id,))
        
        if result and len(result) > 0:
            template = Template(db)
            data = result[0]
            template.id = data['id']
            template.name = data['name'] or ""
            template.description = data['description'] or ""
            template.template_file = data['template_file'] or ""
            template.is_active = data['is_active']
            template.is_default = data['is_default']
            return template
        return None
    
    def save(self):
        """Ruaj shabllonin"""
        if self.id:
            # Update
            query = """UPDATE templates SET 
                name = %s, description = %s, template_file = %s,
                is_active = %s, is_default = %s
                WHERE id = %s"""
            params = (self.name, self.description, self.template_file,
                     self.is_active, self.is_default, self.id)
        else:
            # Insert
            query = """INSERT INTO templates 
                (name, description, template_file, is_active, is_default)
                VALUES (%s, %s, %s, %s, %s)"""
            params = (self.name, self.description, self.template_file,
                     self.is_active, self.is_default)
        
        result = self.db.execute_query(query, params)
        if result and not self.id:
            self.id = result
        return result is not None
    
    def set_as_default(self):
        """Vendos këtë shabllon si default"""
        # Heq default nga të gjithë shabllonat
        query = "UPDATE templates SET is_default = FALSE"
        self.db.execute_query(query)
        
        # Vendos këtë si default
        self.is_default = True
        return self.save()
    
    def delete(self):
        """Fshi shabllonin"""
        if not self.id:
            return False
        
        query = "DELETE FROM templates WHERE id = %s"
        result = self.db.execute_query(query, (self.id,))
        return result is not None
    
    def to_dict(self):
        """Kthen të dhënat si dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_file': self.template_file,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

