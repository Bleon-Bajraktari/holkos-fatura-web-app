"""
Cilësime globale të aplikacionit - Versioni 1.0.6 (Fix për Asetet dhe Persistencën)
"""
import os
import sys

# 1. Drejtoria e Paketuar (Aty ku ndodhen asetet brenda .exe)
if getattr(sys, 'frozen', False):
    # PyInstaller krijon një folder të përkohshëm në _MEIPASS
    BUNDLE_DIR = sys._MEIPASS
    # Drejtoria ku ndodhet vetë skedari .exe (për të dhënat që duam të mbeten)
    DATA_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = BUNDLE_DIR

# Drejtoritë statike (Brenda .exe)
ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SQL_DIR = os.path.join(BUNDLE_DIR, "sql")

# Drejtoritë e të dhënave (Jashtë .exe - Persistente)
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")

# Krijo dosjet e të dhënave nëse nuk ekzistojnë në disk
for directory in [EXPORTS_DIR, TEMPLATES_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
    except:
        pass

# Cilësime default
DEFAULT_VAT_PERCENTAGE = 18.0
DEFAULT_INVOICE_NUMBER_FORMAT = "FATURA NR.{number}"
DEFAULT_DATE_FORMAT = "%d.%m.%Y"
APP_NAME = "Holkos Fatura"
APP_VERSION = "1.0.6"
