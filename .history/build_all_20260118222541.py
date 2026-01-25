import subprocess
import os
import sys
import shutil

def build_all():
    # 1. Pastro buildup-in e vjetër në dist
    if os.path.exists("dist"):
        print("Duke pastruar folderin 'dist'...")
        shutil.rmtree("dist")
    
    components = [
        {
            "name": "Holkos Fatura",
            "script": "main.py",
            "type": "--windowed",
            "icon": "icon.ico"
        },
        {
            "name": "DataMigrator",
            "script": "migrate_data.py",
            "type": "--console",
            "icon": None
        },
        {
            "name": "BackupTool",
            "script": "create_backup.py",
            "type": "--windowed",
            "icon": None
        }
    ]

    for item in components:
        print(f"\n--- Duke ndërtuar: {item['name']} ---")
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--onefile",
            item["type"],
            f"--name={item['name']}"
        ]
        
        # Shto ikone nese ka
        if item["icon"]:
            icon_path = os.path.join("assets", "images", item["icon"])
            if os.path.exists(icon_path):
                cmd.append(f"--icon={icon_path}")

        # Shto folderat e nevojshem si data
        cmd.extend(["--add-data", "config;config"])
        cmd.extend(["--add-data", "models;models"])
        cmd.extend(["--add-data", "views;views"])
        cmd.extend(["--add-data", "services;services"])
        cmd.extend(["--add-data", "assets;assets"])
        cmd.extend(["--add-data", "sql;sql"])
        
        cmd.append(item["script"])
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ U ndërtua me sukses: {item['name']}")
        except Exception as e:
            print(f"❌ Gabim gjatë ndërtimit të {item['name']}: {e}")

    print("\n" + "="*50)
    print("PROCESI PËRFUNDOI ME SUKSES!")
    print("Të gjitha skedarët ndodhen në folderin: dist/")
    print("1. Holkos Fatura.exe (Aplikacioni)")
    print("2. DataMigrator.exe (Për dërgim në Cloud)")
    print("3. BackupTool.exe (Për ruajtje të dhënash)")
    print("="*50)

if __name__ == "__main__":
    build_all()
