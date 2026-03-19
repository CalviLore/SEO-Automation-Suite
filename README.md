# 🔍 SEO Automation Suite

Una raccolta di script Python per automatizzare l'audit SEO tecnico di un sito e-commerce.
Ogni script è indipendente ma progettato per lavorare in sequenza, dal crawling iniziale fino all'analisi delle performance.

---

## 📦 Script inclusi

| Script | Cosa fa |
|---|---|
| `seo_crawler_audit.py` | Scansiona la sitemap e raccoglie i dati SEO di ogni pagina |
| `seo_audit_report.py` | Legge il CSV e genera un report testuale con le priorità |
| `backlink_auditor.py` | Verifica la qualità dei backlink da Google Search Console |
| `keyword_extractor.py` | Estrae keyword long-tail dai suggerimenti di Google |
| `structured_data_checker.py` | Controlla prezzi e dati strutturati (schema.org) |
| `core_vitals_checker.py` | Misura LCP, CLS e TTFB con un browser Chrome reale |

---

## ⚙️ Installazione

### 1. Clona il repository
```bash
git clone https://github.com/TUO_USERNAME/SEO-Automation-Suite.git
cd SEO-Automation-Suite
```

### 2. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 3. Solo per `core_vitals_checker.py` — installa il browser
```bash
playwright install chrome
```

---

## 🚀 Utilizzo consigliato (flusso completo)

Gli script sono pensati per essere eseguiti in questo ordine:

### Step 1 — Crawling e audit SEO
Modifica la variabile `MIA_SITEMAP` in `seo_crawler_audit.py` con l'URL della tua sitemap, poi lancia:
```bash
python seo_crawler_audit.py
```
Produce: `super_audit_tecnico.csv`

---

### Step 2 — Report problemi
```bash
python seo_audit_report.py
```
Legge `super_audit_tecnico.csv` e stampa a schermo tutti i problemi trovati.
Produce: `pagine_prioritarie_da_sistemare.csv`

---

### Step 3 — Verifica dati strutturati e prezzi
```bash
python structured_data_checker.py
```
Legge `super_audit_tecnico.csv`, filtra i prodotti e verifica lo schema.org.
Produce: `audit_prezzi_COMPLETO.csv`

---

### Step 4 — Analisi backlink
Esporta i backlink da Google Search Console, rinomina il file `backlinks_gsc.csv`
e mettilo nella cartella `backlink/`, poi lancia:
```bash
python backlink_auditor.py
```
Produce: `audit_backlink_COMPLETO.csv`

---

### Step 5 — Keyword research
Modifica la variabile `SEED_KEYWORD` in `keyword_extractor.py`, poi lancia:
```bash
python keyword_extractor.py
```
Produce: `keyword_longtail_[parola_chiave].csv`

---

### Step 6 — Core Web Vitals
Modifica il dizionario `PAGINE_DA_TESTARE` in `core_vitals_checker.py`, poi lancia:
```bash
python core_vitals_checker.py
```
Produce: `report_comparativo_vitals.csv`

---

## 📁 Struttura del progetto

```
SEO-Automation-Suite/
│
├── seo_crawler_audit.py          # Step 1: crawling sitemap + audit SEO
├── seo_audit_report.py           # Step 2: report problemi da CSV
├── structured_data_checker.py    # Step 3: verifica schema.org e prezzi
├── backlink_auditor.py           # Step 4: analisi qualità backlink
├── keyword_extractor.py          # Step 5: estrazione keyword long-tail
├── core_vitals_checker.py        # Step 6: misura Core Web Vitals
│
├── backlink/
│   └── backlinks_gsc.csv         # (da creare) export da Google Search Console
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 📋 Dipendenze

```
pandas
numpy
requests
beautifulsoup4
lxml
playwright
```

Installa tutto con:
```bash
pip install -r requirements.txt
```

---

## 🙈 File ignorati da Git

I file CSV generati dagli script **non vengono tracciati da Git** (vedi `.gitignore`)
perché possono contenere dati sensibili o dati specifici di un sito.

---

## 📌 Compatibilità

- Python 3.8+
- Testato su Windows 10/11 e macOS
- Compatibile con siti PrestaShop e qualsiasi CMS con sitemap XML standard

---

## 📜 Licenza

MIT License — libero per uso personale e commerciale.
