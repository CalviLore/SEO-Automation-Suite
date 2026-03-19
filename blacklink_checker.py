"""
===============================================================
 BACKLINK AUDITOR - Analisi qualità dei link in entrata
===============================================================
Cosa fa questo script:
  Legge un file CSV esportato da Google Search Console contenente
  i siti esterni che puntano al tuo sito (i "backlink").

  Per ogni link effettua una visita alla pagina sorgente e valuta:
    - Se il link è ancora presente (o è stato rimosso)
    - Dove si trova nella pagina (articolo, footer, sidebar...)
    - Il testo cliccabile del link (anchor text)
    - Se il sito sorgente contiene contenuti tossici (spam, gambling, ecc.)

  Produce un punteggio di qualità (Power Score) per ogni backlink
  e salva tutto in un CSV finale per analisi e pulizia.

Come si usa:
  1. Esporta i backlink da Google Search Console in formato CSV
  2. Rinomina il file "backlinks_gsc.csv" e mettilo nella cartella "backlink/"
  3. Cambia `MIO_DOMINIO` con il tuo dominio (es. "example.com")
  4. Lancia: python backlink_auditor.py

Struttura cartelle richiesta:
  progetto/
  ├── backlink_auditor.py
  └── backlink/
      └── backlinks_gsc.csv     <-- file esportato da Search Console

Dipendenze richieste:
  pip install pandas requests beautifulsoup4
===============================================================
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time


# ==========================================
# CONFIGURAZIONE - Modifica questi valori
# ==========================================
MIO_DOMINIO       = "www.EXAMPLE_SITE.com"          # <-- inserisci il tuo dominio
FILE_INPUT        = "backlink/backlinks_gsc.csv"     # <-- percorso del CSV di Search Console
FILE_OUTPUT       = "audit_backlink_COMPLETO.csv"    # <-- nome del file di output finale

# Parole che identificano siti tossici o spam
PAROLE_TOSSICHE   = ['casino', 'betting', 'crypto', 'porn']


# ==========================================
# 1. ANALISI DI UN SINGOLO BACKLINK
#    Visita la pagina sorgente e valuta la qualità del link
# ==========================================
def analizza_singolo_link(url_sorgente, mio_dominio):
    """
    Visita una pagina esterna e valuta la qualità del backlink verso il nostro sito.

    Parametri:
        url_sorgente (str): URL della pagina che contiene (o dovrebbe contenere) il link
        mio_dominio  (str): Il nostro dominio da cercare nella pagina (es. "example.com")

    Ritorna:
        list: [tipo_risultato, power_score, anchor_text, note]
              - tipo_risultato : etichetta qualitativa (ECCELLENTE, SCARSO, ecc.)
              - power_score    : punteggio da 0 a 10
              - anchor_text    : testo cliccabile del link
              - note           : info aggiuntive o messaggi di errore
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    try:
        r = requests.get(url_sorgente, headers=headers, timeout=10)

        # Se la pagina non risponde correttamente, la segniamo come offline
        if r.status_code != 200:
            return ["OFFLINE", 0, "N/D", "Errore Connessione"]

        soup = BeautifulSoup(r.text, 'html.parser')

        # --- STEP 1: Cerca il nostro link nella pagina ---
        # Cerca il primo tag <a> il cui attributo href contiene il nostro dominio
        link_tag = soup.find('a', href=lambda h: h and mio_dominio in h)

        if not link_tag:
            # Il link non c'è più: potrebbe essere stato rimosso dopo l'indicizzazione
            return ["RIMOSSO", 0, "N/D", "Link non più presente"]

        # Anchor text = il testo visibile e cliccabile del link
        anchor = link_tag.get_text().strip() or "[Immagine/Vuoto]"

        # --- STEP 2: Valuta la posizione del link nella struttura della pagina ---
        # Un link dentro un articolo o paragrafo vale molto di più di uno nel footer
        parenti = [p.name for p in link_tag.parents]  # Lista dei tag "contenitori" del link

        if 'article' in parenti or 'main' in parenti or 'p' in parenti:
            tipo, score = "⭐️ ECCELLENTE", 10   # Link editoriale nel contenuto: massimo valore SEO
        elif 'footer' in parenti or 'aside' in parenti:
            tipo, score = "🔴 SCARSO", 2         # Link nel footer o sidebar: poco valore SEO
        else:
            tipo, score = "🟡 MEDIO", 5          # Posizione non determinata: valore intermedio

        # --- STEP 3: Controllo rapido per contenuti tossici/spam ---
        # Se la pagina parla di gambling, crypto-spam, contenuti per adulti ecc.,
        # il link è dannoso per la nostra reputazione SEO
        testo_lower = soup.get_text().lower()
        if any(parola in testo_lower for parola in PAROLE_TOSSICHE):
            tipo, score = "💀 TOSSICO", 0        # Link da sito tossico: da disavow su Google

        return [tipo, score, anchor, "Attivo"]

    except Exception as e:
        return ["ERRORE", 0, "N/D", str(e)]


# ==========================================
# 2. ORCHESTRATORE PRINCIPALE
#    Legge il CSV, scansiona tutti i link, salva il risultato
# ==========================================
def genera_csv_backlink():
    """
    Legge il file CSV di Google Search Console, analizza ogni backlink
    e salva i risultati in un nuovo CSV con punteggi e classificazioni.
    """
    try:
        # Carica il file CSV esportato da Google Search Console
        df_input = pd.read_csv(FILE_INPUT)

        # Trova automaticamente la colonna che contiene gli URL
        # (cerca la prima colonna che ha valori che iniziano con "http")
        col_url = next(
            (c for c in df_input.columns if df_input[c].astype(str).str.contains('http').any()),
            None
        )

        if not col_url:
            print("❌ Colonna URL non trovata nel CSV!")
            return

        # Prende tutti gli URL (senza righe vuote)
        urls = df_input[col_url].dropna().tolist()
        totale_link = len(urls)

        risultati = []
        print(f"🚀 Avvio scansione di {totale_link} backlink...")

        for indice, u in enumerate(urls, 1):
            # Analizza il singolo link
            dati = analizza_singolo_link(u, MIO_DOMINIO)

            risultati.append({
                "URL Sorgente" : u,
                "Tipo Risultato": dati[0],
                "Power Score"  : dati[1],
                "Anchor Text"  : dati[2],
                "Note"         : dati[3]
            })

            # Mostra il progresso in tempo reale
            print(f"[{indice}/{totale_link}] {dati[0]} | {u[:50]}")

            # Pausa di 1 secondo tra una richiesta e l'altra
            # Fondamentale per non essere bloccati dai siti sorgente
            time.sleep(1)

        # Salva il CSV finale con encoding UTF-8 con BOM
        # (utf-8-sig garantisce la corretta visualizzazione in Excel su Windows)
        df_finale = pd.DataFrame(risultati)
        df_finale.to_csv(FILE_OUTPUT, index=False, sep=',', encoding='utf-8-sig')

        print(f"\n🏆 FATTO! Analizzati {totale_link} backlink.")
        print(f"💡 Apri '{FILE_OUTPUT}' per vedere il quadro completo.")

    except FileNotFoundError:
        print(f"❌ File non trovato: assicurati che '{FILE_INPUT}' esista nella cartella corretta.")


# ==========================================
# PUNTO DI AVVIO DELLO SCRIPT
# ==========================================
if __name__ == "__main__":
    genera_csv_backlink()