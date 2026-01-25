import subprocess
import os
import sys

def build_backup_tool():
    name = "BackupTool"
    script = "create_backup.py"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # Ky ka GUI (CustomTkinter) prandaj nuk duam console
        f"--name={name}",
        "--add-data", "config;config", # Përfshijmë konfigurimin
        script
    ]
    
    print(f"Duke krijuar {name}.exe...")
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*40)
        print(f"SUKSES! Vegla u krijua: dist\\{name}.exe")
        print("Kopjojeni këtë skedar në kompjuterin tjetër dhe përdoreni për Backup.")
        print("="*40)
    except subprocess.CalledProcessError as e:
        print(f"Gabim: {e}")

if __name__ == "__main__":
    build_backup_tool()
