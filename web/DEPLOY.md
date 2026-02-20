# Udhëzimet për Deploy të Holkos Fatura

Ky dokument përshkruan hapat për të deployuar aplikacionin Holkos Fatura në Vercel dhe për të lidhur databazën TiDB Cloud.

---

## Gati për Render dhe Vercel

Projekti është **i gatshëm** për deploy:

- **Backend (Render):** `web/backend` – ka `requirements.txt`, `render.yaml`, dhe `uvicorn` si start. Migrimi i DB (përfshirë tabelën `contracts`) ekzekutohet në startup.
- **Frontend (Vercel):** `web/app` – ka `vercel.json` me rewrites: `/api/*` dërgohet te Render API; `/uploads/*` te Render; pjesa tjetër SPA.
- **CORS:** Backend lejon `allow_origins=["*"]`, i përshtatshëm për çdo domen Vercel.

**Nëse URL-i i backend-it në Render është i ndryshëm** nga `https://holkos-fatura-api.onrender.com`, ndrysho në `web/app/vercel.json` fushat `destination` me URL-in tënd të Render.

---

## Checklist për Deploy (shpejtë)

| Hapi | Vercel (Frontend) | Render (Backend) |
|------|-------------------|------------------|
| Root Directory | `web/app` | `web/backend` |
| Build | `npm run build` | `pip install -r requirements.txt` |
| Start | (static) | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Env vars | (opsional) BACKEND_URL | DATABASE_URL, **JWT_SECRET_KEY**, PYTHON_VERSION |

**Obligatorisht në Render:** Vendos `JWT_SECRET_KEY` (gjenero me `openssl rand -hex 32`).

---

## Push dhe Deploy – hapat e shpejtë

1. **Sigurohu që `.env` nuk përfshihet në Git**  
   Skedari `.gitignore` përmban `.env` dhe `web/backend/.env` – mos hiq këto rreshta.

2. **Push në GitHub**:
   ```bash
   git add .
   git status   # kontrollo që .env nuk është në listë
   git commit -m "Gati për deploy – Vercel + Render + TiDB"
   git push origin main
   ```

3. **Backend (Render.com)**  
   Nëse projekti ekziston: push aktivizon redeploy.  
   Nëse është i ri: **New** → **Web Service** → lidh repo, **Root Directory**: `web/backend`, **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`.  
   Në **Environment** vendos: `DATABASE_URL` (TiDB Cloud), `JWT_SECRET_KEY` (openssl rand -hex 32), `PYTHON_VERSION=3.11.10`.

4. **Frontend (Vercel)**  
   Nëse projekti ekziston: push aktivizon redeploy.  
   Nëse është i ri: **Add New** → **Project** → lidh repo, **Root Directory**: `web/app`.  
   Opsional për email: në **Environment** shto `BACKEND_URL=https://holkos-fatura-api.onrender.com`.

5. **Pas deploy-it**  
   Hap URL-in e Vercel dhe testo: Cilësimet, Faturat, dërgimi i email-it (nëse ke plotësuar SMTP në Cilësimet dhe BACKEND_URL në Vercel).

---

## Arkitektura e Deploy-it

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vercel        │     │   Render.com    │     │   TiDB Cloud    │
│   (Frontend)    │────▶│   (Backend API) │────▶│   (Database)    │
│   React + Vite  │     │   FastAPI       │     │   MySQL compat. │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Zhvillim Lokal (Localhost)

### Backend (`web/backend`)

1. **Kopjo .env**:
   ```bash
   cd web/backend
   cp .env.example .env
   ```

2. **Plotëso .env**:
   - **DATABASE_URL** – TiDB Cloud (si më poshtë) OSE MySQL lokal:
     ```bash
     # MySQL lokal (XAMPP):
     DATABASE_URL=mysql+pymysql://root:@localhost:3306/holkos_fatura1
     ```
   - Për email (opsional): plotëso SMTP në Cilësimet pas deploy

