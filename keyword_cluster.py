"""
===============================================================
 ML KEYWORD CLUSTERING - Analisi Semantica con Scikit-Learn
===============================================================
Cosa fa questo script:
 Legge un file CSV contenente una lista di keyword grezze 
 (estratte in precedenza tramite API o scraping) e utilizza 
 tecniche di NLP per raggrupparle in cluster semantici basati 
 sull'intento di ricerca.
 
 Utilizza:
 - Pandas: per la manipolazione del dataset.
 - TF-IDF (Term Frequency-Inverse Document Frequency): per 
   vettorizzare il testo testuale in matrici matematiche.
 - K-Means: algoritmo di Machine Learning non supervisionato 
   per calcolare le distanze semantiche e creare i raggruppamenti.

 Business Value:
 Trasforma migliaia di keyword disordinate in "Silos SEO" o 
 architetture per campagne Ads in pochi secondi, automatizzando
 l'analisi esplorativa del testo.

Come si usa:
 1. Assicurati di avere un file CSV con una colonna "Keyword".
 2. Modifica la variabile `FILE_INPUT` con il nome del tuo CSV.
 3. Imposta `NUM_CLUSTER` in base a quanti gruppi vuoi ottenere.
 4. Lancia: python nlp_keyword_cluster.py

Dipendenze richieste:
 pip install pandas scikit-learn numpy
===============================================================
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import warnings

# Disabilita i warning di libreria per mantenere l'output pulito
warnings.filterwarnings("ignore")

def esegui_clustering(file_csv, numero_cluster=5):
    print(f"📂 Caricamento dataset da: '{file_csv}'...")
    
    # 1. Data Ingestion: Lettura dati con Pandas
    try:
        df = pd.read_csv(file_csv)
        if 'Keyword' not in df.columns:
            print("❌ Errore: Il file CSV deve contenere una colonna chiamata 'Keyword'.")
            return
        lista_keyword = df['Keyword'].dropna().tolist()
    except FileNotFoundError:
        print(f"❌ Errore: File '{file_csv}' non trovato. Controlla il nome.")
        return

    # Sicurezza: evita di chiedere troppi cluster se il dataset è piccolo
    numero_cluster = min(numero_cluster, len(lista_keyword) // 3)
    if numero_cluster < 2:
        numero_cluster = 2

    print(f"🤖 Avvio Modello ML K-Means: Raggruppamento di {len(lista_keyword)} keyword in {numero_cluster} cluster...")
    
    # 2. NLP Vectorization (Trasforma le parole in pesi matematici TF-IDF)
    vectorizer = TfidfVectorizer(stop_words=None, ngram_range=(1, 2))
    X = vectorizer.fit_transform(lista_keyword)
    
    # 3. Addestramento del Modello K-Means (Unsupervised Learning)
    print("🧠 Calcolo delle distanze semantiche in corso...")
    modello_kmeans = KMeans(n_clusters=numero_cluster, random_state=42, n_init=10)
    modello_kmeans.fit(X)
    
    # Salviamo i risultati nel DataFrame originale
    df['Cluster_ID'] = modello_kmeans.labels_
    
    # 4. Feature Extraction: Diamo un nome umano a ogni cluster
    termini_importanti = vectorizer.get_feature_names_out()
    centroidi = modello_kmeans.cluster_centers_.argsort()[:, ::-1]
    
    nomi_cluster = {}
    for i in range(numero_cluster):
        # Prende le prime 2 parole più forti per nominare il gruppo
        top_words = [termini_importanti[ind] for ind in centroidi[i, :2]]
        nomi_cluster[i] = " - ".join(top_words).upper()
        
    df['Tema_Semantico'] = df['Cluster_ID'].map(nomi_cluster)
    
    # Riordiniamo il DataFrame per una lettura logica
    df = df.sort_values(by=['Tema_Semantico', 'Keyword']).reset_index(drop=True)
    
    # 5. Data Export: Salvataggio del nuovo Dataset arricchito
    nome_file_output = file_csv.replace(".csv", "_CLUSTERED.csv")
    df.to_csv(nome_file_output, index=False)
    
    print(f"\n🏆 Elaborazione completata! File salvato: {nome_file_output}")
    
    # 6. Anteprima dei risultati (utile per presentazioni e log)
    print("\n📊 ANTEPRIMA DEI CLUSTER GENERATI:")
    for cluster_nome, dati in df.groupby('Tema_Semantico'):
        print(f"\n🏷️  CLUSTER: {cluster_nome} ({len(dati)} keywords)")
        for kw in dati['Keyword'].head(4): # Mostra solo un assaggio per gruppo
            print(f"   - {kw}")
        if len(dati) > 4:
            print("   - ...")

if __name__ == "__main__":
    # --- CONFIGURAZIONE SCRIPT ---
    # Sostituisci con il nome del file CSV da cui vuoi partire
    FILE_INPUT = "lista_keyword_guanti_da_lavoro.csv" 
    
    # Imposta il numero di "silos" semantici desiderati
    NUM_CLUSTER = 7
    # -----------------------------

    esegui_clustering(FILE_INPUT, NUM_CLUSTER)
