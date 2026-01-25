# Quick Start Guide - Holkos Fatura

## Hapat e para

### 1. Instalimi i Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup i Databazës

**Opsioni 1: Automatik (Rekomandohet)**
```bash
python setup_database.py
```

**Opsioni 2: Manual**
1. Startoni MySQL në xampp
2. Hapni phpMyAdmin ose MySQL command line
3. Krijoni databazën:
   ```sql
   CREATE DATABASE holkos_fatura;
   ```
4. Ekzekutoni skemën:
   ```bash
   mysql -u root holkos_fatura < sql/schema.sql
   ```

### 3. Konfigurimi

Nëse MySQL ka password, ndrysho në `config/database.py`:
```python
self.password = "password_jote"
```

### 4. Ekzekutimi i Aplikacionit

```bash
python main.py
```

## Përdorimi

### Krijimi i Faturave

1. Kliko "Fatura të reja" në sidebar
2. Zgjedh ose shto klient të ri
3. Plotëso informacionet e faturave
4. Shto artikujt (përshkrimi, sasia në m², çmimi)
5. Totalet llogariten automatikisht
6. Kliko "Ruaj dhe Gjenero PDF"

### Menaxhimi i Klientëve

1. Kliko "Klientë" në sidebar
2. Plotëso formularin dhe kliko "Ruaj"
3. Përdor "Kërko" për të gjetur klientë ekzistues
4. Përdor "Redakto" ose "Fshi" për menaxhim

### Cilësimet e Kompanisë

1. Kliko "Cilësime" në sidebar
2. Plotëso informacionet e kompanisë
3. Zgjedh logo (opsional)
4. Kliko "Ruaj"

### Lista e Faturave

1. Kliko "Lista faturave" në sidebar
2. Përdor filtra për të gjetur fatura specifike
3. Përdor butonat për shikim, redaktim, gjenerim PDF, ose fshirje

## Struktura e Dosjeve

- `exports/` - PDF-të e gjeneruara ruhen këtu
- `assets/images/` - Logo e kompanisë
- `sql/` - Skema e databazës

## Troubleshooting

### Gabim: "Nuk mund të lidhet me databazën"
- Sigurohu që MySQL është i startuar në xampp
- Kontrollo credentials në `config/database.py`
- Verifiko që databaza `holkos_fatura` ekziston

### PDF nuk gjenerohet
- Sigurohu që ka artikuj në fatura
- Kontrollo që fatura është e ruajtur
- Verifiko që dosja `exports/` ekziston dhe ka të drejta shkrimi

### Klientët nuk shfaqen
- Sigurohu që ka klientë të ruajtur në databazë
- Përdor "Klientë" për të shtuar klientë të rinj

## Mbështetje

Për probleme ose pyetje, kontrollo dokumentacionin në `README.md`