3. **Starto backend**:
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Testo**: `http://localhost:8000/` dhe `http://localhost:8000/email/status`

### Frontend (`web/app`)

1. **Plotëso .env** (opsional – default është `/api`):
   ```
   VITE_API_BASE=/api
   ```

2. **Starto frontend**:
   ```bash
   cd web/app
   npm install
   npm run dev
   ```

3. **Proxy**: Vite proxy `/api` → `http://localhost:8000` (shiko `vite.config.ts`)

---

## Importimi i backup-it në Cloud

Për të marrë të dhënat nga një pajisje tjetër (p.sh. backup nga Holkos Fatura LOKAL) dhe për t’i vendosur në TiDB Cloud:

1. **Sigurohu që tabelat ekzistojnë** në TiDB Cloud. Nëse databaza është e re, ekzekuto fillimisht `sql/schema.sql` nga TiDB Cloud Console.
2. **Kopjo skedarin e backup-it** (`.sql`) në projektin.
3. **Konfiguro `web/backend/.env`** me `DATABASE_URL` të TiDB Cloud (si në hapat e mësipërm).
4. **Ekzekuto skriptin e importit**:
   ```bash
   python import_backup_to_cloud.py backup.sql
   ```
   ose, pa argument, jep shtegun kur pyetet.
5. Konfirmo me `po` kur pyetet.
6. Pas importit, `pdf_path` pastrohet automatikisht (shtigjet lokale nuk vlejnë në cloud; PDF-et gjenerohen në kërkesë).

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
| `PYTHON_VERSION` | `3.11.10` |
| `JWT_SECRET_KEY` | Sekret i fortë (min. 32 kar.): `openssl rand -hex 32` |
| `APP_INITIAL_USERNAME` | `admin` (opsional, default) |
| `APP_INITIAL_PASSWORD` | `holkos2025` (opsional, ndrysho nga Cilësimet pas login) |

**E rëndësishme:** `JWT_SECRET_KEY` duhet të jetë i ndryshëm në prod. Gjenero: `openssl rand -hex 32`

Ose përdor variabla të ndara:

| Key | Value |
|-----|-------|
| `TIDB_HOST` | Host nga TiDB Cloud |
| `TIDB_PORT` | `4000` |
| `TIDB_USER` | Username |
| `TIDB_PASSWORD` | Password |
| `TIDB_DATABASE` | `test` |

### 2.3 Deploy dhe merr URL

Pas deploy-it të suksesshëm, merr URL-in (p.sh. `https://holkos-fatura-api.onrender.com`). Ky duhet të jetë i njëjtë me `vercel.json` rewrites (nëse ndryshon, ndërroje atje).

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

**Nuk nevojiten** – frontend përdor `VITE_API_BASE=/api` për localhost dhe deploy. `vercel.json` rewrites drejtojnë `/api` te Render backend.

Nëse backend-i yt ka URL tjetër, ndërro në `web/app/vercel.json` në `rewrites.destination`.

### 3.4 TiDB Cloud Integration (Opsional)

Për konfigurim automatik të databazës:

1. Në Vercel, shko te **Integrations**
2. Shto **TiDB Cloud** nga Marketplace
3. Ndiq hapat për të lidhur klusterin

Kjo vendos automatikisht `TIDB_HOST`, `TIDB_PORT`, etj. për backend (nëse backend është në të njëjtën platformë).

---

## Hapi 4: Verifikimi

1. **Backend**: Hap `https://[backend-url]/` – duhet të shfaqet `{"message": "Holkos Fatura API is running"}`
2. **Backend health**: Hap `https://[backend-url]/health` – `{"status":"ok","database":"connected"}`
3. **Frontend**: Hap URL-in e Vercel – duhet të shfaqet faqja e Login
4. **Login**: Përdor `admin` / `holkos2025` (ose kredencialet nga APP_INITIAL_*)
5. **Testo**: Krijo një klient ose faturë për të verifikuar lidhjen me TiDB

