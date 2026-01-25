
from PIL import Image
import os

def create_ico():
    img_path = r"c:\xampp\htdocs\Holkos Fatura\assets\images\logo.png"
    ico_path = r"c:\xampp\htdocs\Holkos Fatura\assets\images\icon.ico"
    
    if os.path.exists(img_path):
        img = Image.open(img_path)
        # Convert to RGBA if not already
        img = img.convert("RGBA")
        # Save as ico with multiple sizes
        img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Ikona u krijua me sukses në: {ico_path}")
    else:
        print(f"Gabim: Logo nuk u gjet në {img_path}")

if __name__ == "__main__":
    create_ico()
