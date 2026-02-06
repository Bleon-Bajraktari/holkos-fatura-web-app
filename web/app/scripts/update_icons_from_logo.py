"""
- logo-gray.png → ikonat e PWA (icon-192, icon-512, apple-touch-icon)
- logo.png (e bardha) → login-logo.png (për faqen e login-it)
"""
from PIL import Image
import os
import shutil

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public = os.path.join(base, "public")
    assets = os.path.normpath(os.path.join(base, "..", "..", "assets", "images"))
    logo_gray = os.path.join(assets, "logo-gray.png")
    logo_white = os.path.join(assets, "logo.png")

    # Logo e bardhë për faqen e login-it
    if os.path.exists(logo_white):
        shutil.copy2(logo_white, os.path.join(public, "login-logo.png"))
        print(f"U kopjua login-logo.png (nga logo.png)")
    else:
        print("Njoftim: logo.png nuk u gjet – faqja e login do të përdorë ikonën e PWA.")

    if not os.path.exists(logo_gray):
        print(f"Gabim: Logo-gray nuk u gjet në {logo_gray}")
        return

    img = Image.open(logo_gray).convert("RGBA")
    print(f"Burim PWA: {logo_gray} ({img.size[0]}x{img.size[1]})")

    for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")]:
        out = img.resize((size, size), Image.Resampling.LANCZOS)
        path = os.path.join(public, name)
        out.save(path)
        print(f"U ruajt: {path}")

    print("Ikona u përditësuan!")

if __name__ == "__main__":
    main()
