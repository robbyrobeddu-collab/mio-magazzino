import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- 1. CONFIGURAZIONE ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets, scope)
    client = gspread.authorize(creds)
    return client.open("Magazzino").sheet1

sheet = get_sheet()

# --- 2. LETTURA E PULIZIA DATI ---
try:
    all_data = sheet.get_all_values()
    if len(all_data) > 1:
        headers = [str(c).lower().strip() for c in all_data[0]]
        df = pd.DataFrame(all_data[1:], columns=headers)
        
        # Pulizia preventiva delle colonne testuali
        text_cols = ['codice', 'categoria', 'descrizione', 'posizione']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', '<NA>'], '')
        
        # Forza la colonna prezzo a numerico, trattando la virgola come punto
        df['prezzo'] = df['prezzo'].astype(str).str.replace(',', '.')
        df['prezzo'] = pd.to_numeric(df['prezzo'], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'])
except Exception as e:
    st.error(f"Errore lettura: {e}")

# --- 3. FILTRI DI RICERCA ---
st.subheader("📋 Inventario")

ricerca = st.text_input("🔍 Cerca per descrizione o codice...", placeholder="Scrivi qui per filtrare...")

col1, col2 = st.columns(2)

# Assicuriamoci che le colonne di testo siano stringhe standard
text_cols = ['codice', 'categoria', 'descrizione', 'posizione
