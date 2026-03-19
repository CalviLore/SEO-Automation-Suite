"""
===============================================================
 STRUCTURED DATA & PRICE CHECKER - Verifica prezzi e schema.org
===============================================================
Cosa fa questo script:
  Legge il CSV prodotto da seo_crawler_audit.py, filtra solo le
  pagine prodotto (quelle che finiscono in .html) e per ognuna
  verifica se i "Dati Strutturati" sono presenti e corretti.

  I Dati Strutturati (schema.org) sono informazioni nascoste nel
  codice HTML che Google usa per mostrare prezzi, disponibilità
  e stelle di valutazione direttamente nei risultati di ricerca
  (i cosiddetti "Rich Snippet").

  Per ogni prodotto controlla:
    - Se esiste il blocco JSON-LD di tipo "Product"
    - Il prezzo dichiarato nel codice
    - La valuta (EUR, USD, ecc.)
    - La disponibilità (In stock / Esaurito / Non specificata)

Come si usa:
  1. Assicurati di avere già eseguito seo_crawler_audit.py
     e di avere il file "super_audit_tecnico.csv" nella cartella
  2. Lancia: python structured_data_checker.py
  3. Trovi il report in "audit_prezzi_COMPLETO.csv"

Dipendenze richieste:
  pip install pandas requests beautifulsoup4
===============================================================
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time


# ==========================================
# CONFIGURAZIONE - Modifica questi valori
# ==========================================
FILE_INPUT  = "super_audit_tecnico.csv"     # <-- CSV generato da seo_crawler_audit.py
FILE_OUTPUT = "audit_prezzi_COMPLETO.csv"   # <-- nome del file di report finale


# ==========================================
# 1. VERIFICA DATI STRUTTURATI DI UNA SINGOLA PAGINA
#    Legge il codice HTML e cerca il blocco JSON-LD "Product"
# ==========================================
def verifica_dati_strutturati(url):
    """
    Visita una pagina prodotto e ne estrae i Dati Strutturati (schema.org).

    I Dati Strutturati sono blocchi JSON nascosti nell'HTML con tag:
      <script type="application/ld+json"> ... </script>
    Google li legge per mostrare prezzi e disponibilità nei risultati.

    Parametri:
        url (str): URL della pagina prodotto da analizzare

    Ritorna:
        dict: Dizionario con URL, presenza del prodotto, prezzo, valuta
              e disponibilità. In caso di errore, include il messaggio.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36',
        'Accept'    : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        # Se la pagina non risponde correttamente, restituisce un errore
        if response.status_code != 200:
            return {
                "URL"              : url,
                "Prodotto Trovato" : "❌ NO",
                "Prezzo"           : "Errore HTTP",
                "Disponibilità"    : "N/D"
            }

        soup = BeautifulSoup(response.text, 'html.parser')

        # Cerca tutti i blocchi di dati strutturati nella pagina
        # Sono tag <script type="application/ld+json"> che contengono JSON
        scripts = soup.find_all('script', type='application/ld+json')

        # Struttura di risultato di default (nel caso non troviamo nulla)
        risultato = {
            "URL"              : url,
            "Prodotto Trovato" : "❌ NO",
            "Prezzo"           : "N/D",
            "Valuta"           : "N/D",
            "Disponibilità"    : "N/D"
        }

        # Esamina ogni blocco JSON trovato nella pagina
        for script in scripts:
            try:
                dati  = json.loads(script.string)

                # Un blocco può contenere un singolo oggetto o una lista di oggetti
                items = dati if isinstance(dati, list) else [dati]

                for item in items:
                    # Cerca il tipo "Product" (schema.org/Product)
                    if item.get('@type') == 'Product' or 'Product' in str(item.get('@type')):
                        risultato["Prodotto Trovato"] = "✅ SI"

                        # Le offerte (prezzo, valuta, disponibilità) stanno nel campo "offers"
                        offers = item.get('offers', {})
                        if isinstance(offers, list):
                            offers = offers[0]  # Se ci sono più offerte, prende la prima

                        risultato["Prezzo"]  = offers.get('price', "Mancante")
                        risultato["Valuta"]  = offers.get('priceCurrency', "Mancante")

                        # La disponibilità è un URL schema.org, es:
                        # "https://schema.org/InStock" o "https://schema.org/OutOfStock"
                        disp = offers.get('availability', '')
                        if 'InStock' in disp:
                            risultato["Disponibilità"] = "🟢 Disponibile"
                        elif 'OutOfStock' in disp:
                            risultato["Disponibilità"] = "🔴 Esaurito"
                        else:
                            risultato["Disponibilità"] = "⚠️ Non specificata"

            except:
                continue  # Se un blocco JSON è malformato, lo salta e va avanti

        return risultato

    except Exception as e:
        return {"URL": url, "Prodotto Trovato": "Errore", "Errore": str(e)}


# ==========================================
# 2. ORCHESTRATORE PRINCIPALE
#    Filtra i prodotti dal CSV e avvia la verifica su ognuno
# ==========================================
def avvia_controllo_prezzi_da_audit():
    """
    Carica il CSV dell'audit SEO, estrae le pagine prodotto e
    avvia la verifica dei dati strutturati per ognuna.

    Input atteso:
        FILE_INPUT: CSV con almeno una colonna 'URL' e pagine
                    prodotto identificabili dall'estensione .html

    Output:
        FILE_OUTPUT: CSV con il report completo di prezzi e disponibilità
    """
    print(f"📂 Caricamento dati da '{FILE_INPUT}'...")

    try:
        # Carica il CSV generato da seo_crawler_audit.py
        df = pd.read_csv(FILE_INPUT)

        # Filtra solo le URL che finiscono in .html
        # In PrestaShop (e molti altri CMS) le pagine prodotto hanno questo formato
        prodotti_df   = df[df['URL'].astype(str).str.endswith('.html', na=False)]
        urls_prodotti = prodotti_df['URL'].tolist()

        totale_prodotti = len(urls_prodotti)
        print(f"🎯 Trovati {totale_prodotti} prodotti da verificare.")
        print(f"🚀 Avvio scansione su {totale_prodotti} prodotti...\n")

        report = []

        for i, link in enumerate(urls_prodotti, 1):
            dati = verifica_dati_strutturati(link)
            report.append(dati)

            # Mostra il progresso in tempo reale con prezzo e disponibilità
            prezzo = dati.get('Prezzo', 'N/D')
            disp   = dati.get('Disponibilità', 'N/D')
            print(f"[{i}/{totale_prodotti}] {prezzo}€ | {disp} → {link.split('/')[-1]}")

            # Pausa tra una richiesta e l'altra per non sovraccaricare il server
            time.sleep(1)

        # Salva il report finale
        df_finale = pd.DataFrame(report)
        df_finale.to_csv(FILE_OUTPUT, index=False, encoding='utf-8')
        print(f"\n🏆 FATTO! Report salvato in '{FILE_OUTPUT}'")

    except FileNotFoundError:
        print(f"❌ File non trovato: '{FILE_INPUT}'. Hai già eseguito seo_crawler_audit.py?")
    except KeyError:
        print("❌ Colonna 'URL' non trovata nel CSV. Controlla il nome delle colonne.")


# ==========================================
# PUNTO DI AVVIO DELLO SCRIPT
# ==========================================
if __name__ == "__main__":
    avvia_controllo_prezzi_da_audit()
