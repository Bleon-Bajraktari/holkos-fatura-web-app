# Sistem Fatura PDF - Holkos

Aplikacion desktop dhe web për gjenerimin automatik të faturave dhe ofertave PDF me menaxhim shabllonash dhe klientësh.

## Teknologjitë

- Python 3.8+
- CustomTkinter - GUI modern (Desktop)
- React + TypeScript + Vite - Frontend (Web)
- FastAPI - Backend (Web)
- MySQL - Databazë
- ReportLab - Gjenerimi i PDF-ve
- Pillow - Përpunimi i imazheve

## Instalimi

### Desktop Application

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

### Web Application

1. Instaloni dependencies për backend:
```bash
cd web/backend
pip install -r requirements.txt
```

2. Instaloni dependencies për frontend:
```bash
cd web/app
npm install
```

3. Startoni backend:
```bash
cd web/backend
python main.py
```

4. Startoni frontend:
```bash
cd web/app
npm run dev
```

## Struktura e Projektit

- `config/` - Konfigurime
- `models/` - Modelet e të dhënave
- `views/` - Interfejsit grafike (Desktop)
- `services/` - Shërbimet (PDF generator, etj.)
- `templates/` - Shabllonat e faturave
- `sql/` - Skema e databazës
- `exports/` - PDF-të e gjeneruara
- `assets/` - Imazhe dhe fonta
- `web/app/` - Frontend React application
- `web/backend/` - Backend FastAPI application
