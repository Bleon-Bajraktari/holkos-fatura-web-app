"""
Shton background gri (#9ca3af) në ikonat e PWA.
Zëvendëson edhe të bardhën (piksela jo transparente) me gri.
Ekzekuto: python add_icon_bg.py (nga web/app/scripts/)
"""
from PIL import Image
import os

GRAY_BG = (0x9c, 0xa3, 0xaf, 255)  # #9ca3af
WHITE_THRESHOLD = 235  # Pikselat me R,G,B > kjo merren si "background" dhe zëvendësohen me gri

def is_white_or_transparent(pixel):
    if len(pixel) >= 4 and pixel[3] < 30:
        return True  # Transparent
    if len(pixel) >= 3:
        r, g, b = pixel[0], pixel[1], pixel[2]
        return r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD
    return False

def add_gray_bg(img_path: str, out_path: str, size: int):
    if not os.path.exists(img_path):
        print(f"Gabim: {img_path} nuk ekziston")
        return False
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    pixels = img.load()
    # Zëvendëso të bardhën dhe transparent me gri
    for y in range(h):
        for x in range(w):
            p = pixels[x, y]
            if is_white_or_transparent(p):
                pixels[x, y] = GRAY_BG
    if size and (w != size or h != size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    img.save(out_path)
    print(f"U ruajt: {out_path}")
    return True

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public = os.path.join(base, "public")
    assets_logo = os.path.normpath(os.path.join(base, "..", "..", "assets", "images", "logo.png"))

    # Burimi: logo.png origjinal (me background të bardhë) për ta zëvendësuar me gri
    src = assets_logo
    if not os.path.exists(src):
        src = os.path.join(public, "icon-512.png")
    if not os.path.exists(src):
        print("Gabim: Nuk u gjet asnjë burim për ikonat.")
        return

    add_gray_bg(src, os.path.join(public, "icon-192.png"), 192)
    add_gray_bg(src, os.path.join(public, "icon-512.png"), 512)
    add_gray_bg(src, os.path.join(public, "apple-touch-icon.png"), 180)
    print("Ikona u përditësuan me background gri.")

if __name__ == "__main__":
    main()
