
import subprocess
import os
import sys

def build():
    # Emri i aplikacionit
    name = "Holkos Fatura Debug"
    # Scripti kryesor
    main_script = "main.py"
    # Ikona
    icon = os.path.join("assets", "images", "icon.ico")
    
    # Komanda e PyInstaller
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        # "--windowed",  # E heqim kete per te pare error-et ne terminal
        f"--name={name}",
        f"--icon={icon}",
        "--add-data=assets;assets",
        "--add-data=sql;sql",
        "--add-data=templates;templates",
        "--collect-all=customtkinter",
        main_script
    ]
    
    print(f"Duke filluar paketimin e {name} (me terminal hapur)...")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*30)
        print(f"PROCESI PERFUNDOI.")
        print(f"Hapni kete skedar per te pare nese ka error:")
        print(f"{os.path.abspath('dist')}\\{name}.exe")
        print("="*30)
    except subprocess.CalledProcessError as e:
        print(f"Gabim gjatë paketimit: {e}")

if __name__ == "__main__":
    build()
