"""
Përdor logo-gray.png si burim dhe krijon ikonat e PWA (192, 512, 180px).
Logo duhet të jetë në assets/images/logo-gray.png
"""
from PIL import Image
import os

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public = os.path.join(base, "public")
    logo_path = os.path.normpath(os.path.join(base, "..", "..", "assets", "images", "logo-gray.png"))

    if not os.path.exists(logo_path):
        print(f"Gabim: Logo nuk u gjet në {logo_path}")
        print("Ju lutem vendosni logo-gray.png në assets/images/")
        return

    img = Image.open(logo_path).convert("RGBA")
    print(f"Burim: {logo_path} ({img.size[0]}x{img.size[1]})")

    for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")]:
        out = img.resize((size, size), Image.Resampling.LANCZOS)
        path = os.path.join(public, name)
        out.save(path)
        print(f"U ruajt: {path}")

    print("Ikona u përditësuan!")

if __name__ == "__main__":
    main()
