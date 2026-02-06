"""
Shton background gri (#9ca3af) në ikonat e PWA.
Ekzekuto: python add_icon_bg.py (nga web/app/scripts/)
"""
from PIL import Image
import os

GRAY_BG = (0x9c, 0xa3, 0xaf, 255)  # #9ca3af

def add_gray_bg(img_path: str, out_path: str, size: int):
    if not os.path.exists(img_path):
        print(f"Gabim: {img_path} nuk ekziston")
        return False
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    # Krijo canvas gri dhe vendos logo mbi të (transparent -> gri)
    bg = Image.new("RGBA", (w, h), GRAY_BG)
    bg.paste(img, (0, 0), img)
    if size and (w != size or h != size):
        bg = bg.resize((size, size), Image.Resampling.LANCZOS)
    bg.save(out_path)
    print(f"U ruajt: {out_path}")
    return True

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public = os.path.join(base, "public")
    assets_logo = os.path.normpath(os.path.join(base, "..", "..", "assets", "images", "logo.png"))

    # Burimi: icon-512.png ekzistues ose logo.png
    src = os.path.join(public, "icon-512.png")
    if not os.path.exists(src):
        src = assets_logo
    if not os.path.exists(src):
        print("Gabim: Nuk u gjet asnjë burim për ikonat.")
        return

    add_gray_bg(src, os.path.join(public, "icon-192.png"), 192)
    add_gray_bg(src, os.path.join(public, "icon-512.png"), 512)
    add_gray_bg(src, os.path.join(public, "apple-touch-icon.png"), 180)
    print("Ikona u përditësuan me background gri.")

if __name__ == "__main__":
    main()
