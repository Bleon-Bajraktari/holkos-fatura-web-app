"""
Cilësime globale të aplikacionit - Fix për .exe
"""
import os
import sys

# Gjej drejtorinë ku ndodhet .exe ose scripti (për të shmangur folderat temp)
if getattr(sys, 'frozen', False):
    # Nëse është .exe, përdor folderin ku ndodhet .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Nëse është script, përdor folderin e projektit
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Drejtoritë e të dhënave (Tani janë jashtë folderit temp)
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# Krijo dosjet nëse nuk ekzistojnë (në vendndodhjen korrekte)
for directory in [EXPORTS_DIR, ASSETS_DIR, TEMPLATES_DIR, IMAGES_DIR, FONTS_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
    except:
        pass

# Cilësime default
DEFAULT_VAT_PERCENTAGE = 18.0
DEFAULT_INVOICE_NUMBER_FORMAT = "FATURA NR.{number}"
DEFAULT_DATE_FORMAT = "%d.%m.%Y"

# Emri i aplikacionit
APP_NAME = "Holkos Fatura"
APP_VERSION = "1.0.5" # Version i ri për të konfirmuar ndryshimin
