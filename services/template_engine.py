"""
Motor për përpunimin e shabllonave
"""
import re
from typing import Dict, Any

class TemplateEngine:
    """Klasa për përpunimin e shabllonave me variabla"""
    
    @staticmethod
    def render(template_content: str, variables: Dict[str, Any]) -> str:
        """
        Zëvendëson variablat në shabllon me vlerat aktuale
        
        Variablat në format {{variable_name}}
        """
        result = template_content
        
        # Zëvendëso variablat
        for key, value in variables.items():
            pattern = r'\{\{' + re.escape(key) + r'\}\}'
            result = re.sub(pattern, str(value), result)
        
        return result
    
    @staticmethod
    def extract_variables(template_content: str) -> list:
        """Nxjerr të gjitha variablat nga shablloni"""
        pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(pattern, template_content)
        return list(set(variables))  # Kthen lista unike

