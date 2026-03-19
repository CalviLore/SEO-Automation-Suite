"""
===============================================================
 KEYWORD LONG-TAIL EXTRACTOR - Estrazione suggerimenti da Google
===============================================================
Cosa fa questo script:
  Sfrutta l'API pubblica dei suggerimenti di Google (la stessa
  usata dalla barra di ricerca quando scrivi) per estrarre
  centinaia di keyword a "coda lunga" (long-tail) partendo
  da una sola parola chiave di partenza.

  Tecnica usata: "Alphabet Soup" (Zuppa di Lettere)
    → Cerca la parola base + ogni lettera dell'alfabeto (a, b, c...)
    → Google restituisce i suggerimenti più cercati per ogni combo
    → Il risultato è una lista di keyword reali e ricercate

  Esempio:
    Parola base: "scarpe antinfortunistiche"
    → "scarpe antinfortunistiche amazon"
    → "scarpe antinfortunistiche basse"
    → "scarpe antinfortunistiche con punta in acciaio"
    → ... e così via per tutte le lettere

Come si usa:
  1. Cambia la variabile `SEED_KEYWORD` con la tua parola chiave
  2. Lancia: python keyword_extractor.py
  3. Trovi il CSV nella stessa cartella con tutte le keyword trovate

Dipendenze richieste:
  pip install requests pandas
===============================================================
"""

import requests
import json
import pandas as pd
import time
import string


# ==========================================
# CONFIGURAZIONE - Modifica questi valori
# ==========================================
SEED_KEYWORD = "scarpe antinfortunistiche"   # <-- inserisci la tua parola chiave di partenza
LINGUA       = "it"                          # <-- lingua dei suggerimenti Google (it, en, fr, de...)


# ==========================================
# URL dell'API pubblica dei suggerimenti Google
# Non richiede autenticazione né API key
# ==========================================
GOOGLE_SUGGEST_URL = "http://suggestqueries.google.com/complete/search"


# ==========================================
# 1. ESTRAZIONE KEYWORD LONG-TAIL
#    Tecnica: ricerca base + Alphabet Soup
# ==========================================
def trova_keyword_long_tail(parola_base):
    """
    Estrae keyword a coda lunga dai suggerimenti automatici di Google.

    Strategia in 2 fasi:
      Fase 1 - Ricerca base: interroga Google con la sola parola chiave
      Fase 2 - Alphabet Soup: ripete la ricerca aggiungendo ogni lettera
               dell'alfabeto per ottenere suggerimenti più specifici

    Parametri:
        parola_base (str): La keyword di partenza (es. "scarpe antinfortunistiche")

    Ritorna:
        list: Lista di keyword uniche trovate (senza duplicati)
    """
    print(f"🎯 Estrazione suggerimenti Google per: '{parola_base}'...")

    # Usiamo un 'set' (insieme) invece di una lista:
    # i set eliminano automaticamente i duplicati
    keywords_trovate = set()

    # --- FASE 1: Ricerca base ---
    # Interroga Google con la sola parola chiave, senza aggiunte
    params_base = {'client': 'chrome', 'q': parola_base, 'hl': LINGUA}
    try:
        risposta    = requests.get(GOOGLE_SUGGEST_URL, params=params_base)
        suggerimenti = json.loads(risposta.text)[1]  # I suggerimenti sono nel secondo elemento JSON
        for sug in suggerimenti:
            keywords_trovate.add(sug)
    except Exception as e:
        print(f"⚠️  Errore nella ricerca base: {e}")

    # --- FASE 2: Alphabet Soup ---
    # Per ogni lettera dell'alfabeto, cerca "[parola base] [lettera]"
    # Es: "scarpe a", "scarpe b", "scarpe c"...
    # Google restituisce le query più cercate che iniziano con quella combinazione
    alfabeto = list(string.ascii_lowercase)

    print("🔠 Alphabet Soup in corso (26 lettere)...")

    for lettera in alfabeto:
        params_avanzati = {
            'client': 'chrome',
            'q'     : f"{parola_base} {lettera}",   # Es: "scarpe antinfortunistiche a"
            'hl'    : LINGUA
        }
        try:
            risposta     = requests.get(GOOGLE_SUGGEST_URL, params=params_avanzati)
            suggerimenti = json.loads(risposta.text)[1]
            for sug in suggerimenti:
                keywords_trovate.add(sug)
        except:
            pass  # Se una lettera fallisce, continuiamo con la prossima

        # Stampa un punto per ogni lettera elaborata: feedback visivo di avanzamento
        print(".", end="", flush=True)

        # Pausa tra una richiesta e l'altra per non essere bloccati da Google
        time.sleep(0.5)

    print()  # Va a capo dopo i puntini
    return list(keywords_trovate)


# ==========================================
# PUNTO DI AVVIO DELLO SCRIPT
# ==========================================
if __name__ == "__main__":

    # Avvia l'estrazione con la keyword configurata in cima
    risultati = trova_keyword_long_tail(SEED_KEYWORD)

    print(f"\n🔥 Trovate {len(risultati)} keyword a coda lunga per '{SEED_KEYWORD}'")

    # Organizza i risultati in un DataFrame e li ordina alfabeticamente
    df = pd.DataFrame(risultati, columns=["Keyword"])
    df = df.sort_values(by="Keyword").reset_index(drop=True)

    # Nome del file basato sulla keyword (gli spazi diventano underscore)
    nome_file = f"keyword_longtail_{SEED_KEYWORD.replace(' ', '_')}.csv"
    df.to_csv(nome_file, index=False, encoding='utf-8')

    print(f"🏆 File salvato: '{nome_file}'")
    print(f"\n💡 Anteprima delle prime 30 keyword trovate:")
    for kw in risultati[:30]:
        print(f"  👉 {kw}")
