# Udhëzimet për Deploy të Holkos Fatura

Ky dokument përshkruan hapat për të deployuar aplikacionin Holkos Fatura në Vercel dhe për të lidhur databazën TiDB Cloud.

## Arkitektura e Deploy-it

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vercel        │     │   Render.com    │     │   TiDB Cloud    │
│   (Frontend)    │────▶│   (Backend API) │────▶│   (Database)    │
│   React + Vite  │     │   FastAPI       │     │   MySQL compat. │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Hapi 1: Konfigurimi i TiDB Cloud

### 1.1 Merr credentials nga TiDB Cloud

1. Hyr në [TiDB Cloud Console](https://tidbcloud.com)
2. Zgjidh klusterin tënd
3. Kliko **Connect** → **General** → zgjidh **Operating System**
4. Merr vlerat:
   - **Host** (p.sh. `gateway01.eu-central-1.prod.aws.tidbcloud.com`)
   - **Port**: `4000`
   - **User** (p.sh. `xxxxx.root`)
   - **Password** (Generate ose përdor ekzistuesen)
   - **Database** (p.sh. `test`)

### 1.2 Krijo DATABASE_URL

Format për TiDB Cloud:
```
mysql://USER:PASSWORD@HOST:4000/DATABASE?sslaccept=strict
```

Shembull:
```
mysql://23pY2336LXLw5MR.root:oFv0JzSZ1dk8olqt@gateway01.eu-central-1.prod.aws.tidbcloud.com:4000/test?sslaccept=strict
```

**Shënim**: Kur vendos fjalëkalimin në URL, evita karaktere speciale ose përdor URL encoding (p.sh. `@` → `%40`).

---

## Hapi 2: Deploy i Backend në Render.com

### 2.1 Krijo llogari dhe lidh repo

1. Hyr në [Render.com](https://render.com) dhe krijoni llogari
2. Kliko **New** → **Web Service**
3. Lidh repositorin Git (GitHub/GitLab)
4. Konfiguro:
   - **Name**: `holkos-fatura-api`
   - **Root Directory**: `web/backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 2.2 Variablat e mjedisit në Render

Në **Environment** shto:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `mysql://USER:PASSWORD@HOST:4000/DATABASE?sslaccept=strict` |
| `PYTHON_VERSION` | `3.11` |

Ose përdor variabla të ndara:

| Key | Value |
|-----|-------|
| `TIDB_HOST` | Host nga TiDB Cloud |
| `TIDB_PORT` | `4000` |
| `TIDB_USER` | Username |
| `TIDB_PASSWORD` | Password |
| `TIDB_DATABASE` | `test` |

### 2.3 Deploy dhe merr URL

Pas deploy-it të suksesshëm, merr URL-in (p.sh. `https://holkos-fatura-api.onrender.com`). Ky do të jetë **VITE_API_BASE** për frontend.

---

## Hapi 3: Deploy i Frontend në Vercel

### 3.1 Lidh repo me Vercel

1. Hyr në [Vercel](https://vercel.com)
2. Kliko **Add New** → **Project**
3. Importo repositorin Git

### 3.2 Konfigurimi i projektit

- **Root Directory**: `web/app` (rëndësishme!)
- **Framework Preset**: Vite (detektohet automatikisht)
- **Build Command**: `npm run build` (default)
- **Output Directory**: `dist` (default)

### 3.3 Variablat e mjedisit në Vercel

Shto variablin:

| Key | Value |
|-----|-------|
| `VITE_API_BASE` | URL e backend-it (p.sh. `https://holkos-fatura-api.onrender.com`) |

**Shënim**: Në zhvillim lokal, frontend përdor `/api` (proxy në localhost:8000). Për prod, përdor URL-in e plotë të backend-it.

### 3.4 TiDB Cloud Integration (Opsional)

Për konfigurim automatik të databazës:

1. Në Vercel, shko te **Integrations**
2. Shto **TiDB Cloud** nga Marketplace
3. Ndiq hapat për të lidhur klusterin

Kjo vendos automatikisht `TIDB_HOST`, `TIDB_PORT`, etj. për backend (nëse backend është në të njëjtën platformë).

---

## Hapi 4: Verifikimi

1. **Backend**: Hap `https://[backend-url]/` – duhet të shfaqet `{"message": "Holkos Fatura API is running"}`
2. **Frontend**: Hap URL-in e Vercel – aplikacioni duhet të ngarkohet
3. **Testo lidhjen**: Krijo një klient ose faturë për të verifikuar lidhjen me TiDB

---

## Skema e Databazës

Sigurohu që databaza TiDB ka tabelat e nevojshme. Ekzekuto skemën në TiDB Cloud:

1. Në TiDB Cloud Console → **Connect** → **Connect with SQL Client** (ose Chat2Query)
2. Ekzekuto përmbajtjen e skedarit `sql/schema.sql` nga rrënja e projektit

---

## Troubleshooting

### CORS errors
Backend ka `allow_origins=["*"]`. Nëse ke probleme, kontrollo që domajni i Vercel është në listë.

### Database connection failed
- Verifiko që IP e Render është e lejuar në TiDB Cloud (Access List) – për klustera Dedicated, vendos `0.0.0.0/0` për publik
- Kontrollo që DATABASE_URL është i saktë (pa hapësira, me `sslaccept=strict`)

### Frontend nuk lidhet me API
- Verifiko që `VITE_API_BASE` është vendosur në Vercel (Environment Variables)
- Pas ndryshimit të variablave, bëj **Redeploy** që Vite ta përfshijë në build

---

## Struktura e projektit

```
web/
├── app/           ← Frontend (Vercel - Root: web/app)
│   ├── vercel.json
│   ├── .env.example
│   └── src/
├── backend/       ← Backend (Render - Root: web/backend)
│   ├── main.py
│   ├── database.py
│   ├── .env.example
│   └── render.yaml
└── DEPLOY.md      ← Ky dokument
```
