# Sistem Fatura PDF - Holkos

Aplikacion desktop për gjenerimin automatik të faturave PDF me menaxhim shabllonash dhe klientësh.

## Teknologjitë

- Python 3.8+
- CustomTkinter - GUI modern
- MySQL - Databazë
- ReportLab - Gjenerimi i PDF-ve
- Pillow - Përpunimi i imazheve

## Instalimi

1. Instaloni dependencies:
```bash
pip install -r requirements.txt
```

2. Startoni MySQL në xampp

3. Krijoni databazën:
```sql
CREATE DATABASE holkos_fatura;
```

4. Ekzekutoni skemën:
```bash
mysql -u root holkos_fatura < sql/schema.sql
```

5. Konfiguroni databazën në `config/database.py`

6. Ekzekutoni aplikacionin:
```bash
python main.py
```

## Struktura e Projektit

- `config/` - Konfigurime
- `models/` - Modelet e të dhënave
- `views/` - Interfejsit grafike
- `services/` - Shërbimet (PDF generator, etj.)
- `templates/` - Shabllonat e faturave
- `sql/` - Skema e databazës
- `exports/` - PDF-të e gjeneruara
- `assets/` - Imazhe dhe fonta