---

## Skema e Databazës

Sigurohu që databaza TiDB ka tabelat e nevojshme. Ekzekuto skemën në TiDB Cloud:

1. Në TiDB Cloud Console → **Connect** → **Connect with SQL Client** (ose Chat2Query)
2. Ekzekuto përmbajtjen e skedarit `sql/schema.sql` nga rrënja e projektit

---

## Troubleshooting

### Të dhënat nuk shfaqen (lidhja me databazë / API)

**1. Kontrollo vercel.json rewrites**
- `web/app/vercel.json` duhet të ketë rewrites që drejtojnë `/api` te Render backend
- URL-i në `destination` duhet të përputhet me URL-in e backend-it (p.sh. `https://holkos-fatura-api.onrender.com`)
- Nëse backend-i ka URL tjetër, ndërro në vercel.json dhe bëj Redeploy

**2. Kontrollo që backend-i (Render) funksionon**
- Hap `https://[backend-url]/` – duhet të shfaqet `{"message": "Holkos Fatura API is running"}`
- Hap `https://[backend-url]/health` – duhet `{"status": "ok", "database": "connected"}`
- Nëse 502/503: Render (free tier) fiket pas 15 min – prit 30–60 s dhe rifresko
- Nëse `/health` tregon `database: error`: DATABASE_URL në Render është gabim

**3. Kontrollo DATABASE_URL në Render**
- Në Render: **Environment** → sigurohu që `DATABASE_URL` është i vendosur saktë
- Format: `mysql://USER:PASSWORD@HOST:4000/test?sslaccept=strict`
- Pas ndryshimit, bëj **Redeploy** të backend-it

**4. Kontrollo skemën e databazës**
- Ekzekuto `sql/schema.sql` në TiDB Cloud nëse tabelat nuk ekzistojnë
- Verifiko që databaza ka të dhëna

### Email nuk dërgohet
**SMTP nga Cilësimet (Gmail/Outlook)** – përdor Vercel Serverless Function:
1. Plotëso Cilësimet → Konfigurimi i Email-it (smtp_server, smtp_user, smtp_password)
2. Për Gmail: përdor **App Password** (jo fjalëkalimin normal) – krijo në Google Account → Security → App Passwords
3. Në Vercel Environment: shto `BACKEND_URL=https://holkos-fatura-api.onrender.com`
4. Funksionon vetëm në deploy (Vercel) – localhost përdor backend SMTP direkt

### CORS errors (Access-Control-Allow-Origin)
Backend ka konfigurim për `*.vercel.app`. Nëse ende ke CORS:
- Bëj **Redeploy** të backend-it në Render (ndryshimet e CORS duhet të aplikohen)
- Shto origjinën në Render: **Environment** → `CORS_ORIGINS=https://emri-projektit.vercel.app`

### CORS të tjera
Backend ka `allow_origins=["*"]`. Nëse ke probleme, kontrollo që domajni i Vercel është në listë.

### Database connection failed
- Verifiko që IP e Render është e lejuar në TiDB Cloud (Access List) – për klustera Dedicated, vendos `0.0.0.0/0` për publik
- Kontrollo që DATABASE_URL është i saktë (pa hapësira, me `sslaccept=strict`)

### Frontend nuk lidhet me API
- Verifiko që `web/app/vercel.json` rewrites drejtojnë `/api` te URL-i i saktë të backend-it
- Kontrollo që backend-i (Render) është i vënë në punë dhe `/health` kthen OK

### Login vonon shumë (cold start)
- Render free tier fiket pas 15 min. Hapja e parë e faqes së login ngre serverin në sfond (ping `/health`).
- Nëse login dështon me "Serveri po ngrohet..." – prit 30–60 s dhe provo përsëri.
- Për server gjithmonë aktiv: përdor planin e paguar të Render.

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
