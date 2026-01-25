
import subprocess
import os
import sys

def build():
    # Emri i aplikacionit
    name = "Holkos Fatura"
    # Scripti kryesor
    main_script = "main.py"
    # Ikona
    icon = os.path.join("assets", "images", "icon.ico")
    
    # Komanda e PyInstaller
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={name}",
        f"--icon={icon}",
        # Shtimi i aseteve (folderat e UI dhe imazhet)
        "--add-data=assets;assets",
        "--add-data=sql;sql",
        "--add-data=templates;templates",
        # CustomTkinter kërkon këtë për të funksionuar si .exe
        "--collect-all=customtkinter",
        main_script
    ]
    
    print(f"Duke filluar paketimin e {name}...")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*30)
        print(f"SUKSES! Programi u krijua në folderin 'dist'.")
        print(f"Mund ta gjeni këtu: {os.path.abspath('dist')}\\{name}.exe")
        print("="*30)
    except subprocess.CalledProcessError as e:
        print(f"Gabim gjatë paketimit: {e}")

if __name__ == "__main__":
    build()
