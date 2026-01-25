
import subprocess
import os
import sys

def build_migrator():
    name = "DataMigrator"
    script = "migrate_data.py"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--console",  # Duam console që të shohim progresin
        f"--name={name}",
        script
    ]
    
    print(f"Duke krijuar {name}.exe...")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*40)
        print(f"SUKSES! Vegla u krijua: dist\\{name}.exe")
        print("Kopjojeni këtë skedar në kompjuterin tjetër dhe ekzekutojeni.")
        print("="*40)
    except subprocess.CalledProcessError as e:
        print(f"Gabim: {e}")

if __name__ == "__main__":
    build_migrator()
