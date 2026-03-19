"""
===============================================================
 CORE WEB VITALS CHECKER - Misurazione performance reale da browser
===============================================================
Cosa fa questo script:
  Apre un browser Chrome reale (in modalità invisibile) e misura
  le prestazioni di caricamento delle pagine del tuo sito,
  simulando un utente su smartphone Android.

  Misura i 3 Core Web Vitals di Google:
    - LCP  (Largest Contentful Paint): quanto tempo ci vuole per
            vedere il contenuto principale della pagina.
            ✅ Buono se < 2.5s
    - CLS  (Cumulative Layout Shift): quanto "si sposta" il contenuto
            mentre la pagina carica (fastidioso per l'utente).
            ✅ Buono se < 0.1
    - TTFB (Time To First Byte): quanto impiega il server a rispondere.
            ✅ Buono se < 800ms

  Testa più pagine in parallelo (homepage, categoria, prodotto)
  e produce un report comparativo in CSV.

Come si usa:
  1. Installa le dipendenze (vedi sotto)
  2. Modifica il dizionario `PAGINE_DA_TESTARE` con i tuoi URL
  3. Lancia: python core_vitals_checker.py

Dipendenze richieste:
  pip install playwright pandas
  playwright install chrome
===============================================================
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd


# ==========================================
# CONFIGURAZIONE - Modifica questi valori
# ==========================================

# Pagine da testare: aggiungi, rimuovi o modifica le voci liberamente
# Formato: "ETICHETTA": "https://www.EXAMPLE_SITE.com/pagina"
PAGINE_DA_TESTARE = {
    "HOMEPAGE"  : "https://www.EXAMPLE_SITE.com/it/",
    "CATEGORIA" : "https://www.EXAMPLE_SITE.com/it/categoria-esempio",
    "PRODOTTO"  : "https://www.EXAMPLE_SITE.com/it/prodotto-esempio.html"
}

FILE_OUTPUT = "report_comparativo_vitals.csv"   # <-- nome del file di output

# Simula uno smartphone Android (come fa Google per valutare il sito in mobile)
VIEWPORT_MOBILE = {'width': 390, 'height': 844}
USER_AGENT_MOBILE = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/116.0.0.0 Mobile Safari/537.36"
)


# ==========================================
# 1. ANALISI CORE WEB VITALS DI UNA SINGOLA PAGINA
#    Apre la pagina nel browser e raccoglie le metriche tramite
#    le API JavaScript native del browser (PerformanceObserver)
# ==========================================
async def analizza_core_vitals(context, url, etichetta):
    """
    Apre una pagina nel browser e misura i Core Web Vitals.

    Usa le API native del browser (PerformanceObserver) per raccogliere
    metriche reali, esattamente come farebbe Chrome DevTools.

    Parametri:
        context   : il contesto browser di Playwright (simula il dispositivo)
        url       (str): URL della pagina da misurare
        etichetta (str): nome descrittivo della pagina (es. "HOMEPAGE")

    Ritorna:
        dict: Dizionario con etichetta, URL e valori LCP, CLS, TTFB
              oppure un messaggio di errore se la pagina non risponde
    """
    print(f"🚀 Analisi {etichetta}: {url}")
    page = await context.new_page()

    try:
        # Carica la pagina e aspetta il completamento del caricamento
        await page.goto(url, wait_until="load", timeout=60000)

        # Esegue JavaScript direttamente nel browser per raccogliere le metriche
        # PerformanceObserver è un'API nativa del browser, non richiede librerie esterne
        vitals = await page.evaluate('''() => {
            return new Promise((resolve) => {
                let lcp = 0;   // Largest Contentful Paint
                let cls = 0;   // Cumulative Layout Shift

                // Osserva il momento in cui il contenuto principale appare a schermo
                new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    lcp = entries[entries.length - 1].startTime;
                }).observe({type: 'largest-contentful-paint', buffered: true});

                // Osserva ogni spostamento di elementi durante il caricamento
                new PerformanceObserver((entryList) => {
                    for (const entry of entryList.getEntries()) {
                        // hadRecentInput = true significa che lo shift è causato
                        // da un'azione dell'utente (accettabile), quindi lo escludiamo
                        if (!entry.hadRecentInput) {
                            cls += entry.value;
                        }
                    }
                }).observe({type: 'layout-shift', buffered: true});

                // Aspetta 2 secondi per raccogliere tutti gli eventi, poi restituisce i dati
                setTimeout(() => {
                    resolve({
                        lcp : Math.round(lcp) / 1000,
                        cls : Math.round(cls * 1000) / 1000,
                        ttfb: Math.round(
                            performance.getEntriesByType('navigation')[0].responseStart
                        )
                    });
                }, 2000);
            });
        }''')

        await page.close()

        # Giudizio automatico basato sulle soglie ufficiali Google:
        # LCP <= 2.5s = Buono, LCP > 2.5s = Da migliorare
        giudizio = "✅ BUONO" if vitals['lcp'] <= 2.5 else "🔴 DA MIGLIORARE"

        return {
            "Tipo"     : etichetta,
            "URL"      : url,
            "TTFB"     : f"{vitals['ttfb']}ms",
            "LCP"      : f"{vitals['lcp']}s",
            "CLS"      : vitals['cls'],
            "Giudizio" : giudizio
        }

    except Exception as e:
        await page.close()
        return {"Tipo": etichetta, "URL": url, "Errore": str(e)}


# ==========================================
# 2. ORCHESTRATORE PRINCIPALE (async)
#    Lancia il browser, testa tutte le pagine e salva il report
# ==========================================
async def main():
    """
    Avvia il browser Chrome in modalità headless (invisibile),
    simula un dispositivo mobile e testa tutte le pagine configurate.
    Salva i risultati in un CSV e li stampa a schermo.
    """
    async with async_playwright() as p:

        # Lancia Chrome in modalità "headless" = invisibile, senza aprire finestre
        browser = await p.chromium.launch(channel="chrome", headless=True)

        # Crea un contesto che simula uno smartphone Android
        context = await browser.new_context(
            viewport   = VIEWPORT_MOBILE,
            user_agent = USER_AGENT_MOBILE
        )

        risultati = []

        # Analizza ogni pagina configurata in PAGINE_DA_TESTARE
        for etichetta, url in PAGINE_DA_TESTARE.items():
            res = await analizza_core_vitals(context, url, etichetta)
            risultati.append(res)

        await browser.close()

        # --- REPORT A SCHERMO ---
        df = pd.DataFrame(risultati)
        print("\n" + "=" * 55)
        print("📊 REPORT COMPARATIVO CORE WEB VITALS")
        print("=" * 55)

        # Mostra la tabella senza la colonna URL (troppo lunga per il terminale)
        colonne_da_mostrare = [c for c in df.columns if c != 'URL']
        print(df[colonne_da_mostrare].to_string(index=False))

        # --- SALVATAGGIO CSV ---
        df.to_csv(FILE_OUTPUT, index=False, encoding='utf-8')
        print(f"\n💾 Report salvato in '{FILE_OUTPUT}'")


# ==========================================
# PUNTO DI AVVIO DELLO SCRIPT
# ==========================================
if __name__ == "__main__":
    asyncio.run(main())