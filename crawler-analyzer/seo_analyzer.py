"""
===============================================================
 SEO AUDIT REPORT - Analisi problemi tecnici di un sito web
===============================================================
Cosa fa questo script:
  Legge un file CSV esportato da uno strumento di SEO audit
  (es. Screaming Frog, Sitebulb, ecc.) e produce un report
  testuale con tutti i problemi trovati, suddivisi per categoria.

  Alla fine genera un secondo file CSV con solo le pagine
  che hanno le urgenze più critiche da sistemare subito.

Come si usa:
  1. Esporta il tuo audit SEO in formato CSV
  2. Metti il file CSV nella stessa cartella di questo script
  3. Cambia il nome del file nella riga in fondo (main)
  4. Lancia lo script: python seo_audit_report.py

Dipendenze richieste:
  pip install pandas numpy
===============================================================
"""

import pandas as pd
import numpy as np


def genera_report_problemi(file_csv):
    """
    Analizza un file CSV di audit SEO e stampa un report dei problemi trovati.

    Parametri:
        file_csv (str): Il percorso al file CSV da analizzare.
                        Es. "audit_sito.csv"

    Output:
        - Stampa a schermo un riepilogo dei problemi per categoria
        - Salva un file CSV con le sole pagine critiche da correggere
    """
    try:
        # --- CARICAMENTO DEL FILE ---
        # Legge il file CSV e lo carica in una "tabella" (DataFrame)
        df = pd.read_csv(file_csv)
        totale = len(df)  # Numero totale di URL analizzati

        print(f"\n📊 --- REPORT SEO AUDIT: {totale} URL ANALIZZATI ---")

        # --- FUNZIONE HELPER: RILEVA VALORI MANCANTI ---
        # Considera "mancante" un campo se contiene:
        #   - La stringa letterale 'Mancante'
        #   - Una cella vuota (NaN)
        #   - Una stringa fatta solo di spazi
        def is_missing(series):
            return (
                (series == 'Mancante') |
                (series.isna()) |
                (series.astype(str).str.strip() == '')
            )

        # -----------------------------------------------
        # CONTROLLO 1: ERRORI DI ACCESSO (Status HTTP)
        # -----------------------------------------------
        # Lo status 200 = pagina ok. Qualsiasi altro codice (404, 500...) è un errore.
        if 'Status' in df.columns:
            df['Status'] = pd.to_numeric(df['Status'], errors='coerce')  # Converte in numero
            errori_status = df[df['Status'] != 200]
            print(f"❌ PAGINE ROTTE (404/500): {len(errori_status)}")

        # -----------------------------------------------
        # CONTROLLO 2: TAG TITLE (il titolo della pagina nei risultati Google)
        # -----------------------------------------------
        if 'Title' in df.columns:
            mancanti_title = df[is_missing(df['Title'])]
            print(f"⚠️  Title mancanti o vuoti: {len(mancanti_title)}")

            if 'Lung. Title' in df.columns:
                # Google mostra meglio i titoli tra 30 e 60 caratteri
                title_short = df[(df['Lung. Title'] > 0) & (df['Lung. Title'] < 30)]
                title_long  = df[df['Lung. Title'] > 60]
                print(f"⚠️  Title troppo corti  (< 30 caratteri): {len(title_short)}")
                print(f"⚠️  Title troppo lunghi (> 60 caratteri): {len(title_long)}")

        # -----------------------------------------------
        # CONTROLLO 3: META DESCRIPTION (il testo descrittivo sotto il titolo su Google)
        # -----------------------------------------------
        if 'Meta Desc' in df.columns:
            mancanti_desc = df[is_missing(df['Meta Desc'])]
            print(f"⚠️  Meta Description mancanti: {len(mancanti_desc)}")

        # -----------------------------------------------
        # CONTROLLO 4: TAG H1 (il titolo principale visibile sulla pagina)
        # -----------------------------------------------
        if 'H1' in df.columns:
            mancanti_h1 = df[is_missing(df['H1'])]
            print(f"⚠️  Pagine senza H1: {len(mancanti_h1)}")

        # -----------------------------------------------
        # CONTROLLO 5: IMMAGINI SENZA TESTO ALT
        # Il testo ALT descrive le immagini ai motori di ricerca e agli screen reader
        # -----------------------------------------------
        if 'Img senza ALT' in df.columns:
            img_critiche = df[df['Img senza ALT'] > 0]
            print(f"🖼️  Pagine con immagini senza ALT text: {len(img_critiche)}")

        # -----------------------------------------------
        # CONTROLLO 6: VELOCITÀ DI CARICAMENTO
        # Pagine lente penalizzano il posizionamento su Google
        # -----------------------------------------------
        if 'Tempo (sec)' in df.columns:
            lente = df[df['Tempo (sec)'] > 2.0]
            print(f"🐢 Pagine lente (caricamento > 2 secondi): {len(lente)}")

        # -----------------------------------------------
        # CONTROLLO 7: DIRETTIVA NOINDEX
        # Una pagina con "noindex" viene esclusa dai risultati di Google
        # -----------------------------------------------
        if 'Robots' in df.columns:
            no_index = df[df['Robots'].fillna('').str.contains('noindex', case=False)]
            print(f"🚫 Pagine escluse da Google (NoIndex): {len(no_index)}")

        # -----------------------------------------------
        # CONTROLLO 8: TITLE DUPLICATI (cannibalizzazione SEO)
        # Più pagine con lo stesso titolo confondono Google su quale indicizzare
        # -----------------------------------------------
        if 'Title' in df.columns:
            duplicati = df[df['Title'].duplicated() & (df['Title'] != 'Mancante')]
            print(f"👯 Title duplicati (stesso titolo su pagine diverse): {len(duplicati)}")

        # -----------------------------------------------
        # GENERAZIONE FILE PRIORITÀ
        # Raccoglie in un unico CSV le pagine con i problemi più gravi:
        # errori HTTP, titolo mancante, H1 mancante
        # -----------------------------------------------
        filtro_urgenze = pd.Series([False] * totale)  # Parte con tutto "falso" (nessun problema)

        if 'Status' in df.columns: filtro_urgenze |= (df['Status'] != 200)
        if 'Title'  in df.columns: filtro_urgenze |= is_missing(df['Title'])
        if 'H1'     in df.columns: filtro_urgenze |= is_missing(df['H1'])

        pagine_da_sistemare = df[filtro_urgenze]

        if not pagine_da_sistemare.empty:
            # Salva il file con le sole pagine critiche
            pagine_da_sistemare.to_csv("pagine_prioritarie_da_sistemare.csv", index=False)
            print(f"\n✅ GENERATO: 'pagine_prioritarie_da_sistemare.csv'")
            print(f"👉 Totale urgenze da sistemare: {len(pagine_da_sistemare)}")
        else:
            print("\n✅ Tutto pulito! Nessuna urgenza trovata.")

    except Exception as e:
        # Se qualcosa va storto (es. file non trovato, colonne diverse) mostra l'errore
        print(f"❌ Errore durante l'analisi: {e}")


# -----------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# -----------------------------------------------
# Questa parte viene eseguita solo quando lanci direttamente questo file.
# Cambia "super_audit_tecnico.csv" con il nome del tuo file CSV.
if __name__ == "__main__":
    genera_report_problemi("super_audit_tecnico.csv")
