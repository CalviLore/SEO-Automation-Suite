"""
===============================================================
 SEO CRAWLER & AUDIT - Scansione sitemap e analisi tecnica SEO
===============================================================
Cosa fa questo script:
  Parte dalla sitemap principale di un sito (file XML) e
  naviga in profondità tutte le sotto-sitemap trovate,
  raccogliendo ogni URL della pagina.

  Per ogni URL trovato esegue un audit SEO tecnico: controlla
  title, meta description, H1, immagini senza ALT, canonical,
  direttive robots e status HTTP.

  Il risultato viene salvato in un file CSV pronto per essere
  analizzato con lo script seo_audit_report.py

Come si usa:
  1. Cambia la variabile `MIA_SITEMAP` con l'URL della tua sitemap
  2. (Opzionale) Cambia `NOME_FILE_OUTPUT` con il nome che vuoi dare al CSV
  3. Lancia: python seo_crawler_audit.py

Compatibile con:
  Siti PrestaShop e qualsiasi CMS che esponga una sitemap XML standard.

Dipendenze richieste:
  pip install requests beautifulsoup4 pandas lxml
===============================================================
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random


# ==========================================
# CONFIGURAZIONE - Modifica questi valori
# ==========================================
MIA_SITEMAP    = "https://www.EXAMPLE_SITE.com/1_index_sitemap.xml"  # <-- inserisci la tua sitemap
NOME_FILE_OUTPUT = "super_audit_tecnico.csv"                          # <-- nome del file di output


# ==========================================
# 1. ESTRAZIONE TOTALE DEGLI URL DALLA SITEMAP
#    Strategia: "Forza Bruta" con timeout generoso (60s)
#    Gestisce sitemap annidate (sitemap che puntano ad altre sitemap)
# ==========================================
def estrai_tutti_gli_url_completo(sitemap_iniziale):
    """
    Parte da una sitemap XML e raccoglie TUTTI gli URL del sito,
    navigando ricorsivamente anche le sotto-sitemap.

    Parametri:
        sitemap_iniziale (str): URL della sitemap principale (es. sitemap_index.xml)

    Ritorna:
        list: Lista di tutti gli URL delle pagine trovate
    """
    print(f"🔍 Avvio estrazione profonda da: {sitemap_iniziale}")

    # Intestazione HTTP per simulare un browser normale ed evitare blocchi
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    sitemap_da_visitare = [sitemap_iniziale]  # Coda di sitemap ancora da leggere
    sitemap_visitate    = set()               # Sitemap già elaborate (evita loop)
    pagine_finali       = set()               # URL delle pagine reali del sito

    # Continua finché ci sono sitemap in coda da visitare
    while sitemap_da_visitare:
        url_corrente = sitemap_da_visitare.pop(0)  # Prende il primo elemento della coda

        # Se l'abbiamo già visitata, salta
        if url_corrente in sitemap_visitate:
            continue
        sitemap_visitate.add(url_corrente)

        print(f"📂 Scansiono: {url_corrente} [Coda: {len(sitemap_da_visitare)}]")

        try:
            # Timeout alto (60s) per gestire sitemap molto grandi o server lenti
            risposta = requests.get(url_corrente, headers=headers, timeout=60)

            if risposta.status_code == 200:
                # Parsing del file XML con BeautifulSoup
                soup  = BeautifulSoup(risposta.text, 'xml')
                links = [tag.text.strip() for tag in soup.find_all('loc')]

                for link in links:
                    if '.xml' in link.lower():
                        # È una sotto-sitemap: la aggiungiamo alla coda da visitare
                        if link not in sitemap_visitate:
                            sitemap_da_visitare.append(link)
                    else:
                        # È una pagina reale: la aggiungiamo al risultato finale
                        pagine_finali.add(link)

            time.sleep(0.5)  # Pausa tra una richiesta e l'altra per non sovraccaricare il server

        except Exception as e:
            print(f"  ❌ Errore/Timeout su {url_corrente}: {e}")

    print(f"✅ ESTRAZIONE CONCLUSA! Trovati {len(pagine_finali)} URL totali.")
    return list(pagine_finali)


# ==========================================
# 2. CATEGORIZZAZIONE URL (logica PrestaShop)
#    Determina il "tipo" di pagina in base alla struttura dell'URL
# ==========================================
def categorizza_url_prestashop(url):
    """
    Classifica un URL in base alla sua struttura tipica di PrestaShop.

    Parametri:
        url (str): L'URL da classificare

    Ritorna:
        str: Una delle categorie: 'Pagina (CMS)', 'Prodotto', 'Homepage', 'Categoria'
    """
    u = url.lower()

    if '/content/' in u:
        return 'Pagina (CMS)'          # Pagine statiche create nel CMS
    elif u.endswith('.html'):
        return 'Prodotto'              # I prodotti in PrestaShop finiscono con .html
    elif u.endswith(('.it/', '.it/it/')) or u.count('/') < 4:
        return 'Homepage'              # URL molto corti = homepage o radice del sito
    else:
        return 'Categoria'             # Tutto il resto è trattato come categoria


# ==========================================
# 3. AUDIT SEO DI UNA SINGOLA PAGINA
#    Scarica la pagina e ne estrae tutti i dati SEO rilevanti
# ==========================================
def analizza_pagina_seo(url):
    """
    Visita un URL e raccoglie i dati SEO tecnici della pagina.

    Parametri:
        url (str): L'URL della pagina da analizzare

    Ritorna:
        dict: Dizionario con tutti i dati SEO, oppure None se la pagina
              non è HTML (es. immagini, PDF) o se si verifica un errore
    """
    headers  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    categoria = categorizza_url_prestashop(url)

    try:
        # stream=True scarica prima solo gli header HTTP, senza scaricare tutto il corpo.
        # Serve per controllare il Content-Type prima di scaricare pagine inutili (immagini, PDF...)
        risposta = requests.get(url, headers=headers, timeout=20, stream=True)

        content_type = risposta.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            return None  # Non è una pagina HTML: saltiamo (es. jpg, pdf, zip...)

        # È HTML: ora scarichiamo e facciamo il parsing completo
        soup = BeautifulSoup(risposta.text, 'html.parser')

        # --- Tag Title (titolo della pagina nei risultati Google) ---
        title = soup.title.string.strip() if soup.title and soup.title.string else 'Mancante'

        # --- Meta Description (testo descrittivo sotto il titolo su Google) ---
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc['content'].strip() if meta_desc and meta_desc.has_attr('content') else 'Mancante'

        # --- URL Canonical (indica a Google qual è la versione "ufficiale" della pagina) ---
        can_tag   = soup.find('link', rel='canonical')
        canonical = can_tag['href'] if can_tag else 'Mancante'

        # --- Direttiva Robots (dice a Google se indicizzare o meno la pagina) ---
        rob_tag = soup.find('meta', attrs={'name': 'robots'})
        robots  = rob_tag['content'] if rob_tag else 'index, follow'  # Default: tutto indicizzabile

        # --- Struttura dei titoli nella pagina ---
        h1       = soup.find('h1').text.strip() if soup.find('h1') else 'Mancante'
        h2_count = len(soup.find_all('h2'))  # Numero di sottotitoli H2

        # --- Analisi immagini: quante sono senza testo ALT ---
        # Il testo ALT è fondamentale per l'accessibilità e per la SEO delle immagini
        immagini      = soup.find_all('img')
        img_totali    = len(immagini)
        img_senza_alt = len([
            img for img in immagini
            if not img.get('alt') or img.get('alt').strip() == ""
        ])

        # Restituisce un dizionario con tutti i dati raccolti per questa pagina
        return {
            'URL'          : url,
            'Tipo'         : categoria,
            'Status'       : risposta.status_code,
            'Robots'       : robots,
            'Canonical'    : canonical,
            'Title'        : title,
            'Lung. Title'  : len(title) if title != 'Mancante' else 0,
            'Meta Desc'    : desc,
            'H1'           : h1,
            'H2 Totali'    : h2_count,
            'Img Totali'   : img_totali,
            'Img senza ALT': img_senza_alt
        }

    except:
        return None  # In caso di errore (timeout, connessione rifiutata, ecc.) ignora la pagina


# ==========================================
# PUNTO DI AVVIO DELLO SCRIPT
# ==========================================
if __name__ == "__main__":

    # FASE 1: Estrai tutti gli URL dalla sitemap
    urls = estrai_tutti_gli_url_completo(MIA_SITEMAP)

    risultati = []

    if urls:
        print(f"\n⚙️  Audit di {len(urls)} potenziali pagine...")

        for i, url in enumerate(urls, 1):
            dati = analizza_pagina_seo(url)

            if dati:  # Aggiunge il risultato solo se la pagina era HTML valida
                risultati.append(dati)
                print(f"[{i}/{len(urls)}] ✅ {url}")

            # --- SALVATAGGIO INTERMEDIO ogni 100 pagine ---
            # Protezione contro crash o interruzioni: i dati vengono salvati
            # progressivamente, così non si perde tutto in caso di errore
            if i % 100 == 0 and risultati:
                pd.DataFrame(risultati).to_csv(NOME_FILE_OUTPUT, index=False, encoding='utf-8')
                print(f"💾 Salvataggio intermedio effettuato ({i} URL processati).")

            time.sleep(0.1)  # Piccola pausa per non sovraccaricare il server target

        # FASE FINALE: salva il CSV completo con tutti i risultati
        pd.DataFrame(risultati).to_csv(NOME_FILE_OUTPUT, index=False, encoding='utf-8')
        print(f"\n🎉 Audit completato! Report salvato in: {NOME_FILE_OUTPUT}")
