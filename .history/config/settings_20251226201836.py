"""
Cilësime globale të aplikacionit
"""
import os

# Rrugët e dosjeve
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# Krijo dosjet nëse nuk ekzistojnë
for directory in [EXPORTS_DIR, ASSETS_DIR, TEMPLATES_DIR, IMAGES_DIR, FONTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Cilësime default
DEFAULT_VAT_PERCENTAGE = 18.0
DEFAULT_INVOICE_NUMBER_FORMAT = "FATURA NR.{number}"
DEFAULT_DATE_FORMAT = "%d.%m.%Y"

# Emri i aplikacionit
APP_NAME = "Holkos Fatura"
APP_VERSION = "1.0.0"

